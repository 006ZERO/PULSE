#pragma once
#include <cstdint>

struct alignas(4) SensorPacket {
    float    accel_x, accel_y, accel_z;
    uint32_t heart_rate;
    uint64_t timestamp_us;
};

static_assert(sizeof(SensorPacket) == 24);
