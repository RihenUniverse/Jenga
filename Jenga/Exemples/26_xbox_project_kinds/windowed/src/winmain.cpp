#include <windows.h>
#include "XboxStaticMath.h"
#include "XboxSharedMath.h"

int WINAPI WinMain(HINSTANCE, HINSTANCE, LPSTR, int) {
    const int value = XboxStaticAdd(10, 20) + XboxSharedSub(12, 4);

    char buffer[128] = {0};
    wsprintfA(buffer, "XboxWindowedApp value=%d", value);
    MessageBoxA(nullptr, buffer, "Jenga Xbox", MB_OK | MB_ICONINFORMATION);
    return 0;
}
