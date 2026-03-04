/**
 * Jenga Example 24 — All Platforms Build
 *
 * A single source file that compiles on every platform supported by Jenga:
 * Windows, Linux (cross-compile), Android (NDK), Web (Emscripten).
 */

#if defined(__ANDROID__)

#include <android/log.h>
#include <android_native_app_glue.h>

void android_main(struct android_app* app) {
    __android_log_print(ANDROID_LOG_INFO, "Jenga", "Hello from Jenga — Android!");

    while (true) {
        int events;
        struct android_poll_source* source;
        while (ALooper_pollOnce(0, nullptr, &events, (void**)&source) >= 0) {
            if (source) source->process(app, source);
            if (app->destroyRequested) return;
        }
    }
}

#elif defined(__EMSCRIPTEN__)

#include <emscripten.h>
#include <cstdio>

int main() {
    std::printf("Hello from Jenga — Web/Emscripten!\n");
    return 0;
}

#else // Windows, Linux, macOS

#include <cstdio>

int main() {
#if defined(_WIN32)
    std::printf("Hello from Jenga — Windows!\n");
#elif defined(__linux__)
    std::printf("Hello from Jenga — Linux!\n");
#elif defined(__APPLE__)
    std::printf("Hello from Jenga — macOS!\n");
#else
    std::printf("Hello from Jenga — Unknown platform!\n");
#endif
    return 0;
}

#endif
