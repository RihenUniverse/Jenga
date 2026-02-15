#include "logger.h"
#include "mathlib.h"
int main() {
    log_line("external include demo");
    return mul(6, 7) == 42 ? 0 : 1;
}
