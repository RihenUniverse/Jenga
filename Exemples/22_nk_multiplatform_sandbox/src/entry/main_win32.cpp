#if defined(_WIN32)
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include "nk.hpp"

extern "C" int WINAPI WinMain(HINSTANCE, HINSTANCE, LPSTR, int) {
    return nk::nk_main(0, nullptr);
}
#endif
