#include "UwpSharedMath.h"

extern "C" int UwpSharedSub(int a, int b) {
    return a - b;
}

extern "C" int UwpSharedDiv2(int a) {
    return a / 2;
}
