# PULSE

Real-time athlete workload and fatigue monitoring on Raspberry Pi.

> 🏆 First-place project — Sport-Tech Hackathon 2026

PULSE reads optical pulse and motion data from a wearable sensor node, processes the measurements locally, estimates fatigue risk with a trained model, and streams the result to a live coaching dashboard. Sessions can be reviewed by athlete and exported as PDF reports.

> **Prototype notice:** PULSE is a sports-performance prototype, not a medical device. Heart-rate, SpO₂, and fatigue outputs must not be used for diagnosis or emergency decisions.

## What it does

- Reads a MAX30100 optical sensor and ADXL345 accelerometer over separate I²C buses.
- Calculates heart rate from measured red/IR pulse peaks instead of generated values.
- Estimates SpO₂ from the measured red/IR ratio.
- Rejects missing contact, saturated readings, stale timestamps, and excessive motion.
- Calibrates the accelerometer for two seconds at hardware startup.
- Runs fatigue inference locally with Python and a Random Forest model.
- Streams telemetry to a browser dashboard through WebSockets.
- Records multiple athletes and sessions, including fatigue events.
- Provides presentation mode, session history, athlete summaries, and PDF export.
- Includes a stress simulator for development without a Raspberry Pi.

## Architecture

```text
MAX30100 (I²C bus 0, 0x57) ─┐
                             ├─> C++ sensor process ─UDP:8080─> C++ shared-memory receiver
ADXL345 (I²C bus 1, 0x53) ──┘                                      │
                                                                     ▼
                                                          Python inference process
                                                                     │ WebSocket
                                                                     ▼
                                                          Node.js dashboard :3000
```

The simulator replaces only the physical sensor process. The receiver, model, server, and dashboard remain the same.

## Hardware assumptions

The default hardware program expects:

| Sensor | Address | Linux device |
|---|---:|---|
| MAX30100 pulse/SpO₂ sensor | `0x57` | `/dev/i2c-0` |
| ADXL345 accelerometer | `0x53` | `/dev/i2c-1` |

Enable both I²C buses before setup. If your board exposes the sensors on different buses, update the device paths in `src/rpi_sensor_the_pi_version.cpp` before compiling.

## Quick start on Raspberry Pi

### 1. Install system packages

Raspberry Pi OS / Debian / Ubuntu:

```bash
sudo apt update
sudo apt install -y git build-essential python3 python3-dev python3-venv nodejs npm i2c-tools
```

Fedora:

```bash
sudo dnf install -y git gcc-c++ python3 python3-devel nodejs npm i2c-tools
```

The Python development headers are required to build `posix-ipc`. A missing `Python.h` error means `python3-dev` or `python3-devel` is not installed.

### 2. Clone and prepare PULSE

```bash
git clone https://github.com/006ZERO/PULSE.git
cd PULSE
chmod +x setup.sh start.sh
./setup.sh
```

`setup.sh` installs Node and Python dependencies, compiles the native processes, and runs offline readiness checks.

### 3. Confirm the sensors

```bash
ls /dev/i2c-*
sudo i2cdetect -y 0
sudo i2cdetect -y 1
```

Expected results:

- Bus `0` contains `57` for the MAX30100.
- Bus `1` contains `53` for the ADXL345.

Do not continue with hardware mode if either address is missing. Check power, ground, SDA/SCL wiring, I²C enablement, and the selected bus.

### 4. Start real hardware mode

Place the wearable flat and keep it completely still while the program performs its two-second accelerometer calibration. Then run:

```bash
./start.sh
```

Hardware is the default source. The explicit equivalent is:

```bash
PULSE_SOURCE=hardware ./start.sh
```

Keep this terminal open. Stop the full stack cleanly with `Ctrl+C`.

### 5. Open the dashboard

On the Pi:

```text
http://localhost:3000
```

From a phone or laptop on the same network, find the Pi address:

```bash
hostname -I
```

Then open:

```text
http://PI_IP_ADDRESS:3000
```

If Fedora blocks remote access, allow the dashboard port:

```bash
sudo firewall-cmd --add-port=3000/tcp
```

Use `--permanent` only if you want that firewall rule to remain after reboot.

### 6. Verify the running system

In a second terminal:

```bash
cd PULSE
npm run workshop:check
```

A working hardware session should report:

```text
PASS  Dashboard server                 HTTP 200
PASS  Sensor telemetry                 packets arriving
```

## Simulator mode

Use the simulator when the Pi or sensors are unavailable:

```bash
PULSE_SOURCE=simulator ./start.sh
```

Open `http://localhost:3000` and start a session. The stress cycle moves through warm-up, active, tired, exhausted, and recovery phases.

Do not run `simulator_stress` and `src/rpi_sensor` together. Both publish the same packet format to UDP port `8080`. `start.sh` stops older PULSE processes before selecting one source.

## Starting and stopping

| Goal | Command |
|---|---|
| One-time setup | `./setup.sh` |
| Real Pi sensors | `./start.sh` |
| Explicit hardware mode | `PULSE_SOURCE=hardware ./start.sh` |
| Simulator mode | `PULSE_SOURCE=simulator ./start.sh` |
| Readiness check | `npm run workshop:check` |
| Stop all processes started by the script | `Ctrl+C` in the `start.sh` terminal |

`npm start` launches only the Node.js web server. It does **not** start the C++ receiver, sensor/simulator source, or Python inference process. Use `start.sh` for the complete system.

## Reading the dashboard

- **Sensor stream live** means telemetry reached the web server within the last three seconds.
- **Signal quality** combines optical contact, valid pulse range, timestamp continuity, and motion-artifact checks.
- **Poor signal / —** means PULSE intentionally rejected an unreliable cardiovascular measurement.
- **Fatigue index** is model output, not a clinical measurement.
- **Athlete overview** groups every saved session by athlete.
- **Session history** shows completed and active sessions stored on that device.

Keep the finger steady on the optical sensor and shield it from strong ambient light. Optical readings during vigorous movement can be unreliable even when the software is operating correctly.

## Troubleshooting

### `Python.h: No such file or directory`

Install Python development headers, remove the incomplete virtual environment if needed, and rerun setup:

```bash
# Fedora
sudo dnf install -y python3-devel

# Debian / Raspberry Pi OS
sudo apt install -y python3-dev

rm -rf .venv
./setup.sh
```

### Dashboard server unavailable

Run the complete stack in one terminal:

```bash
./start.sh
```

Then run the check from a second terminal. Do not open `dashboard.html` directly with a `file://` URL; use `http://localhost:3000`.

### Sensor telemetry unavailable

Check the selected source and running processes:

```bash
pgrep -af "backend|rpi_sensor|simulator_stress|processor.py|server.js"
```

For hardware mode, repeat the I²C scans and confirm `53` and `57` are present. For simulator mode, confirm the command was started with `PULSE_SOURCE=simulator`.

### Sensor detected but values stay blank

- Hold the finger steadily against the MAX30100.
- Reduce ambient light reaching the optical sensor.
- Avoid moving the sensor while a pulse lock is established.
- Wait for several valid beats; PULSE does not invent an initial BPM.
- Check that signal quality rises above the rejection threshold.

### Port already in use

`start.sh` normally removes stale PULSE processes. To inspect the ports manually:

```bash
sudo ss -lntup | grep -E ':3000|:8080'
```

Stop the process occupying the port, then rerun `./start.sh`.

## Project structure

```text
.
├── dashboard.html                       # Live dashboard and PDF report UI
├── backend.cpp                          # UDP receiver and shared-memory writer
├── backends/
│   ├── processor.py                     # Signal validation and fatigue inference
│   └── server.js                        # HTTP, session storage, and WebSockets
├── src/
│   ├── rpi_sensor_the_pi_version.cpp    # Real MAX30100 + ADXL345 acquisition
│   └── sensor_packet.hpp                # Shared 32-byte telemetry contract
├── simulator_stress.cpp                 # Full fatigue-cycle simulator
├── data_logger.cpp                      # CSV telemetry logger
├── fatigue_model.pkl                    # Trained Random Forest model
├── fatigue_scaler.pkl                   # Model feature scaler
├── setup.sh                             # Dependencies and native compilation
├── start.sh                             # Complete process orchestration
└── tools/workshop-check.js              # Offline and live readiness checks
```

## Data flow and packet compatibility

Every native producer and consumer must use the same `SensorPacket` definition. After changing `src/sensor_packet.hpp`, always rerun:

```bash
./setup.sh
```

The current packet is 32 bytes and contains acceleration, measured heart rate, measured SpO₂, signal quality, and a monotonic timestamp.

## Validating measurement quality

Before a public demonstration:

1. Compare heart rate with a chest strap at rest, during activity, and during recovery.
2. Compare SpO₂ with a fingertip pulse oximeter while stationary.
3. Record the error and signal quality under each condition.
4. Run the complete system continuously for at least 20–30 minutes.
5. Confirm poor contact produces a blank reading rather than a plausible false value.

The MAX30100 is sensitive to placement and motion. Accurate sports use requires physical validation on the final enclosure and athlete attachment—not only successful software execution.

## License

No license file is currently included. Add one before distributing or reusing the project outside its intended workshop context.
