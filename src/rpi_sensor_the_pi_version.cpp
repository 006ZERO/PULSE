#include "sensor_packet.hpp"
#include <algorithm>
#include <arpa/inet.h>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <fcntl.h>
#include <linux/i2c-dev.h>
#include <netinet/in.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <unistd.h>

constexpr const char* SERVER_IP = "127.0.0.1";
constexpr int PORT = 8080;
constexpr int LOOP_US = 10000; // MAX30100 configured for 100 samples/s
constexpr uint8_t ADXL345_ADDR = 0x53;
constexpr uint8_t MAX30100_ADDR = 0x57;

static uint64_t now_us() {
    return static_cast<uint64_t>(std::chrono::duration_cast<std::chrono::microseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count());
}

static int open_i2c(const char* bus, uint8_t address) {
    int fd = open(bus, O_RDWR);
    if (fd < 0 || ioctl(fd, I2C_SLAVE, address) < 0) {
        if (fd >= 0) close(fd);
        return -1;
    }
    return fd;
}

static bool write_reg(int fd, uint8_t reg, uint8_t value) {
    uint8_t bytes[2] = {reg, value};
    return write(fd, bytes, 2) == 2;
}

static bool read_regs(int fd, uint8_t reg, uint8_t* out, size_t length) {
    return write(fd, &reg, 1) == 1 && read(fd, out, length) == static_cast<ssize_t>(length);
}

static void init_adxl345(int fd) {
    write_reg(fd, 0x2D, 0x08); // measurement mode
    write_reg(fd, 0x31, 0x08); // full resolution, +/-2 g
}

static void init_max30100(int fd) {
    write_reg(fd, 0x06, 0x40); // reset
    usleep(10000);
    write_reg(fd, 0x02, 0x00); // reset FIFO write pointer
    write_reg(fd, 0x03, 0x00); // reset overflow counter
    write_reg(fd, 0x04, 0x00); // reset FIFO read pointer
    write_reg(fd, 0x07, 0x47); // high resolution, 100 Hz, 1600 us pulse
    write_reg(fd, 0x09, 0x8F); // red 27.1 mA, IR 50 mA
    write_reg(fd, 0x06, 0x03); // SpO2 mode
}

static bool read_accel(int fd, float& x, float& y, float& z) {
    uint8_t bytes[6]{};
    if (!read_regs(fd, 0x32, bytes, sizeof(bytes))) return false;
    auto value = [&](int i) { return static_cast<int16_t>((bytes[i + 1] << 8) | bytes[i]); };
    constexpr float scale = 1.0f / 256.0f;
    x = value(0) * scale;
    y = value(2) * scale;
    z = value(4) * scale;
    return true;
}

static bool read_ppg(int fd, uint16_t& ir, uint16_t& red) {
    uint8_t bytes[4]{};
    if (!read_regs(fd, 0x05, bytes, sizeof(bytes))) return false;
    ir = static_cast<uint16_t>((bytes[0] << 8) | bytes[1]);
    red = static_cast<uint16_t>((bytes[2] << 8) | bytes[3]);
    return true;
}

struct PpgResult { uint32_t bpm = 0; float spo2 = 0; float quality = 0; bool finger = false; };

class PpgProcessor {
    double ir_dc_ = 0, red_dc_ = 0, previous2_ = 0, previous1_ = 0;
    double envelope_ = 1, ir_sq_ = 0, red_sq_ = 0;
    uint64_t last_beat_ = 0, last_valid_ = 0;
    std::array<float, 5> bpms_{};
    size_t bpm_count_ = 0, bpm_cursor_ = 0, window_ = 0;
    float spo2_ = 0;

public:
    PpgResult update(uint16_t ir, uint16_t red, float movement, uint64_t timestamp) {
        PpgResult result;
        result.finger = ir > 5000 && red > 1000 && ir < 65000 && red < 65000;
        if (!result.finger) {
            ir_dc_ = red_dc_ = previous2_ = previous1_ = 0;
            envelope_ = 1; ir_sq_ = red_sq_ = 0; window_ = 0;
            bpm_count_ = bpm_cursor_ = 0; last_beat_ = last_valid_ = 0; spo2_ = 0;
            return result;
        }

        if (ir_dc_ == 0) { ir_dc_ = ir; red_dc_ = red; }
        ir_dc_ += 0.005 * (static_cast<double>(ir) - ir_dc_);
        red_dc_ += 0.005 * (static_cast<double>(red) - red_dc_);
        const double ir_ac = static_cast<double>(ir) - ir_dc_;
        const double red_ac = static_cast<double>(red) - red_dc_;
        envelope_ += 0.02 * (std::abs(ir_ac) - envelope_);
        ir_sq_ += ir_ac * ir_ac;
        red_sq_ += red_ac * red_ac;
        ++window_;

        // Local maximum, adaptive amplitude threshold, and a physiological refractory period.
        if (previous1_ > previous2_ && previous1_ >= ir_ac && previous1_ > std::max(35.0, envelope_ * 0.65)) {
            if (!last_beat_ || timestamp - last_beat_ >= 300000) {
                if (last_beat_) {
                    const float bpm = 60000000.0f / static_cast<float>(timestamp - last_beat_);
                    if (bpm >= 40 && bpm <= 210) {
                        bpms_[bpm_cursor_] = bpm;
                        bpm_cursor_ = (bpm_cursor_ + 1) % bpms_.size();
                        bpm_count_ = std::min(bpms_.size(), bpm_count_ + 1);
                        last_valid_ = timestamp;
                    }
                }
                last_beat_ = timestamp;
            }
        }
        previous2_ = previous1_;
        previous1_ = ir_ac;

        if (window_ >= 100) {
            const double ir_rms = std::sqrt(ir_sq_ / window_);
            const double red_rms = std::sqrt(red_sq_ / window_);
            if (ir_rms > 1 && ir_dc_ > 0 && red_dc_ > 0) {
                const double ratio = (red_rms / red_dc_) / (ir_rms / ir_dc_);
                spo2_ = std::clamp(static_cast<float>(110.0 - 25.0 * ratio), 70.0f, 100.0f);
            }
            ir_sq_ = red_sq_ = 0;
            window_ = 0;
        }

        if (bpm_count_ && timestamp - last_valid_ < 3000000) {
            float sum = 0;
            for (size_t i = 0; i < bpm_count_; ++i) sum += bpms_[i];
            result.bpm = static_cast<uint32_t>(std::lround(sum / bpm_count_));
        }
        result.spo2 = result.bpm ? spo2_ : 0;
        const float perfusion = static_cast<float>(envelope_ / std::max(ir_dc_, 1.0));
        const float optical = std::clamp(25.0f + perfusion * 6000.0f, 25.0f, 98.0f);
        const float motion_penalty = std::clamp(std::abs(movement - 1.0f) * 25.0f, 0.0f, 55.0f);
        result.quality = (result.bpm && result.spo2 > 0) ? std::clamp(optical - motion_penalty, 0.0f, 100.0f) : 0;
        return result;
    }
};

int main() {
    int accel_fd = open_i2c("/dev/i2c-1", ADXL345_ADDR);
    int ppg_fd = open_i2c("/dev/i2c-0", MAX30100_ADDR);
    if (accel_fd < 0 || ppg_fd < 0) {
        fprintf(stderr, "Sensor error: expected ADXL345 at /dev/i2c-1:0x53 and MAX30100 at /dev/i2c-0:0x57\n");
        return 1;
    }
    init_adxl345(accel_fd);
    init_max30100(ppg_fd);

    fprintf(stdout, "Calibrating accelerometer: keep the device flat and still for 2 seconds...\n");
    float offset_x = 0, offset_y = 0, offset_z = 0;
    int calibration_samples = 0;
    for (int i = 0; i < 200; ++i) {
        float x = 0, y = 0, z = 0;
        if (read_accel(accel_fd, x, y, z)) {
            offset_x += x; offset_y += y; offset_z += z;
            ++calibration_samples;
        }
        usleep(LOOP_US);
    }
    if (calibration_samples) {
        offset_x /= calibration_samples;
        offset_y /= calibration_samples;
        offset_z = offset_z / calibration_samples - 1.0f; // preserve gravity on Z
    }

    int socket_fd = socket(AF_INET, SOCK_DGRAM, 0);
    sockaddr_in destination{};
    destination.sin_family = AF_INET;
    destination.sin_port = htons(PORT);
    inet_pton(AF_INET, SERVER_IP, &destination.sin_addr);
    PpgProcessor ppg;
    fprintf(stdout, "Real sensor stream active on %s:%d\n", SERVER_IP, PORT);

    while (true) {
        SensorPacket packet{};
        uint16_t ir = 0, red = 0;
        const bool accel_ok = read_accel(accel_fd, packet.accel_x, packet.accel_y, packet.accel_z);
        if (accel_ok) {
            packet.accel_x -= offset_x;
            packet.accel_y -= offset_y;
            packet.accel_z -= offset_z;
        }
        const bool ppg_ok = read_ppg(ppg_fd, ir, red);
        packet.timestamp_us = now_us();
        const float movement = std::sqrt(packet.accel_x * packet.accel_x + packet.accel_y * packet.accel_y + packet.accel_z * packet.accel_z);
        const PpgResult result = ppg_ok ? ppg.update(ir, red, movement, packet.timestamp_us) : PpgResult{};
        packet.heart_rate = result.bpm;
        packet.spo2 = result.spo2;
        packet.signal_quality = (accel_ok && ppg_ok) ? result.quality : 0;
        sendto(socket_fd, &packet, sizeof(packet), 0, reinterpret_cast<sockaddr*>(&destination), sizeof(destination));
        if (!result.finger) fprintf(stderr, "Waiting for valid finger contact\r");
        usleep(LOOP_US);
    }
}
