#include <android/log.h>

// IMPORTANT: android_main doit être extern "C" car appelée depuis du code C
extern "C" void android_main(void*) {
    __android_log_print(ANDROID_LOG_INFO, "Jenga", "NativeActivity started");
}
