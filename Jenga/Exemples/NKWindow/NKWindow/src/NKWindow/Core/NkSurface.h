#pragma once

// =============================================================================
// NkSurface.h
// Descripteur de surface graphique natif par plateforme.
//
// NkSurfaceDesc contient tous les handles natifs nécessaires à un backend
// graphique (Vulkan, Metal, DirectX, OpenGL, Software) pour créer ses
// propres ressources de rendu.
// =============================================================================

#include "NkTypes.h"
#include "NkPlatformDetect.h"

// Inclusions conditionnelles des headers natifs
#if defined(NKENTSEU_FAMILY_WINDOWS)
#   ifndef WIN32_LEAN_AND_MEAN
#       define WIN32_LEAN_AND_MEAN
#   endif
#   include <Windows.h>

#elif defined(NKENTSEU_PLATFORM_COCOA)
#   ifdef __OBJC__
@class NSView;
@class CAMetalLayer;
#   else
    using NSView       = struct objc_object;
    using CAMetalLayer = struct objc_object;
#   endif

#elif defined(NKENTSEU_PLATFORM_UIKIT)
#   ifdef __OBJC__
@class UIView;
@class CAMetalLayer;
#   else
    using UIView       = struct objc_object;
    using CAMetalLayer = struct objc_object;
#   endif

#elif defined(NKENTSEU_PLATFORM_XCB)
#   include <xcb/xcb.h>

#elif defined(NKENTSEU_PLATFORM_XLIB)
#   include <X11/Xlib.h>

#elif defined(NKENTSEU_PLATFORM_ANDROID)
#   include <android/native_window.h>
#endif

namespace nkentseu
{

// ---------------------------------------------------------------------------
// NkSurfaceDesc - handles natifs de la surface de rendu
// ---------------------------------------------------------------------------

struct NkSurfaceDesc
{
    NkU32  width  = 0;   ///< Largeur en pixels physiques
    NkU32  height = 0;   ///< Hauteur en pixels physiques
    float  dpi    = 1.f; ///< Facteur de mise à l'échelle DPI

#if defined(NKENTSEU_FAMILY_WINDOWS)
    HWND      hwnd      = nullptr; ///< Handle natif Win32
    HINSTANCE hinstance = nullptr; ///< Instance de l'application

#elif defined(NKENTSEU_PLATFORM_COCOA)
    NSView*       view       = nullptr; ///< Vue Cocoa (NSView)
    CAMetalLayer* metalLayer = nullptr; ///< Couche Metal

#elif defined(NKENTSEU_PLATFORM_UIKIT)
    UIView*       view       = nullptr; ///< Vue UIKit
    CAMetalLayer* metalLayer = nullptr; ///< Couche Metal

#elif defined(NKENTSEU_PLATFORM_XCB)
    xcb_connection_t* connection = nullptr; ///< Connexion XCB
    xcb_window_t      window     = 0;       ///< Identifiant de fenêtre XCB

#elif defined(NKENTSEU_PLATFORM_XLIB)
    Display* display = nullptr; ///< Connexion Xlib
    ::Window window  = 0;       ///< Identifiant de fenêtre Xlib

#elif defined(NKENTSEU_PLATFORM_ANDROID)
    ANativeWindow* nativeWindow = nullptr; ///< ANativeWindow Android

#elif defined(NKENTSEU_PLATFORM_WASM)
    const char* canvasId = "#canvas"; ///< ID du canvas HTML

#else
    void* dummy = nullptr; ///< Stub pour plateforme inconnue / Noop
#endif
};

// ---------------------------------------------------------------------------
// NkRendererConfig - configuration de création du renderer
// ---------------------------------------------------------------------------

struct NkRendererConfig
{
    NkRendererApi api         = NkRendererApi::NK_SOFTWARE;
    NkPixelFormat colorFormat = NkPixelFormat::NK_PIXEL_R8G8B8A8_UNORM;
    NkPixelFormat depthFormat = NkPixelFormat::NK_PIXEL_D24_UNORM_S8_UINT;
    NkU32         sampleCount = 1;     ///< MSAA (1 = désactivé)
    bool          vsync       = true;
    bool          debug       = false; ///< Couche de validation

    /// When true, BeginFrame() automatically resizes the framebuffer if the
    /// window dimensions have changed since the last frame — the application
    /// does not need to handle NkWindowResizeEvent manually.
    /// When false, the application calls Renderer::Resize() itself.
    bool          autoResizeFramebuffer = true;
};

// ---------------------------------------------------------------------------
// NkFramebufferInfo - infos du framebuffer
// ---------------------------------------------------------------------------

struct NkFramebufferInfo
{
    NkU32  width  = 0;
    NkU32  height = 0;
    NkU32  pitch  = 0;      ///< Octets par ligne (width * 4 pour RGBA8)
    NkU8*  pixels = nullptr; ///< Pointeur vers pixels (Software uniquement)
};

} // namespace nkentseu
