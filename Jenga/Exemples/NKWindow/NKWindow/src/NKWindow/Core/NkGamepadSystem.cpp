// =============================================================================
// NkGamepadSystem.cpp — implémentation façade + sélection backend
// =============================================================================

#include "NkGamepadSystem.h"
#include "NkPlatformDetect.h"
#include <algorithm>

// Sélection du backend gamepad par plateforme
#if defined(NKENTSEU_PLATFORM_WIN32)
#   include "../Platform/Win32/NkWin32GamepadBackend.h"
    using PlatformGamepadBackend = nkentseu::NkWin32GamepadBackend;

#elif defined(NKENTSEU_PLATFORM_UWP) || defined(NKENTSEU_PLATFORM_XBOX)
#   include "../Platform/UWP/NkUWPGamepadBackend.h"
    using PlatformGamepadBackend = nkentseu::NkUWPGamepadBackend;

#elif defined(NKENTSEU_PLATFORM_COCOA)
#   include "../Platform/Cocoa/NkCocoaGamepadBackend.h"
    using PlatformGamepadBackend = nkentseu::NkCocoaGamepadBackend;

#elif defined(NKENTSEU_PLATFORM_UIKIT)
#   include "../Platform/UIKit/NkUIKitGamepadBackend.h"
    using PlatformGamepadBackend = nkentseu::NkUIKitGamepadBackend;

#elif defined(NKENTSEU_PLATFORM_ANDROID)
#   include "../Platform/Android/NkAndroidGamepadBackend.h"
    using PlatformGamepadBackend = nkentseu::NkAndroidGamepadBackend;

#elif defined(NKENTSEU_PLATFORM_XCB) || defined(NKENTSEU_PLATFORM_XLIB)
#   include "../Platform/Linux/NkLinuxGamepadBackend.h"
    using PlatformGamepadBackend = nkentseu::NkLinuxGamepadBackend;

#elif defined(NKENTSEU_PLATFORM_WASM)
#   include "../Platform/WASM/NkWASMGamepadBackend.h"
    using PlatformGamepadBackend = nkentseu::NkWASMGamepadBackend;

#else
#   include "../Platform/Noop/NkNoopGamepadBackend.h"
    using PlatformGamepadBackend = nkentseu::NkNoopGamepadBackend;
#endif

namespace nkentseu
{

NkGamepadStateData NkGamepadSystem::sDummyState;
NkGamepadInfo      NkGamepadSystem::sDummyInfo;

// ---------------------------------------------------------------------------

NkGamepadSystem& NkGamepadSystem::Instance()
{
    static NkGamepadSystem sInstance;
    return sInstance;
}

// ---------------------------------------------------------------------------

bool NkGamepadSystem::Init()
{
    if (mReady) return true;
    mBackend = std::make_unique<PlatformGamepadBackend>();
    mReady   = mBackend->Init();
    for (auto& s : mPrevState) s = {};
    return mReady;
}

void NkGamepadSystem::Shutdown()
{
    if (!mReady) return;
    if (mBackend) mBackend->Shutdown();
    mBackend.reset();
    mReady = false;
}

// ---------------------------------------------------------------------------
// PollGamepads — détection deltas boutons/axes + fire callbacks
// ---------------------------------------------------------------------------

void NkGamepadSystem::PollGamepads()
{
    if (!mReady || !mBackend) return;
    mBackend->Poll();

    NkU32 count = mBackend->GetConnectedCount();
    for (NkU32 i = 0; i < NK_MAX_GAMEPADS; ++i)
    {
        const NkGamepadStateData& cur  = mBackend->GetState(i);
        const NkGamepadStateData& prev = mPrevState[i];

        // Connexion / déconnexion
        if (cur.connected != prev.connected)
            FireConnect(mBackend->GetInfo(i), cur.connected);

        if (!cur.connected) { mPrevState[i] = cur; continue; }

        // Boutons
        for (NkU32 b = 0; b < static_cast<NkU32>(NkGamepadButton::NK_GAMEPAD_BUTTON_MAX); ++b)
        {
            if (cur.buttons[b] != prev.buttons[b])
            {
                FireButton(i,
                    static_cast<NkGamepadButton>(b),
                    cur.buttons[b] ? NkButtonState::NK_PRESSED : NkButtonState::NK_RELEASED);
            }
        }

        // Axes
        constexpr float kAxisEps = 0.001f;
        for (NkU32 a = 0; a < static_cast<NkU32>(NkGamepadAxis::NK_GAMEPAD_AXIS_MAX); ++a)
        {
            float v = cur.axes[a], pv = prev.axes[a];
            if (std::abs(v - pv) > kAxisEps)
                FireAxis(i, static_cast<NkGamepadAxis>(a), v);
        }

        mPrevState[i] = cur;
    }
}

// ---------------------------------------------------------------------------

NkU32 NkGamepadSystem::GetConnectedCount() const
{ return mReady ? mBackend->GetConnectedCount() : 0; }

bool NkGamepadSystem::IsConnected(NkU32 idx) const
{ return mReady && idx < NK_MAX_GAMEPADS && mBackend->GetState(idx).connected; }

const NkGamepadInfo& NkGamepadSystem::GetInfo(NkU32 idx) const
{ return (mReady && idx < NK_MAX_GAMEPADS) ? mBackend->GetInfo(idx) : sDummyInfo; }

const NkGamepadStateData& NkGamepadSystem::GetState(NkU32 idx) const
{ return (mReady && idx < NK_MAX_GAMEPADS) ? mBackend->GetState(idx) : sDummyState; }

bool NkGamepadSystem::IsButtonDown(NkU32 idx, NkGamepadButton btn) const
{ return GetState(idx).IsButtonDown(btn); }

float NkGamepadSystem::GetAxis(NkU32 idx, NkGamepadAxis ax) const
{ return GetState(idx).GetAxis(ax); }

void NkGamepadSystem::Rumble(NkU32 idx,
    float motorLow, float motorHigh,
    float triggerLeft, float triggerRight, NkU32 durationMs)
{
    if (mReady && mBackend)
        mBackend->Rumble(idx, motorLow, motorHigh, triggerLeft, triggerRight, durationMs);
}

void NkGamepadSystem::SetLEDColor(NkU32 idx, NkU32 rgba)
{
    if (mReady && mBackend)
        mBackend->SetLEDColor(idx, rgba);
}

// ---------------------------------------------------------------------------

void NkGamepadSystem::FireConnect(const NkGamepadInfo& info, bool connected)
{ if (mConnectCb) mConnectCb(info, connected); }

void NkGamepadSystem::FireButton(NkU32 idx, NkGamepadButton btn, NkButtonState st)
{ if (mButtonCb) mButtonCb(idx, btn, st); }

void NkGamepadSystem::FireAxis(NkU32 idx, NkGamepadAxis ax, float value)
{ if (mAxisCb) mAxisCb(idx, ax, value); }

} // namespace nkentseu
