#pragma once

// =============================================================================
// NkXLib.h
// Point d'entrée Linux Xlib.
// =============================================================================

#include "../Core/NkEntry.h"
#include "../Platform/XLib/NkXLibWindowImpl.h"
#include <X11/Xlib.h>
#include <vector>
#include <string>

#ifndef NK_APP_NAME
#define NK_APP_NAME "xlib_app"
#endif

namespace nkentseu { NkEntryState* gState = nullptr; }

int main(int argc, char* argv[])
{
    XInitThreads();

    Display* display = XOpenDisplay(nullptr);
    if (!display) return 1;

    nk_xlib_global_display = display;

    std::vector<std::string> args(argv, argv + argc);

    nkentseu::NkEntryState state(display, args);
    state.appName = NK_APP_NAME;
    nkentseu::gState = &state;

    int result = nkmain(state);

    nkentseu::gState        = nullptr;
    nk_xlib_global_display  = nullptr;

    XCloseDisplay(display);
    return result;
}
