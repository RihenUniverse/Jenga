#pragma once

// =============================================================================
// NkWin32WindowImpl.h
// Implémentation Win32 de IWindowImpl.
//
// V2 — Responsabilité réduite : uniquement la fenêtre.
//   - Pas de pointeur vers EventImpl stocké.
//   - Pas de WndProc, pas de table HWND (tout dans NkWin32EventImpl).
//   - Pas de BlitSoftwareFramebuffer, GetSurfaceDesc reste pour Renderer.
//   - Pas de SetBackgroundColor / GetBackgroundColor.
//   - Create() appelle NkGetEventImpl()->Initialize() pour s'enregistrer.
//   - Close() appelle NkGetEventImpl()->Shutdown() pour se désenregistrer.
// =============================================================================

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <Windows.h>
#include <ShObjIdl.h>

#include "../../Core/IWindowImpl.h"

namespace nkentseu
{

// ---------------------------------------------------------------------------
// Données internes Win32 — pas de eventImpl, pas d'état rendu
// ---------------------------------------------------------------------------

struct NkWin32Data
{
    HWND           hwnd        = nullptr;
    HINSTANCE      hinstance   = nullptr;
    DWORD          dwStyle     = 0;
    DWORD          dwExStyle   = 0;
    DEVMODE        dmScreen    = {};
    ITaskbarList3* taskbarList = nullptr;
    bool           isOpen      = false;
};

// ---------------------------------------------------------------------------
// NkWin32WindowImpl
// ---------------------------------------------------------------------------

class NkWin32WindowImpl : public IWindowImpl
{
public:
    NkWin32WindowImpl()  = default;
    ~NkWin32WindowImpl() override;

    bool Create(const NkWindowConfig& config) override;
    void Close()  override;
    bool IsOpen() const override;

    std::string GetTitle()           const override;
    NkVec2u     GetSize()            const override;
    NkVec2u     GetPosition()        const override;
    float       GetDpiScale()        const override;
    NkVec2u     GetDisplaySize()     const override;
    NkVec2u     GetDisplayPosition() const override;
    NkError     GetLastError()       const override;

    void SetTitle(const std::string& title)  override;
    void SetSize(NkU32 w, NkU32 h)           override;
    void SetPosition(NkI32 x, NkI32 y)       override;
    void SetVisible(bool v)                  override;
    void Minimize()                          override;
    void Maximize()                          override;
    void Restore()                           override;
    void SetFullscreen(bool fs)              override;

    void SetMousePosition(NkU32 x, NkU32 y) override;
    void ShowMouse(bool show)                override;
    void CaptureMouse(bool cap)              override;

    void SetProgress(float progress)         override;

    NkSurfaceDesc GetSurfaceDesc() const     override;

    // Accès interne pour NkWin32EventImpl
    HWND                  GetHwnd()   const { return mData.hwnd;   }
    HINSTANCE             GetHInstance() const { return mData.hinstance; }
    const NkWindowConfig& GetConfig() const { return mConfig;      }
    DWORD                 GetStyle()  const { return mData.dwStyle; }

private:
    NkWin32Data mData;
};

} // namespace nkentseu
