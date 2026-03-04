#if defined(__APPLE__)
#include <TargetConditionals.h>
#if TARGET_OS_MAC && !TARGET_OS_IPHONE
#include "nk.hpp"

int main(int argc, char** argv) {
    return nk::nk_main(argc, argv);
}
#endif
#endif
