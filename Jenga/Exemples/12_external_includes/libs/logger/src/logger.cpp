#include <iostream>
#include "logger.h"
void log_line(const char* msg) {
    std::cout << "[log] " << msg << "\n";
}
