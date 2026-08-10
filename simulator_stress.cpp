#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <algorithm>
#include <cmath>
#include <chrono>
#include <cstdlib>
#include "sensor_packet.hpp"

constexpr const char* SERVER_IP = "127.0.0.1";
constexpr int         PORT      = 8080;

static uint64_t now_us() {
    return static_cast<uint64_t>(
        std::chrono::duration_cast<std::chrono::microseconds>(
            std::chrono::steady_clock::now().time_since_epoch()
        ).count()
    );
}

int main() {
    int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) return 1;

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port   = htons(PORT);
    inet_pton(AF_INET, SERVER_IP, &addr.sin_addr);

    // Phase durations (seconds)
    // 0-15s:  Warm up   — HR 80->120,  movement high
    // 15-35s: Active    — HR 120->150, movement medium
    // 35-55s: Tired     — HR 150->170, movement dropping
    // 55-70s: Exhausted — HR 170->185, movement very low => fatigue triggers
    // 70-80s: Recovery  — HR drops back down

    constexpr int TOTAL_S = 80;
    int tick = 0;

    while (true) {
        float t = tick * 0.01f;  // seconds (10ms per tick)
        float progress = std::min(t / TOTAL_S, 1.0f);

        float hr_base, movement_scale;

        if (t < 15.0f) {
            float p = t / 15.0f;
            hr_base       = 80.0f  + p * 40.0f;
            movement_scale = 1.8f;
        } else if (t < 35.0f) {
            float p = (t - 15.0f) / 20.0f;
            hr_base       = 120.0f + p * 30.0f;
            movement_scale = 1.8f  - p * 0.8f;
        } else if (t < 55.0f) {
            float p = (t - 35.0f) / 20.0f;
            hr_base       = 150.0f + p * 20.0f;
            movement_scale = 1.0f  - p * 0.7f;
        } else if (t < 70.0f) {
            float p = (t - 55.0f) / 15.0f;
            hr_base       = 170.0f + p * 15.0f;
            movement_scale = 0.3f  - p * 0.2f;
        } else {
            float p = (t - 70.0f) / 10.0f;
            hr_base       = 185.0f - p * 80.0f;
            movement_scale = 0.1f  + p * 0.8f;
        }

        // Add natural noise
        float noise_hr  = (static_cast<float>(rand() % 100) / 100.0f - 0.5f) * 8.0f;
        float noise_ax  = (static_cast<float>(rand() % 100) / 100.0f - 0.5f) * 0.3f;
        float noise_ay  = (static_cast<float>(rand() % 100) / 100.0f - 0.5f) * 0.3f;
        float noise_az  = (static_cast<float>(rand() % 100) / 100.0f - 0.5f) * 0.2f;

        SensorPacket pkt{};
        pkt.heart_rate   = static_cast<uint32_t>(std::max(50.0f, hr_base + noise_hr));
        pkt.accel_x      = std::sin(t * 2.1f) * movement_scale + noise_ax;
        pkt.accel_y      = std::cos(t * 1.7f) * movement_scale + noise_ay;
        pkt.accel_z      = std::sin(t * 3.3f) * (movement_scale * 0.5f) + noise_az;
        pkt.timestamp_us = now_us();

        sendto(sockfd, &pkt, sizeof(pkt), 0,
               reinterpret_cast<sockaddr*>(&addr), sizeof(addr));

        // Loop back after full cycle
        if (t >= TOTAL_S) tick = 0;
        else ++tick;

        usleep(10000);
    }

    close(sockfd);
    return 0;
}
