#ifdef __ANDROID__
#include <android/log.h>
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "HelloJenga", __VA_ARGS__)
#else
#include <iostream>
#define LOGI(...) std::cout << __VA_ARGS__ << std::endl
#endif

int main() {
    LOGI("Hello from Jenga!");
    return 0;
}