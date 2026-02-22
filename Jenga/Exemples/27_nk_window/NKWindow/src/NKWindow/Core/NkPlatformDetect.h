#pragma once

// =============================================================================
// NkPlatformDetect.h
// Détection automatique de la plateforme cible.
// Peut être surchargé par la chaîne de build (-DNKENTSEU_PLATFORM_WIN32=1).
// Convention macros : UPPER_SNAKE_CASE préfixé NKENTSEU_
// =============================================================================

// ---------------------------------------------------------------------------
// Détection automatique de la plateforme
// ---------------------------------------------------------------------------

#if defined(_GAMING_XBOX_SCARLETT) || defined(_GAMING_XBOX_XBOXONE) || defined(WINAPI_FAMILY_GAMES)
#   define NKENTSEU_PLATFORM_XBOX    1
#elif defined(WINAPI_FAMILY) && (WINAPI_FAMILY == WINAPI_FAMILY_APP)
#   define NKENTSEU_PLATFORM_UWP     1
#elif defined(_WIN32) || defined(_WIN64)
#   define NKENTSEU_PLATFORM_WIN32   1
#elif defined(__EMSCRIPTEN__)
#   define NKENTSEU_PLATFORM_WASM    1
#elif defined(__ANDROID__)
#   define NKENTSEU_PLATFORM_ANDROID 1
#elif defined(__APPLE__)
#   include <TargetConditionals.h>
#   if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
#       define NKENTSEU_PLATFORM_UIKIT  1
#   else
#       define NKENTSEU_PLATFORM_COCOA  1
#   endif
#elif defined(__linux__)
#   if defined(NKENTSEU_USE_XLIB)
#       define NKENTSEU_PLATFORM_XLIB   1
#   else
#       define NKENTSEU_PLATFORM_XCB    1
#   endif
#else
#   define NKENTSEU_PLATFORM_NOOP    1
#endif

// ---------------------------------------------------------------------------
// Familles de plateformes
// ---------------------------------------------------------------------------

#if defined(NKENTSEU_PLATFORM_WIN32) || defined(NKENTSEU_PLATFORM_UWP) || defined(NKENTSEU_PLATFORM_XBOX)
#   define NKENTSEU_FAMILY_WINDOWS   1
#endif

#if defined(NKENTSEU_PLATFORM_COCOA) || defined(NKENTSEU_PLATFORM_UIKIT)
#   define NKENTSEU_FAMILY_APPLE     1
#endif

#if defined(NKENTSEU_PLATFORM_XCB) || defined(NKENTSEU_PLATFORM_XLIB)
#   define NKENTSEU_FAMILY_LINUX     1
#endif

// ---------------------------------------------------------------------------
// Backends graphiques disponibles par plateforme
// ---------------------------------------------------------------------------

#if defined(NKENTSEU_FAMILY_WINDOWS)
#   define NKENTSEU_RENDERER_DX11_AVAILABLE     1
#   define NKENTSEU_RENDERER_DX12_AVAILABLE     1
#   define NKENTSEU_RENDERER_VULKAN_AVAILABLE   1
#   define NKENTSEU_RENDERER_OPENGL_AVAILABLE   1
#   define NKENTSEU_RENDERER_SOFTWARE_AVAILABLE 1
#endif

#if defined(NKENTSEU_FAMILY_APPLE)
#   define NKENTSEU_RENDERER_METAL_AVAILABLE    1
#   define NKENTSEU_RENDERER_VULKAN_AVAILABLE   1
#   define NKENTSEU_RENDERER_OPENGL_AVAILABLE   1
#   define NKENTSEU_RENDERER_SOFTWARE_AVAILABLE 1
#endif

#if defined(NKENTSEU_FAMILY_LINUX)
#   define NKENTSEU_RENDERER_VULKAN_AVAILABLE   1
#   define NKENTSEU_RENDERER_OPENGL_AVAILABLE   1
#   define NKENTSEU_RENDERER_SOFTWARE_AVAILABLE 1
#endif

#if defined(NKENTSEU_PLATFORM_ANDROID)
#   define NKENTSEU_RENDERER_VULKAN_AVAILABLE   1
#   define NKENTSEU_RENDERER_OPENGL_AVAILABLE   1
#   define NKENTSEU_RENDERER_SOFTWARE_AVAILABLE 1
#endif

#if defined(NKENTSEU_PLATFORM_WASM)
#   define NKENTSEU_RENDERER_OPENGL_AVAILABLE   1
#   define NKENTSEU_RENDERER_SOFTWARE_AVAILABLE 1
#endif

// ---------------------------------------------------------------------------
// Macros utilitaires
// ---------------------------------------------------------------------------

#if defined(NKENTSEU_FAMILY_WINDOWS)
#   define NKENTSEU_API __declspec(dllexport)
#else
#   define NKENTSEU_API __attribute__((visibility("default")))
#endif

#if defined(_MSC_VER)
#   define NKENTSEU_FORCEINLINE __forceinline
#else
#   define NKENTSEU_FORCEINLINE __attribute__((always_inline)) inline
#endif

#define NKENTSEU_UNUSED(x) (void)(x)

#define NKENTSEU_VERSION_MAJOR  1
#define NKENTSEU_VERSION_MINOR  0
#define NKENTSEU_VERSION_PATCH  0
#define NKENTSEU_VERSION_STRING "1.0.0"
