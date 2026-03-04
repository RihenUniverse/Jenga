#define SDL_MAIN_USE_CALLBACKS 1

#include "application.h"

#include <SDL3/SDL.h>
#include <SDL3/SDL_main.h>

#include <cstddef>
#include <string>
#include <vector>

namespace {

struct AppState {
    Application* app = nullptr;
};

void LogAppError(const NkErrorHandler& error) {
    SDL_LogError(
        SDL_LOG_CATEGORY_APPLICATION,
        "Application failed (code=%d): %s",
        NkErrorToExitCode(error),
        error.Message().c_str()
    );
}

std::vector<std::string> BuildArgs(int argc, char** argv) {
    std::vector<std::string> args;
    args.reserve(argc > 0 ? static_cast<std::size_t>(argc - 1) : 0u);
    for (int i = 1; i < argc; ++i) {
        args.emplace_back(argv[i] ? argv[i] : "");
    }
    return args;
}

}  // namespace

SDL_AppResult SDL_AppInit(void** appstate, int argc, char* argv[]) {
    auto* state = new AppState();
    state->app = new Application(BuildArgs(argc, argv));
    *appstate = state;

    const NkErrorHandler result = state->app->Start();
    if (!result.Ok()) {
        LogAppError(result);
        return SDL_APP_FAILURE;
    }
    return SDL_APP_CONTINUE;
}

SDL_AppResult SDL_AppEvent(void* appstate, SDL_Event* event) {
    auto* state = static_cast<AppState*>(appstate);
    if (state == nullptr || state->app == nullptr || event == nullptr) {
        return SDL_APP_FAILURE;
    }

    const NkErrorHandler result = state->app->HandleEvent(*event);
    if (!result.Ok()) {
        LogAppError(result);
        return SDL_APP_FAILURE;
    }
    return state->app->IsRunning() ? SDL_APP_CONTINUE : SDL_APP_SUCCESS;
}

SDL_AppResult SDL_AppIterate(void* appstate) {
    auto* state = static_cast<AppState*>(appstate);
    if (state == nullptr || state->app == nullptr) {
        return SDL_APP_FAILURE;
    }

    const NkErrorHandler result = state->app->IterateFrame();
    if (!result.Ok()) {
        LogAppError(result);
        return SDL_APP_FAILURE;
    }
    return state->app->IsRunning() ? SDL_APP_CONTINUE : SDL_APP_SUCCESS;
}

void SDL_AppQuit(void* appstate, SDL_AppResult) {
    auto* state = static_cast<AppState*>(appstate);
    if (state == nullptr) {
        return;
    }
    if (state->app != nullptr) {
        state->app->Close();
        delete state->app;
        state->app = nullptr;
    }
    delete state;
}
