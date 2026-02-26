#pragma once

// =============================================================================
// NkMouseEvents.h
// Données et classes d'événements souris.
//
// Couvre :
//   NkMouseMoveData        — déplacement curseur (coordonnées client)
//   NkMouseRawData         — mouvement brut sans accélération
//   NkMouseButtonData      — bouton enfoncé / relâché / double-clic
//   NkMouseWheelData       — molette verticale et horizontale
//   NkMouseCrossData       — entrée / sortie de la zone client
//   NkMouseCaptureData     — capture souris (SetCapture / ReleaseCapture)
// =============================================================================

#include "NkEventTypes.h"

/**
 * @brief Namespace nkentseu.
 */
namespace nkentseu {

// ===========================================================================
// NkMouseMoveData — déplacement du curseur dans la zone client
// ===========================================================================

struct NkMouseMoveData {
	static constexpr NkEventType TYPE = NkEventType::NK_MOUSE_MOVE;

	// Coordonnées dans la zone client (pixels physiques)
	NkI32 x = 0, y = 0;
	// Coordonnées écran absolu
	NkI32 screenX = 0, screenY = 0;
	// Déplacement depuis le dernier événement MOUSE_MOVE
	NkI32 deltaX = 0, deltaY = 0;
	// Boutons enfoncés au moment du déplacement (masque de bits NkMouseButton)
	NkU32 buttonsDown = 0;
	NkModifierState modifiers;

	NkMouseMoveData() = default;
	NkMouseMoveData(NkI32 x, NkI32 y, NkI32 sx, NkI32 sy, NkI32 dx = 0, NkI32 dy = 0, NkU32 btns = 0,
					NkModifierState mods = {})
		: x(x), y(y), screenX(sx), screenY(sy), deltaX(dx), deltaY(dy), buttonsDown(btns), modifiers(mods) {
	}

	bool IsButtonDown(NkMouseButton b) const {
		return (buttonsDown & (1u << static_cast<NkU32>(b))) != 0;
	}

	std::string ToString() const {
		return "MouseMove(" + std::to_string(x) + "," + std::to_string(y) + " delta=" + std::to_string(deltaX) + "," +
			   std::to_string(deltaY) + ")";
	}
};

// ===========================================================================
// NkMouseRawData — mouvement brut (WM_INPUT / evdev / IOKit)
// ===========================================================================

struct NkMouseRawData {
	static constexpr NkEventType TYPE = NkEventType::NK_MOUSE_RAW;

	NkI32 deltaX = 0; ///< Mouvement brut horizontal (unités HID, pas pixels)
	NkI32 deltaY = 0; ///< Mouvement brut vertical
	NkI32 deltaZ = 0; ///< Axe Z brut (certains périphériques)

	NkMouseRawData() = default;
	NkMouseRawData(NkI32 dx, NkI32 dy, NkI32 dz = 0) : deltaX(dx), deltaY(dy), deltaZ(dz) {
	}

	std::string ToString() const {
		return "MouseRaw(dx=" + std::to_string(deltaX) + ", dy=" + std::to_string(deltaY) + ")";
	}
};

// ===========================================================================
// NkMouseButtonData — bouton enfoncé, relâché, double-clic
// ===========================================================================

struct NkMouseButtonData {
	static constexpr NkEventType TYPE = NkEventType::NK_MOUSE_BUTTON_PRESS;

	NkMouseButton button = NkMouseButton::NK_MB_LEFT;
	NkButtonState state = NkButtonState::NK_PRESSED;
	NkModifierState modifiers;

	// Coordonnées du clic dans la zone client
	NkI32 x = 0, y = 0;
	// Coordonnées écran
	NkI32 screenX = 0, screenY = 0;

	// Pour les double-clics
	NkU32 clickCount = 1; ///< 1 = simple, 2 = double, 3 = triple…

	NkMouseButtonData() = default;
	NkMouseButtonData(NkMouseButton btn, NkButtonState st, NkI32 x, NkI32 y, NkI32 sx = 0, NkI32 sy = 0,
					  NkModifierState mods = {}, NkU32 clicks = 1)
		: button(btn), state(st), modifiers(mods), x(x), y(y), screenX(sx), screenY(sy), clickCount(clicks) {
	}

	bool IsPress() const {
		return state == NkButtonState::NK_PRESSED;
	}
	bool IsRelease() const {
		return state == NkButtonState::NK_RELEASED;
	}
	bool IsDoubleClick() const {
		return clickCount >= 2;
	}

	std::string ToString() const {
		std::string s = "MouseButton(";
		s += NkMouseButtonToString(button);
		s += ", ";
		s += NkButtonStateToString(state);
		s += " at " + std::to_string(x) + "," + std::to_string(y);
		if (clickCount > 1)
			s += " x" + std::to_string(clickCount);
		if (!modifiers.IsNone()) {
			s += ", ";
			s += modifiers.ToString();
		}
		s += ")";
		return s;
	}
};

// ===========================================================================
// NkMouseWheelData — molette (verticale et horizontale)
// ===========================================================================

struct NkMouseWheelData {
	static constexpr NkEventType TYPE = NkEventType::NK_MOUSE_WHEEL_VERTICAL;

	double delta = 0.0;	 ///< Défilement en "lignes" (positif = vers l'avant / haut)
	double deltaX = 0.0; ///< Défilement horizontal (molette tiltable ou pavé tactile)
	double deltaY = 0.0; ///< Défilement vertical (même valeur que delta pour simplicité)

	// Coordonnées curseur lors de l'événement
	NkI32 x = 0, y = 0;

	NkModifierState modifiers;

	// Précision : true = défilement à haute résolution (trackpad, souris de précision)
	bool highPrecision = false;

	// Facteur de pixels : combien de pixels défiler (pour les UIs à défilement continu)
	double pixelDeltaX = 0.0;
	double pixelDeltaY = 0.0;

	NkMouseWheelData() = default;
	NkMouseWheelData(double dy, double dx = 0.0, NkI32 cx = 0, NkI32 cy = 0, NkModifierState mods = {},
					 bool hiPrecision = false)
		: delta(dy), deltaX(dx), deltaY(dy), x(cx), y(cy), modifiers(mods), highPrecision(hiPrecision) {
	}

	bool IsVertical() const {
		return deltaY != 0.0;
	}
	bool IsHorizontal() const {
		return deltaX != 0.0;
	}
	bool ScrollsUp() const {
		return deltaY > 0.0;
	}
	bool ScrollsDown() const {
		return deltaY < 0.0;
	}
	bool ScrollsLeft() const {
		return deltaX < 0.0;
	}
	bool ScrollsRight() const {
		return deltaX > 0.0;
	}

	std::string ToString() const {
		std::string s = "MouseWheel(";
		if (deltaY != 0.0)
			s += "V=" + std::to_string(deltaY) + " ";
		if (deltaX != 0.0)
			s += "H=" + std::to_string(deltaX) + " ";
		if (highPrecision)
			s += "HiPrec ";
		if (!modifiers.IsNone())
			s += modifiers.ToString();
		s += ")";
		return s;
	}
};

// ===========================================================================
// NkMouseCrossData — entrée / sortie zone client
// ===========================================================================

struct NkMouseCrossData {
	static constexpr NkEventType TYPE = NkEventType::NK_MOUSE_ENTER;
	bool entered = false; ///< true = entré, false = sorti

	NkMouseCrossData() = default;
	explicit NkMouseCrossData(bool e) : entered(e) {
	}

	std::string ToString() const {
		return entered ? "MouseEnter" : "MouseLeave";
	}
};

// ===========================================================================
// NkMouseCaptureData — SetCapture / ReleaseCapture
// ===========================================================================

struct NkMouseCaptureData {
	static constexpr NkEventType TYPE = NkEventType::NK_MOUSE_CAPTURE_BEGIN;
	bool captured = false;

	NkMouseCaptureData() = default;
	explicit NkMouseCaptureData(bool c) : captured(c) {
	}

	std::string ToString() const {
		return captured ? "MouseCaptureBegin" : "MouseCaptureEnd";
	}
};

} // namespace nkentseu
