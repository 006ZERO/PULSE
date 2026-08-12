#pragma once
#include <cstdint>

struct alignas(4) SensorPacket {
    float    accel_x, accel_y, accel_z;
    uint32_t heart_rate;
    float    spo2;
    float    signal_quality;
    uint64_t timestamp_us;
};

static_assert(sizeof(SensorPacket) == 32);
