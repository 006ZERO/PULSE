#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <fstream>
#include <csignal>
#include "sensor_packet.hpp"

constexpr const char* SHM_NAME    = "/sport_tech_shm";
constexpr int         FLUSH_EVERY = 10;

static volatile bool running = true;
static void on_signal(int) { running = false; }

int main() {
    std::signal(SIGINT,  on_signal);
    std::signal(SIGTERM, on_signal);

    int shm_fd = shm_open(SHM_NAME, O_RDONLY, 0666);
    if (shm_fd < 0) return 1;

    auto* shm_ptr = static_cast<const SensorPacket*>(
        mmap(nullptr, sizeof(SensorPacket), PROT_READ, MAP_SHARED, shm_fd, 0)
    );
    if (shm_ptr == MAP_FAILED) return 1;

    std::ofstream file("training_session.csv");
    file << "timestamp_us,accel_x,accel_y,accel_z,heart_rate,spo2,signal_quality\n";
    file.flush();

    int count = 0;
    while (running) {
        file << shm_ptr->timestamp_us << ","
             << shm_ptr->accel_x     << ","
             << shm_ptr->accel_y     << ","
             << shm_ptr->accel_z     << ","
             << shm_ptr->heart_rate  << ","
             << shm_ptr->spo2        << ","
             << shm_ptr->signal_quality << "\n";
        if (++count % FLUSH_EVERY == 0) file.flush();
        usleep(500000);
    }
    file.flush();
    return 0;
}
