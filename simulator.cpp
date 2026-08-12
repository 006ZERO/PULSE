#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <random>
#include <chrono>
#include "sensor_packet.hpp"

constexpr const char* SERVER_IP = "127.0.0.1";
constexpr int PORT = 8080;

int main() {
    int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) return 1;

    sockaddr_in server_addr{};
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr);

    std::mt19937 rng(std::random_device{}());
    std::uniform_real_distribution<float>    accel_dist(-2.0f, 2.0f);
    std::uniform_int_distribution<uint32_t>  hr_dist(80, 180);

    while (true) {
        auto ts = std::chrono::duration_cast<std::chrono::microseconds>(
            std::chrono::steady_clock::now().time_since_epoch()
        ).count();

        SensorPacket pkt{
            accel_dist(rng),
            accel_dist(rng),
            accel_dist(rng),
            hr_dist(rng),
            97.5f,
            92.0f,
            static_cast<uint64_t>(ts)
        };

        sendto(sockfd, &pkt, sizeof(pkt), 0,
               reinterpret_cast<sockaddr*>(&server_addr), sizeof(server_addr));
        usleep(10000);
    }

    close(sockfd);
    return 0;
}
