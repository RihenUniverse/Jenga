#pragma once

// =============================================================================
// NkWindowEvents.h
// Données et classes d'événements relatifs à la fenêtre.
//
// Structs de données (NkWindowXxxData) :
//   Portées dans NkEventData (union) — taille fixe, pas d'allocations.
//
// Classes d'événements typés (NkWindowXxxEvent) :
//   Sous-types de NkEvent permettant l'accès typé via As<T>().
// =============================================================================

#include "NkEventTypes.h"

namespace nkentseu
{

// ===========================================================================
// Structs de données
// ===========================================================================

// ---------------------------------------------------------------------------
// NkWindowCreateData
// ---------------------------------------------------------------------------
struct NkWindowCreateData
{
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_CREATE;
    NkU32 width  = 0;
    NkU32 height = 0;

    NkWindowCreateData() = default;
    NkWindowCreateData(NkU32 w, NkU32 h) : width(w), height(h) {}

    std::string ToString() const
    { return "WindowCreate(" + std::to_string(width) + "x" + std::to_string(height) + ")"; }
};

// ---------------------------------------------------------------------------
// NkWindowCloseData
// ---------------------------------------------------------------------------
struct NkWindowCloseData
{
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_CLOSE;
    bool forced = false; ///< true = demande du système (pas de l'utilisateur)

    NkWindowCloseData() = default;
    explicit NkWindowCloseData(bool forced) : forced(forced) {}

    std::string ToString() const
    { return forced ? "WindowClose(forced)" : "WindowClose(user)"; }
};

// ---------------------------------------------------------------------------
// NkWindowResizeData
// ---------------------------------------------------------------------------
struct NkWindowResizeData
{
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_RESIZE;
    NkU32 width      = 0;
    NkU32 height     = 0;
    NkU32 prevWidth  = 0;
    NkU32 prevHeight = 0;

    NkWindowResizeData() = default;
    NkWindowResizeData(NkU32 w, NkU32 h, NkU32 pw = 0, NkU32 ph = 0)
        : width(w), height(h), prevWidth(pw), prevHeight(ph) {}

    bool GotSmaller() const { return width < prevWidth || height < prevHeight; }

    std::string ToString() const
    {
        return "WindowResize(" + std::to_string(prevWidth) + "x" + std::to_string(prevHeight)
             + " -> " + std::to_string(width) + "x" + std::to_string(height) + ")";
    }
};

// NkWindowResizeBeginData et NkWindowResizeEndData — mêmes champs
using NkWindowResizeBeginData = NkWindowResizeData;
using NkWindowResizeEndData   = NkWindowResizeData;

// ---------------------------------------------------------------------------
// NkWindowMoveData
// ---------------------------------------------------------------------------
struct NkWindowMoveData
{
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_MOVE;
    NkI32 x     = 0, y     = 0; ///< Position courante (coin supérieur gauche écran)
    NkI32 prevX = 0, prevY = 0; ///< Position précédente

    NkWindowMoveData() = default;
    NkWindowMoveData(NkI32 x, NkI32 y, NkI32 px = 0, NkI32 py = 0)
        : x(x), y(y), prevX(px), prevY(py) {}

    std::string ToString() const
    {
        return "WindowMove(" + std::to_string(prevX) + "," + std::to_string(prevY)
             + " -> " + std::to_string(x) + "," + std::to_string(y) + ")";
    }
};

// ---------------------------------------------------------------------------
// NkWindowFocusData
// ---------------------------------------------------------------------------
struct NkWindowFocusData
{
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_FOCUS_GAINED;
    bool focused = false;

    NkWindowFocusData() = default;
    explicit NkWindowFocusData(bool f) : focused(f) {}

    std::string ToString() const
    { return focused ? "WindowFocusGained" : "WindowFocusLost"; }
};

// ---------------------------------------------------------------------------
// NkWindowDpiData
// ---------------------------------------------------------------------------
struct NkWindowDpiData
{
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_DPI_CHANGE;
    float scale     = 1.f;  ///< Nouveau facteur DPI (1.0 = 96 DPI, 2.0 = 192 DPI…)
    float prevScale = 1.f;  ///< Facteur précédent
    NkU32 dpi       = 96;   ///< DPI absolu (e.g. 96, 120, 144, 192)

    NkWindowDpiData() = default;
    NkWindowDpiData(float scale, float prev, NkU32 dpi)
        : scale(scale), prevScale(prev), dpi(dpi) {}

    std::string ToString() const
    {
        return "WindowDpi(" + std::to_string(prevScale)
             + " -> " + std::to_string(scale)
             + ", " + std::to_string(dpi) + "dpi)";
    }
};

// ---------------------------------------------------------------------------
// NkWindowThemeData
// ---------------------------------------------------------------------------
struct NkWindowThemeData
{
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_THEME_CHANGE;
    NkWindowTheme theme = NkWindowTheme::NK_THEME_UNKNOWN;

    NkWindowThemeData() = default;
    explicit NkWindowThemeData(NkWindowTheme t) : theme(t) {}

    std::string ToString() const
    {
        switch (theme)
        {
        case NkWindowTheme::NK_THEME_LIGHT:         return "WindowTheme(LIGHT)";
        case NkWindowTheme::NK_THEME_DARK:          return "WindowTheme(DARK)";
        case NkWindowTheme::NK_THEME_HIGH_CONTRAST: return "WindowTheme(HIGH_CONTRAST)";
        default:                                     return "WindowTheme(UNKNOWN)";
        }
    }
};

// ---------------------------------------------------------------------------
// NkWindowStateData — minimize / maximize / restore / fullscreen / windowed
// ---------------------------------------------------------------------------
struct NkWindowStateData
{
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_MINIMIZE;

    enum class State : NkU32 {
        Minimized, Maximized, Restored, Fullscreen, Windowed
    } state = State::Restored;

    std::string ToString() const
    {
        switch (state)
        {
        case State::Minimized:  return "WindowState(MINIMIZED)";
        case State::Maximized:  return "WindowState(MAXIMIZED)";
        case State::Restored:   return "WindowState(RESTORED)";
        case State::Fullscreen: return "WindowState(FULLSCREEN)";
        case State::Windowed:   return "WindowState(WINDOWED)";
        default:                return "WindowState(UNKNOWN)";
        }
    }
};

// ---------------------------------------------------------------------------
// NkWindowVisibilityData
// ---------------------------------------------------------------------------
struct NkWindowVisibilityData
{
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_SHOWN;
    bool visible = false;

    NkWindowVisibilityData() = default;
    explicit NkWindowVisibilityData(bool v) : visible(v) {}

    std::string ToString() const
    { return visible ? "WindowShown" : "WindowHidden"; }
};

// ---------------------------------------------------------------------------
// NkWindowDestroyData
// ---------------------------------------------------------------------------
struct NkWindowDestroyData
{
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_DESTROY;
    std::string ToString() const { return "WindowDestroy"; }
};

// ---------------------------------------------------------------------------
// NkWindowPaintData
// ---------------------------------------------------------------------------
struct NkWindowPaintData
{
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_PAINT;
    NkI32 dirtyX = 0, dirtyY = 0;
    NkU32 dirtyW = 0, dirtyH = 0; ///< Zone à redessiner (0 = tout)

    NkWindowPaintData() = default;
    NkWindowPaintData(NkI32 x, NkI32 y, NkU32 w, NkU32 h)
        : dirtyX(x), dirtyY(y), dirtyW(w), dirtyH(h) {}

    bool IsFullPaint() const { return dirtyW == 0 || dirtyH == 0; }

    std::string ToString() const
    {
        if (IsFullPaint()) return "WindowPaint(FULL)";
        return "WindowPaint(" + std::to_string(dirtyX) + "," + std::to_string(dirtyY)
             + " " + std::to_string(dirtyW) + "x" + std::to_string(dirtyH) + ")";
    }
};

} // namespace nkentseu
