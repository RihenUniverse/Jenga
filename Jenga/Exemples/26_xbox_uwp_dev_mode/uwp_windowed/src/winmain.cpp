#include <windows.h>
#include "UwpStaticMath.h"
#include "UwpSharedMath.h"

int WINAPI WinMain(HINSTANCE, HINSTANCE, LPSTR, int) {
    const int value = UwpStaticAdd(10, 20) + UwpSharedSub(12, 4);
    return (value > 0) ? 0 : 1;
}
