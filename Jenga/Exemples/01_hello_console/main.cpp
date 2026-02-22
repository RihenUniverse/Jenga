#ifdef __ANDROID__
    #include <android/log.h>
    // Android NativeActivity entry point (must be extern "C")
    extern "C" void android_main(void*) {
        __android_log_print(ANDROID_LOG_INFO, "HelloJenga", "Hello from Jenga on Android!");
    }
#else
    #include <iostream>
    int main() {
        std::cout << "Hello from Jenga!" << std::endl;
        return 0;
    }
#endif