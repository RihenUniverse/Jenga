#include <chrono>
#include <cstdint>
#include <iostream>

static std::uint64_t work(std::uint64_t n) {
    std::uint64_t sum = 0;
    for (std::uint64_t i = 0; i < n; ++i) {
        sum += (i * 2654435761u) ^ (sum >> 1);
    }
    return sum;
}

int main() {
    auto t0 = std::chrono::high_resolution_clock::now();
    volatile auto v = work(5000000);
    auto t1 = std::chrono::high_resolution_clock::now();
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(t1 - t0).count();
    std::cout << "result=" << v << " time_ms=" << ms << "\n";
    return 0;
}
