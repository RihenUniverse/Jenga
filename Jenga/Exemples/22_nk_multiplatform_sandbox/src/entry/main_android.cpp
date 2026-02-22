#if defined(__ANDROID__)
#include "nk.hpp"

extern "C" void android_main(void*) {
    char arg0[] = "nk_android";
    char* argv[] = {arg0, nullptr};
    nk::nk_main(1, argv);
}
#endif
