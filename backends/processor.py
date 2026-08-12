import mmap
import struct
import json
import asyncio
import websockets
import posix_ipc
import joblib
import numpy as np
from collections import deque

PACKET_FORMAT = '=fffIffQ'
PACKET_SIZE   = struct.calcsize(PACKET_FORMAT)

model  = joblib.load('fatigue_model.pkl')
scaler = joblib.load('fatigue_scaler.pkl')

HR_WIN  = 20
MAG_WIN = 30

def compute_hrv(h):
    if len(h) < 2: return 0.0
    return float(np.mean(np.abs(np.diff(list(h)))))

def mov_trend(m):
    if len(m) < MAG_WIN: return 1.0
    half = MAG_WIN // 2
    a, b = list(m)[:half], list(m)[half:]
    return float(np.mean(b) / max(np.mean(a), 0.001))

def estimate_resp_rate(mag_history):
    if len(mag_history) < 20: return 18.0
    recent = list(mag_history)[-20:]
    mean   = np.mean(recent)
    crossings = sum(1 for i in range(1, len(recent))
                    if (recent[i] - mean) * (recent[i-1] - mean) < 0)
    return float(np.clip((crossings / 2) * 6, 8, 50))

async def process_and_send():
    shm      = posix_ipc.SharedMemory("/sport_tech_shm")
    map_file = mmap.mmap(shm.fd, shm.size)

    hr_win   = deque(maxlen=HR_WIN)
    mag_win  = deque(maxlen=MAG_WIN)
    prob_win = deque(maxlen=5)
    previous_hr = None
    previous_timestamp = None
    
    async with websockets.connect("ws://localhost:3000", ping_interval=None) as websocket:
        while True:
            map_file.seek(0)
            raw = map_file.read(PACKET_SIZE)
            ax, ay, az, heart_rate, measured_spo2, sensor_quality, timestamp_us = struct.unpack(PACKET_FORMAT, raw)

            mag  = float(np.sqrt(ax**2 + ay**2 + az**2))
            spo2 = float(measured_spo2) if measured_spo2 > 0 else 0.0
            rr   = estimate_resp_rate(mag_win)

            pulse_ok = 35 <= heart_rate <= 230 and spo2 > 0 and sensor_quality >= 25
            motion_ok = bool(np.all(np.isfinite([ax, ay, az]))) and mag <= 16.0
            timestamp_ok = previous_timestamp is None or timestamp_us > previous_timestamp
            motion_artifact = mag > 4.0
            hr_jump = pulse_ok and previous_hr is not None and abs(heart_rate - previous_hr) > 35
            quality = int(np.clip(sensor_quality, 0, 100))
            if not pulse_ok: quality -= 70
            if not motion_ok: quality -= 70
            if not timestamp_ok: quality -= 40
            if motion_artifact: quality -= 25
            if hr_jump: quality -= 20
            quality = int(np.clip(quality, 0, 100))

            if pulse_ok:
                hr_win.append(heart_rate)
            mag_win.append(mag)

            hrv   = compute_hrv(hr_win)
            trend = mov_trend(mag_win)

            model_hr = heart_rate if pulse_ok else (previous_hr or 60)
            model_spo2 = spo2 if spo2 > 0 else 95.0
            features      = np.array([[model_hr, mag, ax, ay, az, hrv, trend, model_spo2, rr]])
            prob = model.predict_proba(scaler.transform(features))[0][1] if pulse_ok else 0.0
            if pulse_ok: prob_win.append(prob)
            smoothed_prob = float(np.mean(prob_win)) if pulse_ok and prob_win else 0.0

            payload = json.dumps({
                "accel_x":         round(ax, 2),
                "accel_y":         round(ay, 2),
                "accel_z":         round(az, 2),
                "heart_rate":      heart_rate,
                "timestamp_us":    timestamp_us,
                "fatigue_warning": smoothed_prob >= 0.55,
                "fatigue_score":   int(smoothed_prob * 100),
                "hrv":             round(hrv, 2),
                "movement_trend":  round(trend, 2),
                "spo2":            round(spo2, 1),
                "resp_rate":       round(rr, 1),
                "signal_quality":  quality,
                "sensor_health": {
                    "pulse": "ok" if pulse_ok else "fault",
                    "motion": "ok" if motion_ok else "fault",
                    "timestamp": "ok" if timestamp_ok else "stale",
                    "motion_artifact": motion_artifact,
                },
            })

            await websocket.send(payload)
            if pulse_ok: previous_hr = heart_rate
            previous_timestamp = timestamp_us
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(process_and_send())
