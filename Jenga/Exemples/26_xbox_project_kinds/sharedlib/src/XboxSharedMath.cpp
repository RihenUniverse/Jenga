#include "XboxSharedMath.h"

extern "C" int XboxSharedSub(int a, int b) {
    return a - b;
}

extern "C" int XboxSharedDiv2(int a) {
    return a / 2;
}
