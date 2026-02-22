#if defined(__EMSCRIPTEN__)
#include "nk.hpp"

int main(int argc, char** argv) {
    return nk::nk_main(argc, argv);
}
#endif
