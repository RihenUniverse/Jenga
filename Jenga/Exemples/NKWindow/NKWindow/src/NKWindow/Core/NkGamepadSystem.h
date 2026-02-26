#pragma once

// =============================================================================
// NkGamepadSystem.h
// Système gamepad/joystick cross-platform.
//
// Architecture :
//   NkGamepadSystem        — singleton public (polling + callbacks)
//   INkGamepadBackend      — interface PIMPL par plateforme
//
// Backends :
//   NkWin32GamepadBackend  — XInput (Xbox) + DirectInput HID
//   NkCocoaGamepadBackend  — IOKit HID / GCController (macOS)
//   NkUIKitGamepadBackend  — GCController (iOS)
//   NkAndroidGamepadBackend— android/input.h AInputEvent
//   NkXCBGamepadBackend    — evdev /dev/input/js* + /dev/input/event*
//   NkXLibGamepadBackend   — evdev (même backend)
//   NkWASMGamepadBackend   — Gamepad Web API
//   NkNoopGamepadBackend   — stub headless
//
// Usage :
//   auto& gp = nkentseu::NkGamepadSystem::Instance();
//   gp.SetConnectCallback([](const NkGamepadInfo& info, bool connected) { ... });
//   gp.SetButtonCallback([](NkU32 idx, NkGamepadButton btn, NkButtonState st){ ... });
//   gp.SetAxisCallback  ([](NkU32 idx, NkGamepadAxis   ax,  float value)     { ... });
//
//   // Dans la boucle principale :
//   gp.PollGamepads();
//
//   // Accès direct à l'état :
//   const NkGamepadStateData& state = gp.GetState(0);
//   if (state.IsButtonDown(NkGamepadButton::NK_GP_A)) { ... }
//
//   // Vibration :
//   gp.Rumble(0, 0.5f, 0.3f, 0.f, 0.f, 200);
// =============================================================================

#include "Events/NkGamepadEvents.h"
#include <functional>
#include <memory>
#include <array>

/**
 * @brief Namespace nkentseu.
 */
namespace nkentseu {

// Constante : max manettes supportées simultanément
inline constexpr NkU32 NK_MAX_GAMEPADS = 8;

// ---------------------------------------------------------------------------
// Callbacks
// ---------------------------------------------------------------------------

using NkGamepadConnectCallback = std::function<void(const NkGamepadInfo &, bool connected)>;
using NkGamepadButtonCallback = std::function<void(NkU32 idx, NkGamepadButton, NkButtonState)>;
using NkGamepadAxisCallback = std::function<void(NkU32 idx, NkGamepadAxis, float value)>;
using NkGamepadRumbleRequest = NkGamepadRumbleData;

// ---------------------------------------------------------------------------
// INkGamepadBackend — interface PIMPL
// ---------------------------------------------------------------------------

/**
 * @brief Platform backend interface for gamepad polling and control.
 */
class INkGamepadBackend {
public:
	virtual ~INkGamepadBackend() = default;

	/// Initialise le backend (ouvre les devices, enregistre les callbacks OS…)
	virtual bool Init() = 0;

	/// Libère toutes les ressources.
	virtual void Shutdown() = 0;

	/// Pompe les événements gamepad et remplit les états internes.
	virtual void Poll() = 0;

	/// Nombre de manettes actuellement connectées.
	virtual NkU32 GetConnectedCount() const = 0;

	/// Infos sur la manette à l'indice idx (0-based).
	virtual const NkGamepadInfo &GetInfo(NkU32 idx) const = 0;

	/// Snapshot complet de l'état courant.
	virtual const NkGamepadStateData &GetState(NkU32 idx) const = 0;

	/// Lance une vibration. Implémentation peut ignorer si non supporté.
	virtual void Rumble(NkU32 idx, float motorLow, float motorHigh, float triggerLeft, float triggerRight,
						NkU32 durationMs) = 0;

	/// LED de couleur (DualSense, Joy-Con).  RGBA 0xRRGGBBAA.
	virtual void SetLEDColor(NkU32 idx, NkU32 rgba) {
		(void)idx;
		(void)rgba;
	}

	/// Gyro/accéléromètre disponible ?
	virtual bool HasMotion(NkU32 idx) const {
		(void)idx;
		return false;
	}
};

// ---------------------------------------------------------------------------
// NkGamepadSystem — façade singleton
// ---------------------------------------------------------------------------

/**
 * @brief Cross-platform gamepad system facade.
 *
 * PollGamepads() updates backend state, emits callbacks and injects
 * NK_GAMEPAD_* events into the EventSystem queue.
 */
class NkGamepadSystem {
public:
	/// @brief Access singleton instance.
	static NkGamepadSystem &Instance();

	NkGamepadSystem(const NkGamepadSystem &) = delete;
	NkGamepadSystem &operator=(const NkGamepadSystem &) = delete;

	// -----------------------------------------------------------------------
	// Cycle de vie (appelé par NkSystem::Initialise / Close)
	// -----------------------------------------------------------------------

	/// @brief Initialize backend and internal state.
	bool Init();
	/// @brief Shutdown backend and clear state.
	void Shutdown();
	bool IsReady() const {
		return mReady;
	}

	// -----------------------------------------------------------------------
	// Pompe (appeler chaque trame dans la boucle principale)
	// -----------------------------------------------------------------------

	/// @brief Poll backend, detect deltas and emit gamepad events.
	void PollGamepads();

	// -----------------------------------------------------------------------
	// Callbacks
	// -----------------------------------------------------------------------

	void SetConnectCallback(NkGamepadConnectCallback cb) {
		mConnectCb = std::move(cb);
	}
	void SetButtonCallback(NkGamepadButtonCallback cb) {
		mButtonCb = std::move(cb);
	}
	void SetAxisCallback(NkGamepadAxisCallback cb) {
		mAxisCb = std::move(cb);
	}

	// -----------------------------------------------------------------------
	// Accès direct à l'état (polling)
	// -----------------------------------------------------------------------

	/// @brief Number of connected gamepads.
	NkU32 GetConnectedCount() const;
	/// @brief True if gamepad index is connected.
	bool IsConnected(NkU32 idx) const;
	/// @brief Device info for a connected gamepad index.
	const NkGamepadInfo &GetInfo(NkU32 idx) const;
	/// @brief Snapshot state for a gamepad index.
	const NkGamepadStateData &GetState(NkU32 idx) const;

	bool IsButtonDown(NkU32 idx, NkGamepadButton btn) const;
	float GetAxis(NkU32 idx, NkGamepadAxis ax) const;

	// -----------------------------------------------------------------------
	// Sortie / commandes
	// -----------------------------------------------------------------------

	/// Lance une vibration sur la manette idx.
	void Rumble(NkU32 idx, float motorLow = 0.f, float motorHigh = 0.f, float triggerLeft = 0.f,
				float triggerRight = 0.f, NkU32 durationMs = 0);

	/// LED (DualSense, Joy-Con…).
	void SetLEDColor(NkU32 idx, NkU32 rgba);

	// -----------------------------------------------------------------------
	// Accès backend
	// -----------------------------------------------------------------------

	INkGamepadBackend *GetBackend() {
		return mBackend.get();
	}

private:
	NkGamepadSystem() = default;

	void FireConnect(const NkGamepadInfo &info, bool connected);
	void FireButton(NkU32 idx, NkGamepadButton btn, NkButtonState st);
	void FireAxis(NkU32 idx, NkGamepadAxis ax, float value, float prevValue);

	std::unique_ptr<INkGamepadBackend> mBackend;
	bool mReady = false;

	NkGamepadConnectCallback mConnectCb;
	NkGamepadButtonCallback mButtonCb;
	NkGamepadAxisCallback mAxisCb;

	// États précédents pour détection delta (boutons + axes)
	std::array<NkGamepadStateData, NK_MAX_GAMEPADS> mPrevState;
	static NkGamepadStateData sDummyState;
	static NkGamepadInfo sDummyInfo;
};

// ---------------------------------------------------------------------------
// Raccourcis globaux
// ---------------------------------------------------------------------------

/// @brief Convenience accessor for NkGamepadSystem singleton.
inline NkGamepadSystem &NkGamepads() {
	return NkGamepadSystem::Instance();
}

} // namespace nkentseu
