// =============================================================================
// NkWindow.cpp
// Implémentation de Window — sélectionne la bonne impl de plateforme.
// =============================================================================

#include "NkWindow.h"
#include "NkSystem.h"
#include "IEventImpl.h"
#include "NkPlatformDetect.h"

#if defined(NKENTSEU_PLATFORM_WIN32)
#   include "../Platform/Win32/NkWin32WindowImpl.h"
    using PlatformWindowImpl = nkentseu::NkWin32WindowImpl;
#elif defined(NKENTSEU_PLATFORM_UWP) || defined(NKENTSEU_PLATFORM_XBOX)
#   include "../Platform/UWP/NkUWPWindowImpl.h"
    using PlatformWindowImpl = nkentseu::NkUWPWindowImpl;
#elif defined(NKENTSEU_PLATFORM_COCOA)
#   include "../Platform/Cocoa/NkCocoaWindowImpl.h"
    using PlatformWindowImpl = nkentseu::NkCocoaWindowImpl;
#elif defined(NKENTSEU_PLATFORM_UIKIT)
#   include "../Platform/UIKit/NkUIKitWindowImpl.h"
    using PlatformWindowImpl = nkentseu::NkUIKitWindowImpl;
#elif defined(NKENTSEU_PLATFORM_XCB)
#   include "../Platform/XCB/NkXCBWindowImpl.h"
    using PlatformWindowImpl = nkentseu::NkXCBWindowImpl;
#elif defined(NKENTSEU_PLATFORM_XLIB)
#   include "../Platform/XLib/NkXLibWindowImpl.h"
    using PlatformWindowImpl = nkentseu::NkXLibWindowImpl;
#elif defined(NKENTSEU_PLATFORM_ANDROID)
#   include "../Platform/Android/NkAndroidWindowImpl.h"
    using PlatformWindowImpl = nkentseu::NkAndroidWindowImpl;
#elif defined(NKENTSEU_PLATFORM_WASM)
#   include "../Platform/WASM/NkWASMWindowImpl.h"
    using PlatformWindowImpl = nkentseu::NkWASMWindowImpl;
#else
#   include "../Platform/Noop/NkNoopWindowImpl.h"
    using PlatformWindowImpl = nkentseu::NkNoopWindowImpl;
#endif

namespace nkentseu
{

// ---------------------------------------------------------------------------
// Construction
// ---------------------------------------------------------------------------

Window::Window()
    : mImpl(std::make_unique<PlatformWindowImpl>())
{}

Window::Window(const NkWindowConfig& config)
    : mImpl(std::make_unique<PlatformWindowImpl>())
    , mConfig(config)
{
    Create(config);
}

Window::~Window()
{
    if (mImpl && mImpl->IsOpen())
        Close();
}

// ---------------------------------------------------------------------------
// Cycle de vie
// ---------------------------------------------------------------------------

bool Window::Create(const NkWindowConfig& config)
{
    mConfig = config;
    // L'impl crée la fenêtre et appelle NkGetEventImpl()->Initialize()
    return mImpl->Create(config);
}

void Window::Close()
{
    if (mImpl) mImpl->Close();
}

bool Window::IsOpen()  const { return mImpl && mImpl->IsOpen(); }
bool Window::IsValid() const { return IsOpen(); }

// ---------------------------------------------------------------------------
// Propriétés
// ---------------------------------------------------------------------------

std::string    Window::GetTitle()           const { return mImpl ? mImpl->GetTitle()           : "";       }
void           Window::SetTitle(const std::string& t)    { if (mImpl) mImpl->SetTitle(t);                   }
NkVec2u        Window::GetSize()            const { return mImpl ? mImpl->GetSize()            : NkVec2u{}; }
NkVec2u        Window::GetPosition()        const { return mImpl ? mImpl->GetPosition()        : NkVec2u{}; }
float          Window::GetDpiScale()        const { return mImpl ? mImpl->GetDpiScale()        : 1.f;       }
NkVec2u        Window::GetDisplaySize()     const { return mImpl ? mImpl->GetDisplaySize()     : NkVec2u{}; }
NkVec2u        Window::GetDisplayPosition() const { return mImpl ? mImpl->GetDisplayPosition() : NkVec2u{}; }
NkError        Window::GetLastError()       const { return mImpl ? mImpl->GetLastError()       : NkError::Ok(); }
NkWindowConfig Window::GetConfig()          const { return mConfig; }

// ---------------------------------------------------------------------------
// Manipulation
// ---------------------------------------------------------------------------

void Window::SetSize(NkU32 w, NkU32 h)     { if (mImpl) mImpl->SetSize(w, h);       }
void Window::SetPosition(NkI32 x, NkI32 y) { if (mImpl) mImpl->SetPosition(x, y);   }
void Window::SetVisible(bool v)             { if (mImpl) mImpl->SetVisible(v);        }
void Window::Minimize()                     { if (mImpl) mImpl->Minimize();           }
void Window::Maximize()                     { if (mImpl) mImpl->Maximize();           }
void Window::Restore()                      { if (mImpl) mImpl->Restore();            }
void Window::SetFullscreen(bool fs)         { if (mImpl) mImpl->SetFullscreen(fs);   }

// ---------------------------------------------------------------------------
// Souris
// ---------------------------------------------------------------------------

void Window::SetMousePosition(NkU32 x, NkU32 y) { if (mImpl) mImpl->SetMousePosition(x, y); }
void Window::ShowMouse(bool show)                 { if (mImpl) mImpl->ShowMouse(show);         }
void Window::CaptureMouse(bool cap)               { if (mImpl) mImpl->CaptureMouse(cap);       }

// ---------------------------------------------------------------------------
// OS extras
// ---------------------------------------------------------------------------

void Window::SetProgress(float p) { if (mImpl) mImpl->SetProgress(p); }

// ---------------------------------------------------------------------------
// Safe Area
// ---------------------------------------------------------------------------

NkSafeAreaInsets Window::GetSafeAreaInsets() const
{
    return mImpl ? mImpl->GetSafeAreaInsets() : NkSafeAreaInsets{};
}

// ---------------------------------------------------------------------------
// Surface (pour Renderer)
// ---------------------------------------------------------------------------

NkSafeAreaInsets Window::GetSafeAreaInsets() const
{
    return mImpl ? mImpl->GetSafeAreaInsets() : NkSafeAreaInsets{};
}

NkSurfaceDesc Window::GetSurfaceDesc() const
{
    return mImpl ? mImpl->GetSurfaceDesc() : NkSurfaceDesc{};
}

// ---------------------------------------------------------------------------
// Callback (délégué à l'EventImpl)
// ---------------------------------------------------------------------------

void Window::SetEventCallback(NkEventCallback cb)
{
    if (!mImpl) return;
    IEventImpl* ev = NkGetEventImpl();
    if (ev)
    {
        NkSurfaceDesc sd = mImpl->GetSurfaceDesc();
        // Passe le nativeHandle approprié à la plateforme
#if defined(NKENTSEU_FAMILY_WINDOWS)
        ev->SetWindowCallback(sd.hwnd, std::move(cb));
#elif defined(NKENTSEU_PLATFORM_XCB)
        ev->SetWindowCallback(reinterpret_cast<void*>(
            static_cast<uintptr_t>(sd.window)), std::move(cb));
#else
        ev->SetWindowCallback(sd.view, std::move(cb));
#endif
    }
}

} // namespace nkentseu
