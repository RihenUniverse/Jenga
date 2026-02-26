#pragma once

#include <cstring>

// =============================================================================
// NkScancode.h
// Scancodes physiques cross-platform basés sur l'USB HID Usage Table 1.3
// (Section 10 — Keyboard/Keypad).
//
// DIFFÉRENCE FONDAMENTALE :
// ─────────────────────────────────────────────────────────────────────────────
//   NkKey      = CODE LOGIQUE (layout-agnostic)
//                Identifie la POSITION physique de la touche sur un clavier
//                US-QWERTY standard. Le même NkKey::NK_Q correspond toujours
//                à la touche "en haut à gauche des lettres", quelle que soit
//                la langue du clavier.
//                → Idéal pour les raccourcis clavier (Ctrl+Z, WASD…)
//
//   NkScancode = CODE MATÉRIEL (scancode USB HID ou scancode OS brut)
//                Identifie exactement quelle touche physique a été pressée
//                sur le matériel. Invariant à travers les OS et les drivers.
//                Sur un clavier AZERTY, la touche physique qui génère 'A'
//                (en US) donne NkScancode::NK_SC_A mais NkKey::NK_Q.
//                → Idéal pour la saisie de texte et la détection d'appui
//                  indépendamment du layout (jeux multi-langues).
//
//   nativeKey  = CODE OS BRUT (VK_ Win32, KeySym X11, keyCode DOM…)
//                Valeur brute telle que fournie par l'OS. Non portable.
//                → Utile pour le débogage ou des cas très spécifiques.
//
// QUAND UTILISER QUOI :
// ─────────────────────────────────────────────────────────────────────────────
//   Raccourcis clavier               → NkKey  (ex: NK_Z pour undo)
//   Contrôles de jeu WASD            → NkKey  (position physique US invariante)
//   Saisie de texte (IME, layout)    → NkTextInputData::codepoint (Unicode)
//   Détection matérielle de touche   → NkScancode (HID, indépendant du layout)
//   Mapping touches physiques rares  → NkScancode + nativeKey pour fallback
//   Enregistrement de macros         → NkScancode (rejoue sur tout clavier)
//
// CORRESPONDANCE NkKey ↔ NkScancode :
// ─────────────────────────────────────────────────────────────────────────────
//   Sur un clavier US-QWERTY : NkKey et NkScancode correspondent 1-pour-1.
//   Sur un clavier AZERTY :
//     Appui sur la touche physique "A" (position QWERTY) →
//       NkKey::NK_Q      (position US-QWERTY de cette touche)
//       NkScancode::NK_SC_A (usage HID de cette touche physique = 0x04)
//
// PLATEFORMES :
// ─────────────────────────────────────────────────────────────────────────────
//   Win32  : MapVirtualKey(vk, MAPVK_VK_TO_VSC) → scancode PS/2 set 1
//            Converti vers NkScancode via NkScancodeFromWin32()
//   Linux  : XCB/XLib keycode - 8 = index dans la table XKB/evdev
//            Converti via NkScancodeFromLinux()
//   macOS  : NSEvent.keyCode = HID usage (quasiment 1-pour-1)
//            Converti via NkScancodeFromMac()
//   Web    : KeyboardEvent.code = string (e.g., "KeyA", "Space", "ArrowLeft")
//            Converti via NkScancodeFromDOMCode()
//   Android: AKeyEvent scancode (evdev Linux)
//            Converti via NkScancodeFromLinux()
// =============================================================================

#include "../NkTypes.h"
#include <string>

/**
 * @brief Namespace nkentseu.
 */
namespace nkentseu {

// ===========================================================================
// NkScancode — codes USB HID Keyboard/Keypad Usage (Table 10)
// Valeurs = USB HID Usage ID (0x00–0xFF)
// ===========================================================================

enum class NkScancode : NkU32 {
	NK_SC_UNKNOWN = 0,

	// ---[ 0x04–0x1D : Lettres A–Z (ordre USB HID, pas alphabétique) ]--------
	NK_SC_A = 0x04,
	NK_SC_B = 0x05,
	NK_SC_C = 0x06,
	NK_SC_D = 0x07,
	NK_SC_E = 0x08,
	NK_SC_F = 0x09,
	NK_SC_G = 0x0A,
	NK_SC_H = 0x0B,
	NK_SC_I = 0x0C,
	NK_SC_J = 0x0D,
	NK_SC_K = 0x0E,
	NK_SC_L = 0x0F,
	NK_SC_M = 0x10,
	NK_SC_N = 0x11,
	NK_SC_O = 0x12,
	NK_SC_P = 0x13,
	NK_SC_Q = 0x14,
	NK_SC_R = 0x15,
	NK_SC_S = 0x16,
	NK_SC_T = 0x17,
	NK_SC_U = 0x18,
	NK_SC_V = 0x19,
	NK_SC_W = 0x1A,
	NK_SC_X = 0x1B,
	NK_SC_Y = 0x1C,
	NK_SC_Z = 0x1D,

	// ---[ 0x1E–0x27 : Chiffres 1–0 ligne du haut ]---------------------------
	NK_SC_1 = 0x1E,
	NK_SC_2 = 0x1F,
	NK_SC_3 = 0x20,
	NK_SC_4 = 0x21,
	NK_SC_5 = 0x22,
	NK_SC_6 = 0x23,
	NK_SC_7 = 0x24,
	NK_SC_8 = 0x25,
	NK_SC_9 = 0x26,
	NK_SC_0 = 0x27,

	// ---[ 0x28–0x38 : Touches de contrôle principales ]----------------------
	NK_SC_ENTER = 0x28, ///< Enter (principal)
	NK_SC_ESCAPE = 0x29,
	NK_SC_BACKSPACE = 0x2A,
	NK_SC_TAB = 0x2B,
	NK_SC_SPACE = 0x2C,
	NK_SC_MINUS = 0x2D,		 ///< -_
	NK_SC_EQUALS = 0x2E,	 ///< =+
	NK_SC_LBRACKET = 0x2F,	 ///< [{
	NK_SC_RBRACKET = 0x30,	 ///< ]}
	NK_SC_BACKSLASH = 0x31,	 ///< \|
	NK_SC_NONUS_HASH = 0x32, ///< #~ (touches non-US ISO)
	NK_SC_SEMICOLON = 0x33,	 ///< ;:
	NK_SC_APOSTROPHE = 0x34, ///< '"
	NK_SC_GRAVE = 0x35,		 ///< `~
	NK_SC_COMMA = 0x36,		 ///< ,<
	NK_SC_PERIOD = 0x37,	 ///< .>
	NK_SC_SLASH = 0x38,		 ///< /?

	// ---[ 0x39–0x45 : Touches fonction ]-------------------------------------
	NK_SC_CAPS_LOCK = 0x39,
	NK_SC_F1 = 0x3A,
	NK_SC_F2 = 0x3B,
	NK_SC_F3 = 0x3C,
	NK_SC_F4 = 0x3D,
	NK_SC_F5 = 0x3E,
	NK_SC_F6 = 0x3F,
	NK_SC_F7 = 0x40,
	NK_SC_F8 = 0x41,
	NK_SC_F9 = 0x42,
	NK_SC_F10 = 0x43,
	NK_SC_F11 = 0x44,
	NK_SC_F12 = 0x45,

	// ---[ 0x46–0x4F : Bloc de contrôle supérieur droit ]--------------------
	NK_SC_PRINT_SCREEN = 0x46,
	NK_SC_SCROLL_LOCK = 0x47,
	NK_SC_PAUSE = 0x48,
	NK_SC_INSERT = 0x49,
	NK_SC_HOME = 0x4A,
	NK_SC_PAGE_UP = 0x4B,
	NK_SC_DELETE = 0x4C,
	NK_SC_END = 0x4D,
	NK_SC_PAGE_DOWN = 0x4E,
	NK_SC_RIGHT = 0x4F,
	NK_SC_LEFT = 0x50,
	NK_SC_DOWN = 0x51,
	NK_SC_UP = 0x52,

	// ---[ 0x53–0x63 : Pavé numérique ]---------------------------------------
	NK_SC_NUM_LOCK = 0x53,
	NK_SC_NUMPAD_DIV = 0x54,
	NK_SC_NUMPAD_MUL = 0x55,
	NK_SC_NUMPAD_SUB = 0x56,
	NK_SC_NUMPAD_ADD = 0x57,
	NK_SC_NUMPAD_ENTER = 0x58,
	NK_SC_NUMPAD_1 = 0x59,
	NK_SC_NUMPAD_2 = 0x5A,
	NK_SC_NUMPAD_3 = 0x5B,
	NK_SC_NUMPAD_4 = 0x5C,
	NK_SC_NUMPAD_5 = 0x5D,
	NK_SC_NUMPAD_6 = 0x5E,
	NK_SC_NUMPAD_7 = 0x5F,
	NK_SC_NUMPAD_8 = 0x60,
	NK_SC_NUMPAD_9 = 0x61,
	NK_SC_NUMPAD_0 = 0x62,
	NK_SC_NUMPAD_DOT = 0x63,

	// ---[ 0x64–0x67 : Touches ISO/additionnelles ]---------------------------
	NK_SC_NONUS_BACKSLASH = 0x64, ///< Touche ISO entre LShift et Z (claviers européens)
	NK_SC_APPLICATION = 0x65,	  ///< Menu contextuel (Windows key)
	NK_SC_POWER = 0x66,
	NK_SC_NUMPAD_EQUALS = 0x67, ///< = sur pavé numérique (Mac)

	// ---[ 0x68–0x6F : F13–F24 ]----------------------------------------------
	NK_SC_F13 = 0x68,
	NK_SC_F14 = 0x69,
	NK_SC_F15 = 0x6A,
	NK_SC_F16 = 0x6B,
	NK_SC_F17 = 0x6C,
	NK_SC_F18 = 0x6D,
	NK_SC_F19 = 0x6E,
	NK_SC_F20 = 0x6F,
	NK_SC_F21 = 0x70,
	NK_SC_F22 = 0x71,
	NK_SC_F23 = 0x72,
	NK_SC_F24 = 0x73,

	// ---[ 0x74–0x78 : Touches multimédia / contrôle ]------------------------
	NK_SC_EXECUTE = 0x74,
	NK_SC_HELP = 0x75,
	NK_SC_MENU = 0x76,
	NK_SC_SELECT = 0x77,
	NK_SC_STOP = 0x78,
	NK_SC_AGAIN = 0x79,
	NK_SC_UNDO = 0x7A,
	NK_SC_CUT = 0x7B,
	NK_SC_COPY = 0x7C,
	NK_SC_PASTE = 0x7D,
	NK_SC_FIND = 0x7E,
	NK_SC_MUTE = 0x7F,
	NK_SC_VOLUME_UP = 0x80,
	NK_SC_VOLUME_DOWN = 0x81,
	// Consumer/media aliases used by legacy key mapping code.
	NK_SC_MEDIA_PLAY_PAUSE = 0xE0CD,
	NK_SC_MEDIA_STOP = 0xE0B7,
	NK_SC_MEDIA_NEXT = 0xE0B5,
	NK_SC_MEDIA_PREV = 0xE0B6,

	// ---[ 0xE0–0xE7 : Touches modificatrices ]-------------------------------
	NK_SC_LCTRL = 0xE0,
	NK_SC_LSHIFT = 0xE1,
	NK_SC_LALT = 0xE2,
	NK_SC_LSUPER = 0xE3, ///< Win / Cmd / Meta gauche
	NK_SC_RCTRL = 0xE4,
	NK_SC_RSHIFT = 0xE5,
	NK_SC_RALT = 0xE6,	 ///< AltGr
	NK_SC_RSUPER = 0xE7, ///< Win / Cmd / Meta droit

	NK_SC_MAX = 0x100
};

// ===========================================================================
// Utilitaires de conversion
// ===========================================================================

/// Nom lisible du scancode (ex: "SC_A", "SC_SPACE")
const char *NkScancodeToString(NkScancode sc);

/// Convertit un scancode Win32 Set-1 (MAPVK_VK_TO_VSC) vers NkScancode USB HID
NkScancode NkScancodeFromWin32(NkU32 win32Scancode, bool extended);

/// Convertit un keycode Linux evdev (XCB/XLib) vers NkScancode USB HID
/// linux_keycode = xcb_keycode_t ou XLib keycode (soustrait -8 pour evdev)
NkScancode NkScancodeFromLinux(NkU32 linuxKeycode);

/// Convertit un keyCode macOS (NSEvent.keyCode) vers NkScancode USB HID
NkScancode NkScancodeFromMac(NkU32 macKeycode);

/// Convertit un DOM KeyboardEvent.code (WASM) vers NkScancode USB HID
/// domCode exemple: "KeyA", "Space", "ArrowLeft", "Numpad0"
NkScancode NkScancodeFromDOMCode(const char *domCode);

/// Convertit NkScancode vers NkKey (position US-QWERTY invariante)
/// Ce mapping est la table de référence keycode ← scancode
NkKey NkScancodeToKey(NkScancode sc);

// ===========================================================================
// Implémentation inline des conversions
// ===========================================================================

inline const char *NkScancodeToString(NkScancode sc) {
	switch (sc) {
		case NkScancode::NK_SC_A:
			return "SC_A";
		case NkScancode::NK_SC_B:
			return "SC_B";
		case NkScancode::NK_SC_C:
			return "SC_C";
		case NkScancode::NK_SC_D:
			return "SC_D";
		case NkScancode::NK_SC_E:
			return "SC_E";
		case NkScancode::NK_SC_F:
			return "SC_F";
		case NkScancode::NK_SC_G:
			return "SC_G";
		case NkScancode::NK_SC_H:
			return "SC_H";
		case NkScancode::NK_SC_I:
			return "SC_I";
		case NkScancode::NK_SC_J:
			return "SC_J";
		case NkScancode::NK_SC_K:
			return "SC_K";
		case NkScancode::NK_SC_L:
			return "SC_L";
		case NkScancode::NK_SC_M:
			return "SC_M";
		case NkScancode::NK_SC_N:
			return "SC_N";
		case NkScancode::NK_SC_O:
			return "SC_O";
		case NkScancode::NK_SC_P:
			return "SC_P";
		case NkScancode::NK_SC_Q:
			return "SC_Q";
		case NkScancode::NK_SC_R:
			return "SC_R";
		case NkScancode::NK_SC_S:
			return "SC_S";
		case NkScancode::NK_SC_T:
			return "SC_T";
		case NkScancode::NK_SC_U:
			return "SC_U";
		case NkScancode::NK_SC_V:
			return "SC_V";
		case NkScancode::NK_SC_W:
			return "SC_W";
		case NkScancode::NK_SC_X:
			return "SC_X";
		case NkScancode::NK_SC_Y:
			return "SC_Y";
		case NkScancode::NK_SC_Z:
			return "SC_Z";
		case NkScancode::NK_SC_1:
			return "SC_1";
		case NkScancode::NK_SC_2:
			return "SC_2";
		case NkScancode::NK_SC_3:
			return "SC_3";
		case NkScancode::NK_SC_4:
			return "SC_4";
		case NkScancode::NK_SC_5:
			return "SC_5";
		case NkScancode::NK_SC_6:
			return "SC_6";
		case NkScancode::NK_SC_7:
			return "SC_7";
		case NkScancode::NK_SC_8:
			return "SC_8";
		case NkScancode::NK_SC_9:
			return "SC_9";
		case NkScancode::NK_SC_0:
			return "SC_0";
		case NkScancode::NK_SC_ENTER:
			return "SC_ENTER";
		case NkScancode::NK_SC_ESCAPE:
			return "SC_ESCAPE";
		case NkScancode::NK_SC_BACKSPACE:
			return "SC_BACKSPACE";
		case NkScancode::NK_SC_TAB:
			return "SC_TAB";
		case NkScancode::NK_SC_SPACE:
			return "SC_SPACE";
		case NkScancode::NK_SC_MINUS:
			return "SC_MINUS";
		case NkScancode::NK_SC_EQUALS:
			return "SC_EQUALS";
		case NkScancode::NK_SC_LBRACKET:
			return "SC_LBRACKET";
		case NkScancode::NK_SC_RBRACKET:
			return "SC_RBRACKET";
		case NkScancode::NK_SC_BACKSLASH:
			return "SC_BACKSLASH";
		case NkScancode::NK_SC_SEMICOLON:
			return "SC_SEMICOLON";
		case NkScancode::NK_SC_APOSTROPHE:
			return "SC_APOSTROPHE";
		case NkScancode::NK_SC_GRAVE:
			return "SC_GRAVE";
		case NkScancode::NK_SC_COMMA:
			return "SC_COMMA";
		case NkScancode::NK_SC_PERIOD:
			return "SC_PERIOD";
		case NkScancode::NK_SC_SLASH:
			return "SC_SLASH";
		case NkScancode::NK_SC_CAPS_LOCK:
			return "SC_CAPS_LOCK";
		case NkScancode::NK_SC_F1:
			return "SC_F1";
		case NkScancode::NK_SC_F2:
			return "SC_F2";
		case NkScancode::NK_SC_F3:
			return "SC_F3";
		case NkScancode::NK_SC_F4:
			return "SC_F4";
		case NkScancode::NK_SC_F5:
			return "SC_F5";
		case NkScancode::NK_SC_F6:
			return "SC_F6";
		case NkScancode::NK_SC_F7:
			return "SC_F7";
		case NkScancode::NK_SC_F8:
			return "SC_F8";
		case NkScancode::NK_SC_F9:
			return "SC_F9";
		case NkScancode::NK_SC_F10:
			return "SC_F10";
		case NkScancode::NK_SC_F11:
			return "SC_F11";
		case NkScancode::NK_SC_F12:
			return "SC_F12";
		case NkScancode::NK_SC_PRINT_SCREEN:
			return "SC_PRINT_SCREEN";
		case NkScancode::NK_SC_SCROLL_LOCK:
			return "SC_SCROLL_LOCK";
		case NkScancode::NK_SC_PAUSE:
			return "SC_PAUSE";
		case NkScancode::NK_SC_INSERT:
			return "SC_INSERT";
		case NkScancode::NK_SC_HOME:
			return "SC_HOME";
		case NkScancode::NK_SC_PAGE_UP:
			return "SC_PAGE_UP";
		case NkScancode::NK_SC_DELETE:
			return "SC_DELETE";
		case NkScancode::NK_SC_END:
			return "SC_END";
		case NkScancode::NK_SC_PAGE_DOWN:
			return "SC_PAGE_DOWN";
		case NkScancode::NK_SC_RIGHT:
			return "SC_RIGHT";
		case NkScancode::NK_SC_LEFT:
			return "SC_LEFT";
		case NkScancode::NK_SC_DOWN:
			return "SC_DOWN";
		case NkScancode::NK_SC_UP:
			return "SC_UP";
		case NkScancode::NK_SC_NUM_LOCK:
			return "SC_NUM_LOCK";
		case NkScancode::NK_SC_NUMPAD_DIV:
			return "SC_NUMPAD_DIV";
		case NkScancode::NK_SC_NUMPAD_MUL:
			return "SC_NUMPAD_MUL";
		case NkScancode::NK_SC_NUMPAD_SUB:
			return "SC_NUMPAD_SUB";
		case NkScancode::NK_SC_NUMPAD_ADD:
			return "SC_NUMPAD_ADD";
		case NkScancode::NK_SC_NUMPAD_ENTER:
			return "SC_NUMPAD_ENTER";
		case NkScancode::NK_SC_NUMPAD_1:
			return "SC_NUMPAD_1";
		case NkScancode::NK_SC_NUMPAD_2:
			return "SC_NUMPAD_2";
		case NkScancode::NK_SC_NUMPAD_3:
			return "SC_NUMPAD_3";
		case NkScancode::NK_SC_NUMPAD_4:
			return "SC_NUMPAD_4";
		case NkScancode::NK_SC_NUMPAD_5:
			return "SC_NUMPAD_5";
		case NkScancode::NK_SC_NUMPAD_6:
			return "SC_NUMPAD_6";
		case NkScancode::NK_SC_NUMPAD_7:
			return "SC_NUMPAD_7";
		case NkScancode::NK_SC_NUMPAD_8:
			return "SC_NUMPAD_8";
		case NkScancode::NK_SC_NUMPAD_9:
			return "SC_NUMPAD_9";
		case NkScancode::NK_SC_NUMPAD_0:
			return "SC_NUMPAD_0";
		case NkScancode::NK_SC_NUMPAD_DOT:
			return "SC_NUMPAD_DOT";
		case NkScancode::NK_SC_NONUS_BACKSLASH:
			return "SC_NONUS_BACKSLASH";
		case NkScancode::NK_SC_APPLICATION:
			return "SC_APPLICATION";
		case NkScancode::NK_SC_NUMPAD_EQUALS:
			return "SC_NUMPAD_EQUALS";
		case NkScancode::NK_SC_MUTE:
			return "SC_MUTE";
		case NkScancode::NK_SC_VOLUME_UP:
			return "SC_VOLUME_UP";
		case NkScancode::NK_SC_VOLUME_DOWN:
			return "SC_VOLUME_DOWN";
		case NkScancode::NK_SC_LCTRL:
			return "SC_LCTRL";
		case NkScancode::NK_SC_LSHIFT:
			return "SC_LSHIFT";
		case NkScancode::NK_SC_LALT:
			return "SC_LALT";
		case NkScancode::NK_SC_LSUPER:
			return "SC_LSUPER";
		case NkScancode::NK_SC_RCTRL:
			return "SC_RCTRL";
		case NkScancode::NK_SC_RSHIFT:
			return "SC_RSHIFT";
		case NkScancode::NK_SC_RALT:
			return "SC_RALT";
		case NkScancode::NK_SC_RSUPER:
			return "SC_RSUPER";
		default:
			return "SC_UNKNOWN";
	}
}

// ---------------------------------------------------------------------------
// NkScancodeToKey — table de correspondance USB HID → NkKey (layout US-QWERTY)
// Sur un clavier US-QWERTY : NkScancode::NK_SC_Q → NkKey::NK_Q
// Sur un clavier AZERTY  : NkScancode::NK_SC_Q → NkKey::NK_Q aussi !
//   (car NkKey::NK_Q = "touche à la position du Q en QWERTY")
// Cette table est la référence absolue, indépendante du layout utilisateur.
// ---------------------------------------------------------------------------

inline NkKey NkScancodeToKey(NkScancode sc) {
	switch (sc) {
		case NkScancode::NK_SC_A:
			return NkKey::NK_A;
		case NkScancode::NK_SC_B:
			return NkKey::NK_B;
		case NkScancode::NK_SC_C:
			return NkKey::NK_C;
		case NkScancode::NK_SC_D:
			return NkKey::NK_D;
		case NkScancode::NK_SC_E:
			return NkKey::NK_E;
		case NkScancode::NK_SC_F:
			return NkKey::NK_F;
		case NkScancode::NK_SC_G:
			return NkKey::NK_G;
		case NkScancode::NK_SC_H:
			return NkKey::NK_H;
		case NkScancode::NK_SC_I:
			return NkKey::NK_I;
		case NkScancode::NK_SC_J:
			return NkKey::NK_J;
		case NkScancode::NK_SC_K:
			return NkKey::NK_K;
		case NkScancode::NK_SC_L:
			return NkKey::NK_L;
		case NkScancode::NK_SC_M:
			return NkKey::NK_M;
		case NkScancode::NK_SC_N:
			return NkKey::NK_N;
		case NkScancode::NK_SC_O:
			return NkKey::NK_O;
		case NkScancode::NK_SC_P:
			return NkKey::NK_P;
		case NkScancode::NK_SC_Q:
			return NkKey::NK_Q;
		case NkScancode::NK_SC_R:
			return NkKey::NK_R;
		case NkScancode::NK_SC_S:
			return NkKey::NK_S;
		case NkScancode::NK_SC_T:
			return NkKey::NK_T;
		case NkScancode::NK_SC_U:
			return NkKey::NK_U;
		case NkScancode::NK_SC_V:
			return NkKey::NK_V;
		case NkScancode::NK_SC_W:
			return NkKey::NK_W;
		case NkScancode::NK_SC_X:
			return NkKey::NK_X;
		case NkScancode::NK_SC_Y:
			return NkKey::NK_Y;
		case NkScancode::NK_SC_Z:
			return NkKey::NK_Z;
		case NkScancode::NK_SC_1:
			return NkKey::NK_NUM1;
		case NkScancode::NK_SC_2:
			return NkKey::NK_NUM2;
		case NkScancode::NK_SC_3:
			return NkKey::NK_NUM3;
		case NkScancode::NK_SC_4:
			return NkKey::NK_NUM4;
		case NkScancode::NK_SC_5:
			return NkKey::NK_NUM5;
		case NkScancode::NK_SC_6:
			return NkKey::NK_NUM6;
		case NkScancode::NK_SC_7:
			return NkKey::NK_NUM7;
		case NkScancode::NK_SC_8:
			return NkKey::NK_NUM8;
		case NkScancode::NK_SC_9:
			return NkKey::NK_NUM9;
		case NkScancode::NK_SC_0:
			return NkKey::NK_NUM0;
		case NkScancode::NK_SC_ENTER:
			return NkKey::NK_ENTER;
		case NkScancode::NK_SC_ESCAPE:
			return NkKey::NK_ESCAPE;
		case NkScancode::NK_SC_BACKSPACE:
			return NkKey::NK_BACK;
		case NkScancode::NK_SC_TAB:
			return NkKey::NK_TAB;
		case NkScancode::NK_SC_SPACE:
			return NkKey::NK_SPACE;
		case NkScancode::NK_SC_MINUS:
			return NkKey::NK_MINUS;
		case NkScancode::NK_SC_EQUALS:
			return NkKey::NK_EQUALS;
		case NkScancode::NK_SC_LBRACKET:
			return NkKey::NK_LBRACKET;
		case NkScancode::NK_SC_RBRACKET:
			return NkKey::NK_RBRACKET;
		case NkScancode::NK_SC_BACKSLASH:
			return NkKey::NK_BACKSLASH;
		case NkScancode::NK_SC_SEMICOLON:
			return NkKey::NK_SEMICOLON;
		case NkScancode::NK_SC_APOSTROPHE:
			return NkKey::NK_APOSTROPHE;
		case NkScancode::NK_SC_GRAVE:
			return NkKey::NK_GRAVE;
		case NkScancode::NK_SC_COMMA:
			return NkKey::NK_COMMA;
		case NkScancode::NK_SC_PERIOD:
			return NkKey::NK_PERIOD;
		case NkScancode::NK_SC_SLASH:
			return NkKey::NK_SLASH;
		case NkScancode::NK_SC_CAPS_LOCK:
			return NkKey::NK_CAPSLOCK;
		case NkScancode::NK_SC_F1:
			return NkKey::NK_F1;
		case NkScancode::NK_SC_F2:
			return NkKey::NK_F2;
		case NkScancode::NK_SC_F3:
			return NkKey::NK_F3;
		case NkScancode::NK_SC_F4:
			return NkKey::NK_F4;
		case NkScancode::NK_SC_F5:
			return NkKey::NK_F5;
		case NkScancode::NK_SC_F6:
			return NkKey::NK_F6;
		case NkScancode::NK_SC_F7:
			return NkKey::NK_F7;
		case NkScancode::NK_SC_F8:
			return NkKey::NK_F8;
		case NkScancode::NK_SC_F9:
			return NkKey::NK_F9;
		case NkScancode::NK_SC_F10:
			return NkKey::NK_F10;
		case NkScancode::NK_SC_F11:
			return NkKey::NK_F11;
		case NkScancode::NK_SC_F12:
			return NkKey::NK_F12;
		case NkScancode::NK_SC_F13:
			return NkKey::NK_F13;
		case NkScancode::NK_SC_F14:
			return NkKey::NK_F14;
		case NkScancode::NK_SC_F15:
			return NkKey::NK_F15;
		case NkScancode::NK_SC_F16:
			return NkKey::NK_F16;
		case NkScancode::NK_SC_F17:
			return NkKey::NK_F17;
		case NkScancode::NK_SC_F18:
			return NkKey::NK_F18;
		case NkScancode::NK_SC_F19:
			return NkKey::NK_F19;
		case NkScancode::NK_SC_F20:
			return NkKey::NK_F20;
		case NkScancode::NK_SC_F21:
			return NkKey::NK_F21;
		case NkScancode::NK_SC_F22:
			return NkKey::NK_F22;
		case NkScancode::NK_SC_F23:
			return NkKey::NK_F23;
		case NkScancode::NK_SC_F24:
			return NkKey::NK_F24;
		case NkScancode::NK_SC_PRINT_SCREEN:
			return NkKey::NK_PRINT_SCREEN;
		case NkScancode::NK_SC_SCROLL_LOCK:
			return NkKey::NK_SCROLL_LOCK;
		case NkScancode::NK_SC_PAUSE:
			return NkKey::NK_PAUSE_BREAK;
		case NkScancode::NK_SC_INSERT:
			return NkKey::NK_INSERT;
		case NkScancode::NK_SC_HOME:
			return NkKey::NK_HOME;
		case NkScancode::NK_SC_PAGE_UP:
			return NkKey::NK_PAGE_UP;
		case NkScancode::NK_SC_DELETE:
			return NkKey::NK_DELETE;
		case NkScancode::NK_SC_END:
			return NkKey::NK_END;
		case NkScancode::NK_SC_PAGE_DOWN:
			return NkKey::NK_PAGE_DOWN;
		case NkScancode::NK_SC_RIGHT:
			return NkKey::NK_RIGHT;
		case NkScancode::NK_SC_LEFT:
			return NkKey::NK_LEFT;
		case NkScancode::NK_SC_DOWN:
			return NkKey::NK_DOWN;
		case NkScancode::NK_SC_UP:
			return NkKey::NK_UP;
		case NkScancode::NK_SC_NUM_LOCK:
			return NkKey::NK_NUM_LOCK;
		case NkScancode::NK_SC_NUMPAD_DIV:
			return NkKey::NK_NUMPAD_DIV;
		case NkScancode::NK_SC_NUMPAD_MUL:
			return NkKey::NK_NUMPAD_MUL;
		case NkScancode::NK_SC_NUMPAD_SUB:
			return NkKey::NK_NUMPAD_SUB;
		case NkScancode::NK_SC_NUMPAD_ADD:
			return NkKey::NK_NUMPAD_ADD;
		case NkScancode::NK_SC_NUMPAD_ENTER:
			return NkKey::NK_NUMPAD_ENTER;
		case NkScancode::NK_SC_NUMPAD_1:
			return NkKey::NK_NUMPAD_1;
		case NkScancode::NK_SC_NUMPAD_2:
			return NkKey::NK_NUMPAD_2;
		case NkScancode::NK_SC_NUMPAD_3:
			return NkKey::NK_NUMPAD_3;
		case NkScancode::NK_SC_NUMPAD_4:
			return NkKey::NK_NUMPAD_4;
		case NkScancode::NK_SC_NUMPAD_5:
			return NkKey::NK_NUMPAD_5;
		case NkScancode::NK_SC_NUMPAD_6:
			return NkKey::NK_NUMPAD_6;
		case NkScancode::NK_SC_NUMPAD_7:
			return NkKey::NK_NUMPAD_7;
		case NkScancode::NK_SC_NUMPAD_8:
			return NkKey::NK_NUMPAD_8;
		case NkScancode::NK_SC_NUMPAD_9:
			return NkKey::NK_NUMPAD_9;
		case NkScancode::NK_SC_NUMPAD_0:
			return NkKey::NK_NUMPAD_0;
		case NkScancode::NK_SC_NUMPAD_DOT:
			return NkKey::NK_NUMPAD_DOT;
		case NkScancode::NK_SC_NUMPAD_EQUALS:
			return NkKey::NK_NUMPAD_EQUALS;
		case NkScancode::NK_SC_APPLICATION:
			return NkKey::NK_MENU;
		case NkScancode::NK_SC_MUTE:
			return NkKey::NK_MEDIA_MUTE;
		case NkScancode::NK_SC_VOLUME_UP:
			return NkKey::NK_MEDIA_VOLUME_UP;
		case NkScancode::NK_SC_VOLUME_DOWN:
			return NkKey::NK_MEDIA_VOLUME_DOWN;
		case NkScancode::NK_SC_LCTRL:
			return NkKey::NK_LCTRL;
		case NkScancode::NK_SC_LSHIFT:
			return NkKey::NK_LSHIFT;
		case NkScancode::NK_SC_LALT:
			return NkKey::NK_LALT;
		case NkScancode::NK_SC_LSUPER:
			return NkKey::NK_LSUPER;
		case NkScancode::NK_SC_RCTRL:
			return NkKey::NK_RCTRL;
		case NkScancode::NK_SC_RSHIFT:
			return NkKey::NK_RSHIFT;
		case NkScancode::NK_SC_RALT:
			return NkKey::NK_RALT;
		case NkScancode::NK_SC_RSUPER:
			return NkKey::NK_RSUPER;
		default:
			return NkKey::NK_UNKNOWN;
	}
}

// ---------------------------------------------------------------------------
// NkScancodeFromWin32 — PS/2 Set-1 → USB HID
//
// Win32 renvoie des scancodes PS/2 Set-1 via MapVirtualKey(VK, MAPVK_VK_TO_VSC).
// Les touches étendues (E0 prefix) ont le bit 8 fixé dans LPARAM bits 16-23.
//
// Note : Pour obtenir le scancode Win32 correct dans WM_KEYDOWN :
//   NkU32 scanWin32 = (LPARAM >> 16) & 0xFF;
//   bool extended   = (LPARAM >> 24) & 1;
//   NkScancode sc   = NkScancodeFromWin32(scanWin32, extended);
// ---------------------------------------------------------------------------

inline NkScancode NkScancodeFromWin32(NkU32 win32, bool ext) {
	// Table PS/2 Set-1 → USB HID
	// Valeurs non étendues
	static const NkScancode sTbl[0x80] = {
		/*00*/ NkScancode::NK_SC_UNKNOWN,
		/*01*/ NkScancode::NK_SC_ESCAPE,
		/*02*/ NkScancode::NK_SC_1,
		/*03*/ NkScancode::NK_SC_2,
		/*04*/ NkScancode::NK_SC_3,
		/*05*/ NkScancode::NK_SC_4,
		/*06*/ NkScancode::NK_SC_5,
		/*07*/ NkScancode::NK_SC_6,
		/*08*/ NkScancode::NK_SC_7,
		/*09*/ NkScancode::NK_SC_8,
		/*0A*/ NkScancode::NK_SC_9,
		/*0B*/ NkScancode::NK_SC_0,
		/*0C*/ NkScancode::NK_SC_MINUS,
		/*0D*/ NkScancode::NK_SC_EQUALS,
		/*0E*/ NkScancode::NK_SC_BACKSPACE,
		/*0F*/ NkScancode::NK_SC_TAB,
		/*10*/ NkScancode::NK_SC_Q,
		/*11*/ NkScancode::NK_SC_W,
		/*12*/ NkScancode::NK_SC_E,
		/*13*/ NkScancode::NK_SC_R,
		/*14*/ NkScancode::NK_SC_T,
		/*15*/ NkScancode::NK_SC_Y,
		/*16*/ NkScancode::NK_SC_U,
		/*17*/ NkScancode::NK_SC_I,
		/*18*/ NkScancode::NK_SC_O,
		/*19*/ NkScancode::NK_SC_P,
		/*1A*/ NkScancode::NK_SC_LBRACKET,
		/*1B*/ NkScancode::NK_SC_RBRACKET,
		/*1C*/ NkScancode::NK_SC_ENTER,
		/*1D*/ NkScancode::NK_SC_LCTRL,
		/*1E*/ NkScancode::NK_SC_A,
		/*1F*/ NkScancode::NK_SC_S,
		/*20*/ NkScancode::NK_SC_D,
		/*21*/ NkScancode::NK_SC_F,
		/*22*/ NkScancode::NK_SC_G,
		/*23*/ NkScancode::NK_SC_H,
		/*24*/ NkScancode::NK_SC_J,
		/*25*/ NkScancode::NK_SC_K,
		/*26*/ NkScancode::NK_SC_L,
		/*27*/ NkScancode::NK_SC_SEMICOLON,
		/*28*/ NkScancode::NK_SC_APOSTROPHE,
		/*29*/ NkScancode::NK_SC_GRAVE,
		/*2A*/ NkScancode::NK_SC_LSHIFT,
		/*2B*/ NkScancode::NK_SC_BACKSLASH,
		/*2C*/ NkScancode::NK_SC_Z,
		/*2D*/ NkScancode::NK_SC_X,
		/*2E*/ NkScancode::NK_SC_C,
		/*2F*/ NkScancode::NK_SC_V,
		/*30*/ NkScancode::NK_SC_B,
		/*31*/ NkScancode::NK_SC_N,
		/*32*/ NkScancode::NK_SC_M,
		/*33*/ NkScancode::NK_SC_COMMA,
		/*34*/ NkScancode::NK_SC_PERIOD,
		/*35*/ NkScancode::NK_SC_SLASH,
		/*36*/ NkScancode::NK_SC_RSHIFT,
		/*37*/ NkScancode::NK_SC_NUMPAD_MUL,
		/*38*/ NkScancode::NK_SC_LALT,
		/*39*/ NkScancode::NK_SC_SPACE,
		/*3A*/ NkScancode::NK_SC_CAPS_LOCK,
		/*3B*/ NkScancode::NK_SC_F1,
		/*3C*/ NkScancode::NK_SC_F2,
		/*3D*/ NkScancode::NK_SC_F3,
		/*3E*/ NkScancode::NK_SC_F4,
		/*3F*/ NkScancode::NK_SC_F5,
		/*40*/ NkScancode::NK_SC_F6,
		/*41*/ NkScancode::NK_SC_F7,
		/*42*/ NkScancode::NK_SC_F8,
		/*43*/ NkScancode::NK_SC_F9,
		/*44*/ NkScancode::NK_SC_F10,
		/*45*/ NkScancode::NK_SC_NUM_LOCK,
		/*46*/ NkScancode::NK_SC_SCROLL_LOCK,
		/*47*/ NkScancode::NK_SC_NUMPAD_7,
		/*48*/ NkScancode::NK_SC_NUMPAD_8,
		/*49*/ NkScancode::NK_SC_NUMPAD_9,
		/*4A*/ NkScancode::NK_SC_NUMPAD_SUB,
		/*4B*/ NkScancode::NK_SC_NUMPAD_4,
		/*4C*/ NkScancode::NK_SC_NUMPAD_5,
		/*4D*/ NkScancode::NK_SC_NUMPAD_6,
		/*4E*/ NkScancode::NK_SC_NUMPAD_ADD,
		/*4F*/ NkScancode::NK_SC_NUMPAD_1,
		/*50*/ NkScancode::NK_SC_NUMPAD_2,
		/*51*/ NkScancode::NK_SC_NUMPAD_3,
		/*52*/ NkScancode::NK_SC_NUMPAD_0,
		/*53*/ NkScancode::NK_SC_NUMPAD_DOT,
		/*54*/ NkScancode::NK_SC_UNKNOWN, // SysRq
		/*55*/ NkScancode::NK_SC_UNKNOWN,
		/*56*/ NkScancode::NK_SC_NONUS_BACKSLASH,
		/*57*/ NkScancode::NK_SC_F11,
		/*58*/ NkScancode::NK_SC_F12,
		// 0x59..0x7F → UNKNOWN
	};

	if (win32 >= 0x80)
		return NkScancode::NK_SC_UNKNOWN;

	if (ext) {
		// Touches étendues (préfixe E0 PS/2)
		switch (win32) {
			case 0x1C:
				return NkScancode::NK_SC_NUMPAD_ENTER;
			case 0x1D:
				return NkScancode::NK_SC_RCTRL;
			case 0x35:
				return NkScancode::NK_SC_NUMPAD_DIV;
			case 0x37:
				return NkScancode::NK_SC_PRINT_SCREEN;
			case 0x38:
				return NkScancode::NK_SC_RALT;
			case 0x47:
				return NkScancode::NK_SC_HOME;
			case 0x48:
				return NkScancode::NK_SC_UP;
			case 0x49:
				return NkScancode::NK_SC_PAGE_UP;
			case 0x4B:
				return NkScancode::NK_SC_LEFT;
			case 0x4D:
				return NkScancode::NK_SC_RIGHT;
			case 0x4F:
				return NkScancode::NK_SC_END;
			case 0x50:
				return NkScancode::NK_SC_DOWN;
			case 0x51:
				return NkScancode::NK_SC_PAGE_DOWN;
			case 0x52:
				return NkScancode::NK_SC_INSERT;
			case 0x53:
				return NkScancode::NK_SC_DELETE;
			case 0x5B:
				return NkScancode::NK_SC_LSUPER;
			case 0x5C:
				return NkScancode::NK_SC_RSUPER;
			case 0x5D:
				return NkScancode::NK_SC_APPLICATION;
			default:
				return NkScancode::NK_SC_UNKNOWN;
		}
	}

	return sTbl[win32];
}

// ---------------------------------------------------------------------------
// NkScancodeFromLinux — evdev keycode → USB HID
//
// Linux evdev : keycode = xcb_keycode_t / XLib keycode
// USB HID     = evdev keycode + 8  (définition Linux kernel)
// Donc : hid = linuxKeycode - 8 ... sauf que c'est pas tout à fait vrai,
// la vraie table est dans les sources du noyau (hid-input.c).
// On utilise ici la table complète evdev→HID.
//
// Usage XCB  : NkScancodeFromLinux(ev->detail)
// Usage XLib : NkScancodeFromLinux(event.xkey.keycode)
// ---------------------------------------------------------------------------

inline NkScancode NkScancodeFromLinux(NkU32 kc) {
	// evdev keycode → USB HID (table partielle, couvre 98% des claviers)
	// Source : linux/drivers/hid/hid-input.c + USB HID 1.11 Table 10
	switch (kc) {
		case 1:
			return NkScancode::NK_SC_ESCAPE;
		case 2:
			return NkScancode::NK_SC_1;
		case 3:
			return NkScancode::NK_SC_2;
		case 4:
			return NkScancode::NK_SC_3;
		case 5:
			return NkScancode::NK_SC_4;
		case 6:
			return NkScancode::NK_SC_5;
		case 7:
			return NkScancode::NK_SC_6;
		case 8:
			return NkScancode::NK_SC_7;
		case 9:
			return NkScancode::NK_SC_8;
		case 10:
			return NkScancode::NK_SC_9;
		case 11:
			return NkScancode::NK_SC_0;
		case 12:
			return NkScancode::NK_SC_MINUS;
		case 13:
			return NkScancode::NK_SC_EQUALS;
		case 14:
			return NkScancode::NK_SC_BACKSPACE;
		case 15:
			return NkScancode::NK_SC_TAB;
		case 16:
			return NkScancode::NK_SC_Q;
		case 17:
			return NkScancode::NK_SC_W;
		case 18:
			return NkScancode::NK_SC_E;
		case 19:
			return NkScancode::NK_SC_R;
		case 20:
			return NkScancode::NK_SC_T;
		case 21:
			return NkScancode::NK_SC_Y;
		case 22:
			return NkScancode::NK_SC_U;
		case 23:
			return NkScancode::NK_SC_I;
		case 24:
			return NkScancode::NK_SC_O;
		case 25:
			return NkScancode::NK_SC_P;
		case 26:
			return NkScancode::NK_SC_LBRACKET;
		case 27:
			return NkScancode::NK_SC_RBRACKET;
		case 28:
			return NkScancode::NK_SC_ENTER;
		case 29:
			return NkScancode::NK_SC_LCTRL;
		case 30:
			return NkScancode::NK_SC_A;
		case 31:
			return NkScancode::NK_SC_S;
		case 32:
			return NkScancode::NK_SC_D;
		case 33:
			return NkScancode::NK_SC_F;
		case 34:
			return NkScancode::NK_SC_G;
		case 35:
			return NkScancode::NK_SC_H;
		case 36:
			return NkScancode::NK_SC_J;
		case 37:
			return NkScancode::NK_SC_K;
		case 38:
			return NkScancode::NK_SC_L;
		case 39:
			return NkScancode::NK_SC_SEMICOLON;
		case 40:
			return NkScancode::NK_SC_APOSTROPHE;
		case 41:
			return NkScancode::NK_SC_GRAVE;
		case 42:
			return NkScancode::NK_SC_LSHIFT;
		case 43:
			return NkScancode::NK_SC_BACKSLASH;
		case 44:
			return NkScancode::NK_SC_Z;
		case 45:
			return NkScancode::NK_SC_X;
		case 46:
			return NkScancode::NK_SC_C;
		case 47:
			return NkScancode::NK_SC_V;
		case 48:
			return NkScancode::NK_SC_B;
		case 49:
			return NkScancode::NK_SC_N;
		case 50:
			return NkScancode::NK_SC_M;
		case 51:
			return NkScancode::NK_SC_COMMA;
		case 52:
			return NkScancode::NK_SC_PERIOD;
		case 53:
			return NkScancode::NK_SC_SLASH;
		case 54:
			return NkScancode::NK_SC_RSHIFT;
		case 55:
			return NkScancode::NK_SC_NUMPAD_MUL;
		case 56:
			return NkScancode::NK_SC_LALT;
		case 57:
			return NkScancode::NK_SC_SPACE;
		case 58:
			return NkScancode::NK_SC_CAPS_LOCK;
		case 59:
			return NkScancode::NK_SC_F1;
		case 60:
			return NkScancode::NK_SC_F2;
		case 61:
			return NkScancode::NK_SC_F3;
		case 62:
			return NkScancode::NK_SC_F4;
		case 63:
			return NkScancode::NK_SC_F5;
		case 64:
			return NkScancode::NK_SC_F6;
		case 65:
			return NkScancode::NK_SC_F7;
		case 66:
			return NkScancode::NK_SC_F8;
		case 67:
			return NkScancode::NK_SC_F9;
		case 68:
			return NkScancode::NK_SC_F10;
		case 69:
			return NkScancode::NK_SC_NUM_LOCK;
		case 70:
			return NkScancode::NK_SC_SCROLL_LOCK;
		case 71:
			return NkScancode::NK_SC_NUMPAD_7;
		case 72:
			return NkScancode::NK_SC_NUMPAD_8;
		case 73:
			return NkScancode::NK_SC_NUMPAD_9;
		case 74:
			return NkScancode::NK_SC_NUMPAD_SUB;
		case 75:
			return NkScancode::NK_SC_NUMPAD_4;
		case 76:
			return NkScancode::NK_SC_NUMPAD_5;
		case 77:
			return NkScancode::NK_SC_NUMPAD_6;
		case 78:
			return NkScancode::NK_SC_NUMPAD_ADD;
		case 79:
			return NkScancode::NK_SC_NUMPAD_1;
		case 80:
			return NkScancode::NK_SC_NUMPAD_2;
		case 81:
			return NkScancode::NK_SC_NUMPAD_3;
		case 82:
			return NkScancode::NK_SC_NUMPAD_0;
		case 83:
			return NkScancode::NK_SC_NUMPAD_DOT;
		case 86:
			return NkScancode::NK_SC_NONUS_BACKSLASH;
		case 87:
			return NkScancode::NK_SC_F11;
		case 88:
			return NkScancode::NK_SC_F12;
		case 96:
			return NkScancode::NK_SC_NUMPAD_ENTER;
		case 97:
			return NkScancode::NK_SC_RCTRL;
		case 98:
			return NkScancode::NK_SC_NUMPAD_DIV;
		case 99:
			return NkScancode::NK_SC_PRINT_SCREEN;
		case 100:
			return NkScancode::NK_SC_RALT;
		case 102:
			return NkScancode::NK_SC_HOME;
		case 103:
			return NkScancode::NK_SC_UP;
		case 104:
			return NkScancode::NK_SC_PAGE_UP;
		case 105:
			return NkScancode::NK_SC_LEFT;
		case 106:
			return NkScancode::NK_SC_RIGHT;
		case 107:
			return NkScancode::NK_SC_END;
		case 108:
			return NkScancode::NK_SC_DOWN;
		case 109:
			return NkScancode::NK_SC_PAGE_DOWN;
		case 110:
			return NkScancode::NK_SC_INSERT;
		case 111:
			return NkScancode::NK_SC_DELETE;
		case 113:
			return NkScancode::NK_SC_MUTE;
		case 114:
			return NkScancode::NK_SC_VOLUME_DOWN;
		case 115:
			return NkScancode::NK_SC_VOLUME_UP;
		case 119:
			return NkScancode::NK_SC_PAUSE;
		case 125:
			return NkScancode::NK_SC_LSUPER;
		case 126:
			return NkScancode::NK_SC_RSUPER;
		case 127:
			return NkScancode::NK_SC_APPLICATION;
		// XCB/XLib ajoute 8 au keycode evdev
		// Ex: xcb_keycode_t 9 = evdev 1 = Escape
		// → appeler avec keycode - 8 si source XCB/XLib
		default:
			return NkScancode::NK_SC_UNKNOWN;
	}
}

/// Version XCB/XLib : soustrait 8 avant de convertir
inline NkScancode NkScancodeFromXKeycode(NkU32 xkeycode) {
	return (xkeycode >= 8) ? NkScancodeFromLinux(xkeycode - 8) : NkScancode::NK_SC_UNKNOWN;
}

// ---------------------------------------------------------------------------
// NkScancodeFromMac — NSEvent.keyCode → USB HID
//
// Les keyCodes macOS sont presque identiques aux HID usage IDs mais avec
// quelques exceptions notables (certaines touches spéciales).
// ---------------------------------------------------------------------------

inline NkScancode NkScancodeFromMac(NkU32 kc) {
	switch (kc) {
		case 0x00:
			return NkScancode::NK_SC_A;
		case 0x01:
			return NkScancode::NK_SC_S;
		case 0x02:
			return NkScancode::NK_SC_D;
		case 0x03:
			return NkScancode::NK_SC_F;
		case 0x04:
			return NkScancode::NK_SC_H;
		case 0x05:
			return NkScancode::NK_SC_G;
		case 0x06:
			return NkScancode::NK_SC_Z;
		case 0x07:
			return NkScancode::NK_SC_X;
		case 0x08:
			return NkScancode::NK_SC_C;
		case 0x09:
			return NkScancode::NK_SC_V;
		case 0x0B:
			return NkScancode::NK_SC_B;
		case 0x0C:
			return NkScancode::NK_SC_Q;
		case 0x0D:
			return NkScancode::NK_SC_W;
		case 0x0E:
			return NkScancode::NK_SC_E;
		case 0x0F:
			return NkScancode::NK_SC_R;
		case 0x10:
			return NkScancode::NK_SC_Y;
		case 0x11:
			return NkScancode::NK_SC_T;
		case 0x12:
			return NkScancode::NK_SC_1;
		case 0x13:
			return NkScancode::NK_SC_2;
		case 0x14:
			return NkScancode::NK_SC_3;
		case 0x15:
			return NkScancode::NK_SC_4;
		case 0x16:
			return NkScancode::NK_SC_6;
		case 0x17:
			return NkScancode::NK_SC_5;
		case 0x18:
			return NkScancode::NK_SC_EQUALS;
		case 0x19:
			return NkScancode::NK_SC_9;
		case 0x1A:
			return NkScancode::NK_SC_7;
		case 0x1B:
			return NkScancode::NK_SC_MINUS;
		case 0x1C:
			return NkScancode::NK_SC_8;
		case 0x1D:
			return NkScancode::NK_SC_0;
		case 0x1E:
			return NkScancode::NK_SC_RBRACKET;
		case 0x1F:
			return NkScancode::NK_SC_O;
		case 0x20:
			return NkScancode::NK_SC_U;
		case 0x21:
			return NkScancode::NK_SC_LBRACKET;
		case 0x22:
			return NkScancode::NK_SC_I;
		case 0x23:
			return NkScancode::NK_SC_P;
		case 0x24:
			return NkScancode::NK_SC_ENTER;
		case 0x25:
			return NkScancode::NK_SC_L;
		case 0x26:
			return NkScancode::NK_SC_J;
		case 0x27:
			return NkScancode::NK_SC_APOSTROPHE;
		case 0x28:
			return NkScancode::NK_SC_K;
		case 0x29:
			return NkScancode::NK_SC_SEMICOLON;
		case 0x2A:
			return NkScancode::NK_SC_BACKSLASH;
		case 0x2B:
			return NkScancode::NK_SC_COMMA;
		case 0x2C:
			return NkScancode::NK_SC_SLASH;
		case 0x2D:
			return NkScancode::NK_SC_N;
		case 0x2E:
			return NkScancode::NK_SC_M;
		case 0x2F:
			return NkScancode::NK_SC_PERIOD;
		case 0x30:
			return NkScancode::NK_SC_TAB;
		case 0x31:
			return NkScancode::NK_SC_SPACE;
		case 0x32:
			return NkScancode::NK_SC_GRAVE;
		case 0x33:
			return NkScancode::NK_SC_BACKSPACE;
		case 0x35:
			return NkScancode::NK_SC_ESCAPE;
		case 0x37:
			return NkScancode::NK_SC_LSUPER; // Cmd gauche
		case 0x38:
			return NkScancode::NK_SC_LSHIFT;
		case 0x39:
			return NkScancode::NK_SC_CAPS_LOCK;
		case 0x3A:
			return NkScancode::NK_SC_LALT;
		case 0x3B:
			return NkScancode::NK_SC_LCTRL;
		case 0x3C:
			return NkScancode::NK_SC_RSHIFT;
		case 0x3D:
			return NkScancode::NK_SC_RALT;
		case 0x3E:
			return NkScancode::NK_SC_RCTRL;
		case 0x36:
			return NkScancode::NK_SC_RSUPER; // Cmd droit
		case 0x3F:
			return NkScancode::NK_SC_APPLICATION; // Fn
		case 0x40:
			return NkScancode::NK_SC_F17;
		case 0x41:
			return NkScancode::NK_SC_NUMPAD_DOT;
		case 0x43:
			return NkScancode::NK_SC_NUMPAD_MUL;
		case 0x45:
			return NkScancode::NK_SC_NUMPAD_ADD;
		case 0x47:
			return NkScancode::NK_SC_NUM_LOCK; // Clear sur Mac
		case 0x48:
			return NkScancode::NK_SC_VOLUME_UP;
		case 0x49:
			return NkScancode::NK_SC_VOLUME_DOWN;
		case 0x4A:
			return NkScancode::NK_SC_MUTE;
		case 0x4B:
			return NkScancode::NK_SC_NUMPAD_DIV;
		case 0x4C:
			return NkScancode::NK_SC_NUMPAD_ENTER;
		case 0x4E:
			return NkScancode::NK_SC_NUMPAD_SUB;
		case 0x4F:
			return NkScancode::NK_SC_F18;
		case 0x50:
			return NkScancode::NK_SC_F19;
		case 0x51:
			return NkScancode::NK_SC_NUMPAD_EQUALS;
		case 0x52:
			return NkScancode::NK_SC_NUMPAD_0;
		case 0x53:
			return NkScancode::NK_SC_NUMPAD_1;
		case 0x54:
			return NkScancode::NK_SC_NUMPAD_2;
		case 0x55:
			return NkScancode::NK_SC_NUMPAD_3;
		case 0x56:
			return NkScancode::NK_SC_NUMPAD_4;
		case 0x57:
			return NkScancode::NK_SC_NUMPAD_5;
		case 0x58:
			return NkScancode::NK_SC_NUMPAD_6;
		case 0x59:
			return NkScancode::NK_SC_NUMPAD_7;
		case 0x5A:
			return NkScancode::NK_SC_F20;
		case 0x5B:
			return NkScancode::NK_SC_NUMPAD_8;
		case 0x5C:
			return NkScancode::NK_SC_NUMPAD_9;
		case 0x60:
			return NkScancode::NK_SC_F5;
		case 0x61:
			return NkScancode::NK_SC_F6;
		case 0x62:
			return NkScancode::NK_SC_F7;
		case 0x63:
			return NkScancode::NK_SC_F3;
		case 0x64:
			return NkScancode::NK_SC_F8;
		case 0x65:
			return NkScancode::NK_SC_F9;
		case 0x67:
			return NkScancode::NK_SC_F11;
		case 0x69:
			return NkScancode::NK_SC_F13;
		case 0x6A:
			return NkScancode::NK_SC_F16;
		case 0x6B:
			return NkScancode::NK_SC_F14;
		case 0x6D:
			return NkScancode::NK_SC_F10;
		case 0x6F:
			return NkScancode::NK_SC_F12;
		case 0x71:
			return NkScancode::NK_SC_F15;
		case 0x72:
			return NkScancode::NK_SC_INSERT; // Help = Insert
		case 0x73:
			return NkScancode::NK_SC_HOME;
		case 0x74:
			return NkScancode::NK_SC_PAGE_UP;
		case 0x75:
			return NkScancode::NK_SC_DELETE;
		case 0x76:
			return NkScancode::NK_SC_F4;
		case 0x77:
			return NkScancode::NK_SC_END;
		case 0x78:
			return NkScancode::NK_SC_F2;
		case 0x79:
			return NkScancode::NK_SC_PAGE_DOWN;
		case 0x7A:
			return NkScancode::NK_SC_F1;
		case 0x7B:
			return NkScancode::NK_SC_LEFT;
		case 0x7C:
			return NkScancode::NK_SC_RIGHT;
		case 0x7D:
			return NkScancode::NK_SC_DOWN;
		case 0x7E:
			return NkScancode::NK_SC_UP;
		default:
			return NkScancode::NK_SC_UNKNOWN;
	}
}

// ---------------------------------------------------------------------------
// NkScancodeFromDOMCode — DOM KeyboardEvent.code → USB HID
// Référence : https://www.w3.org/TR/uievents-code/
// ---------------------------------------------------------------------------

inline NkScancode NkScancodeFromDOMCode(const char *code) {
	if (!code || !code[0])
		return NkScancode::NK_SC_UNKNOWN;

	// Comparaison par hash de la première lettre pour accélérer
	switch (code[0]) {
		case 'K': // Key*
			if (code[1] == 'e' && code[2] == 'y') {
				char c = code[3];
				if (c == 'A')
					return NkScancode::NK_SC_A;
				if (c == 'B')
					return NkScancode::NK_SC_B;
				if (c == 'C')
					return NkScancode::NK_SC_C;
				if (c == 'D')
					return NkScancode::NK_SC_D;
				if (c == 'E')
					return NkScancode::NK_SC_E;
				if (c == 'F')
					return NkScancode::NK_SC_F;
				if (c == 'G')
					return NkScancode::NK_SC_G;
				if (c == 'H')
					return NkScancode::NK_SC_H;
				if (c == 'I')
					return NkScancode::NK_SC_I;
				if (c == 'J')
					return NkScancode::NK_SC_J;
				if (c == 'K')
					return NkScancode::NK_SC_K;
				if (c == 'L')
					return NkScancode::NK_SC_L;
				if (c == 'M')
					return NkScancode::NK_SC_M;
				if (c == 'N')
					return NkScancode::NK_SC_N;
				if (c == 'O')
					return NkScancode::NK_SC_O;
				if (c == 'P')
					return NkScancode::NK_SC_P;
				if (c == 'Q')
					return NkScancode::NK_SC_Q;
				if (c == 'R')
					return NkScancode::NK_SC_R;
				if (c == 'S')
					return NkScancode::NK_SC_S;
				if (c == 'T')
					return NkScancode::NK_SC_T;
				if (c == 'U')
					return NkScancode::NK_SC_U;
				if (c == 'V')
					return NkScancode::NK_SC_V;
				if (c == 'W')
					return NkScancode::NK_SC_W;
				if (c == 'X')
					return NkScancode::NK_SC_X;
				if (c == 'Y')
					return NkScancode::NK_SC_Y;
				if (c == 'Z')
					return NkScancode::NK_SC_Z;
			}
			break;

		case 'D': // Digit* or Delete/End...
			if (code[1] == 'i' && code[2] == 'g' && code[3] == 'i' && code[4] == 't') {
				char c = code[5];
				if (c == '1')
					return NkScancode::NK_SC_1;
				if (c == '2')
					return NkScancode::NK_SC_2;
				if (c == '3')
					return NkScancode::NK_SC_3;
				if (c == '4')
					return NkScancode::NK_SC_4;
				if (c == '5')
					return NkScancode::NK_SC_5;
				if (c == '6')
					return NkScancode::NK_SC_6;
				if (c == '7')
					return NkScancode::NK_SC_7;
				if (c == '8')
					return NkScancode::NK_SC_8;
				if (c == '9')
					return NkScancode::NK_SC_9;
				if (c == '0')
					return NkScancode::NK_SC_0;
			}
			if (code[1] == 'e') {
				if (code[2] == 'l')
					return NkScancode::NK_SC_DELETE; // Delete
			}
			break;

		case 'N': // Numpad* or NumLock
			if (code[1] == 'u' && code[2] == 'm' && code[3] == 'p' && code[4] == 'a' && code[5] == 'd') {
				const char *k = code + 6;
				if (k[0] == '0')
					return NkScancode::NK_SC_NUMPAD_0;
				if (k[0] == '1')
					return NkScancode::NK_SC_NUMPAD_1;
				if (k[0] == '2')
					return NkScancode::NK_SC_NUMPAD_2;
				if (k[0] == '3')
					return NkScancode::NK_SC_NUMPAD_3;
				if (k[0] == '4')
					return NkScancode::NK_SC_NUMPAD_4;
				if (k[0] == '5')
					return NkScancode::NK_SC_NUMPAD_5;
				if (k[0] == '6')
					return NkScancode::NK_SC_NUMPAD_6;
				if (k[0] == '7')
					return NkScancode::NK_SC_NUMPAD_7;
				if (k[0] == '8')
					return NkScancode::NK_SC_NUMPAD_8;
				if (k[0] == '9')
					return NkScancode::NK_SC_NUMPAD_9;
				if (k[0] == 'D' && k[1] == 'e' && k[2] == 'c')
					return NkScancode::NK_SC_NUMPAD_DOT;
				if (k[0] == 'E' && k[1] == 'n')
					return NkScancode::NK_SC_NUMPAD_ENTER;
				if (k[0] == 'A' && k[1] == 'd')
					return NkScancode::NK_SC_NUMPAD_ADD;
				if (k[0] == 'S' && k[1] == 'u')
					return NkScancode::NK_SC_NUMPAD_SUB;
				if (k[0] == 'M' && k[1] == 'u')
					return NkScancode::NK_SC_NUMPAD_MUL;
				if (k[0] == 'D' && k[1] == 'i')
					return NkScancode::NK_SC_NUMPAD_DIV;
				if (k[0] == 'E' && k[1] == 'q')
					return NkScancode::NK_SC_NUMPAD_EQUALS;
			}
			if (code[1] == 'u' && code[2] == 'm' && code[3] == 'L')
				return NkScancode::NK_SC_NUM_LOCK;
			break;

		case 'F': // F1..F24
			if (code[1] == '1' || (code[1] >= '1' && code[1] <= '9')) {
				int fn = 0;
				if (code[2] == 0)
					fn = code[1] - '0';
				else
					fn = (code[1] - '0') * 10 + (code[2] - '0');
				switch (fn) {
					case 1:
						return NkScancode::NK_SC_F1;
					case 2:
						return NkScancode::NK_SC_F2;
					case 3:
						return NkScancode::NK_SC_F3;
					case 4:
						return NkScancode::NK_SC_F4;
					case 5:
						return NkScancode::NK_SC_F5;
					case 6:
						return NkScancode::NK_SC_F6;
					case 7:
						return NkScancode::NK_SC_F7;
					case 8:
						return NkScancode::NK_SC_F8;
					case 9:
						return NkScancode::NK_SC_F9;
					case 10:
						return NkScancode::NK_SC_F10;
					case 11:
						return NkScancode::NK_SC_F11;
					case 12:
						return NkScancode::NK_SC_F12;
					case 13:
						return NkScancode::NK_SC_F13;
					case 14:
						return NkScancode::NK_SC_F14;
					case 15:
						return NkScancode::NK_SC_F15;
					case 16:
						return NkScancode::NK_SC_F16;
					case 17:
						return NkScancode::NK_SC_F17;
					case 18:
						return NkScancode::NK_SC_F18;
					case 19:
						return NkScancode::NK_SC_F19;
					case 20:
						return NkScancode::NK_SC_F20;
					case 21:
						return NkScancode::NK_SC_F21;
					case 22:
						return NkScancode::NK_SC_F22;
					case 23:
						return NkScancode::NK_SC_F23;
					case 24:
						return NkScancode::NK_SC_F24;
				}
			}
			break;

		case 'A': // Arrow*, Alt*
			if (code[1] == 'r' && code[2] == 'r' && code[3] == 'o' && code[4] == 'w') {
				if (code[5] == 'L')
					return NkScancode::NK_SC_LEFT;
				if (code[5] == 'R')
					return NkScancode::NK_SC_RIGHT;
				if (code[5] == 'U')
					return NkScancode::NK_SC_UP;
				if (code[5] == 'D')
					return NkScancode::NK_SC_DOWN;
			}
			if (code[1] == 'l' && code[2] == 't') {
				if (code[3] == 'L')
					return NkScancode::NK_SC_LALT;
				if (code[3] == 'R')
					return NkScancode::NK_SC_RALT;
			}
			break;

		case 'S': // Space, Shift*, ScrollLock
			if (code[1] == 'p')
				return NkScancode::NK_SC_SPACE;
			if (code[1] == 'h' && code[2] == 'i' && code[3] == 'f' && code[4] == 't') {
				if (code[5] == 'L')
					return NkScancode::NK_SC_LSHIFT;
				if (code[5] == 'R')
					return NkScancode::NK_SC_RSHIFT;
			}
			if (code[1] == 'c')
				return NkScancode::NK_SC_SCROLL_LOCK; // ScrollLock
			break;

		case 'C': // Control*, CapsLock
			if (code[1] == 'o' && code[2] == 'n' && code[3] == 't' && code[4] == 'r') {
				if (code[7] == 'L')
					return NkScancode::NK_SC_LCTRL;
				if (code[7] == 'R')
					return NkScancode::NK_SC_RCTRL;
			}
			if (code[1] == 'a')
				return NkScancode::NK_SC_CAPS_LOCK;
			break;

		case 'M': // Meta*, MediaPlay...
			if (code[1] == 'e' && code[2] == 't' && code[3] == 'a') {
				if (code[4] == 'L')
					return NkScancode::NK_SC_LSUPER;
				if (code[4] == 'R')
					return NkScancode::NK_SC_RSUPER;
			}
			if (code[1] == 'e' && code[2] == 'd' && code[3] == 'i')
				return NkScancode::NK_SC_UNKNOWN;
			break;

		case 'E': // Enter, End
			if (code[1] == 'n' && code[2] == 't')
				return NkScancode::NK_SC_ENTER;
			if (code[1] == 'n' && code[2] == 'd')
				return NkScancode::NK_SC_END;
			if (code[1] == 's')
				return NkScancode::NK_SC_ESCAPE;
			break;

		case 'B': // Backspace, BackquoteIntlBackslash
			if (code[1] == 'a' && code[2] == 'c' && code[3] == 'k' && code[4] == 's')
				return NkScancode::NK_SC_BACKSPACE;
			if (code[1] == 'a' && code[2] == 'c' && code[3] == 'k' && code[4] == 'q')
				return NkScancode::NK_SC_GRAVE;
			if (code[1] == 'r')
				return NkScancode::NK_SC_UNKNOWN; // BrowserXxx
			break;

		case 'T': // Tab
			if (code[1] == 'a')
				return NkScancode::NK_SC_TAB;
			break;

		case 'P': // PageUp, PageDown, PrintScreen, Pause
			if (code[1] == 'a' && code[2] == 'g' && code[3] == 'e') {
				if (code[4] == 'U')
					return NkScancode::NK_SC_PAGE_UP;
				if (code[4] == 'D')
					return NkScancode::NK_SC_PAGE_DOWN;
			}
			if (code[1] == 'r' && code[2] == 'i')
				return NkScancode::NK_SC_PRINT_SCREEN;
			if (code[1] == 'a' && code[2] == 'u')
				return NkScancode::NK_SC_PAUSE;
			break;

		case 'H': // Home
			if (code[1] == 'o')
				return NkScancode::NK_SC_HOME;
			break;

		case 'I': // Insert
			if (code[1] == 'n' && code[2] == 's')
				return NkScancode::NK_SC_INSERT;
			break;

		case 'Q': // Quote, etc.
			if (code[1] == 'u' && code[2] == 'o')
				return NkScancode::NK_SC_APOSTROPHE;
			break;

		case 'G': // Backquote = Grave
			break;
	}

	// Touches ponctuelles
	struct {
		const char *dom;
		NkScancode sc;
	} kExtra[] = {{"Minus", NkScancode::NK_SC_MINUS},
				  {"Equal", NkScancode::NK_SC_EQUALS},
				  {"BracketLeft", NkScancode::NK_SC_LBRACKET},
				  {"BracketRight", NkScancode::NK_SC_RBRACKET},
				  {"Backslash", NkScancode::NK_SC_BACKSLASH},
				  {"Semicolon", NkScancode::NK_SC_SEMICOLON},
				  {"Quote", NkScancode::NK_SC_APOSTROPHE},
				  {"Backquote", NkScancode::NK_SC_GRAVE},
				  {"Comma", NkScancode::NK_SC_COMMA},
				  {"Period", NkScancode::NK_SC_PERIOD},
				  {"Slash", NkScancode::NK_SC_SLASH},
				  {"IntlBackslash", NkScancode::NK_SC_NONUS_BACKSLASH},
				  {"ContextMenu", NkScancode::NK_SC_APPLICATION},
				  {"OSLeft", NkScancode::NK_SC_LSUPER},
				  {"OSRight", NkScancode::NK_SC_RSUPER},
				  {"Volume_Mute", NkScancode::NK_SC_MUTE},
				  {"Volume_Up", NkScancode::NK_SC_VOLUME_UP},
				  {"Volume_Down", NkScancode::NK_SC_VOLUME_DOWN},
				  {nullptr, NkScancode::NK_SC_UNKNOWN}};
	for (auto *e = kExtra; e->dom; ++e)
		if (strcmp(code, e->dom) == 0)
			return e->sc;

	return NkScancode::NK_SC_UNKNOWN;
}

} // namespace nkentseu
