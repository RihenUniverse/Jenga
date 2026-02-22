#include <android/log.h>

#if __has_include(<SDL3/SDL.h>)
    #include <SDL3/SDL.h>
    #define JENGA_HAS_SDL3 1
#else
    #define JENGA_HAS_SDL3 0
#endif

extern "C" void android_main(void*) {
#if JENGA_HAS_SDL3
    SDL_SetMainReady();
    __android_log_print(ANDROID_LOG_INFO, "Jenga", "SDL3 Android.mk sample: SDL3 detected");
#else
    __android_log_print(
        ANDROID_LOG_WARN,
        "Jenga",
        "SDL3 header not found. Set SDL3_ROOT and use --android-build-system ndk-mk"
    );
#endif
}
