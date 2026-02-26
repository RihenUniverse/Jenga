// =============================================================================
// NkEventTypes.cpp
// Implémentation des utilitaires NkEventType / NkKey / NkModifierState.
// =============================================================================

#include "NkEventTypes.h"
#include <string>

/**
 * @brief Namespace nkentseu.
 */
namespace nkentseu {

// ===========================================================================
// NkGetEventCategory
// ===========================================================================

NkEventCategory NkGetEventCategory(NkEventType type) {
	switch (type) {
		case NkEventType::NK_WINDOW_CREATE:
		case NkEventType::NK_WINDOW_CLOSE:
		case NkEventType::NK_WINDOW_DESTROY:
		case NkEventType::NK_WINDOW_PAINT:
		case NkEventType::NK_WINDOW_RESIZE:
		case NkEventType::NK_WINDOW_RESIZE_BEGIN:
		case NkEventType::NK_WINDOW_RESIZE_END:
		case NkEventType::NK_WINDOW_MOVE:
		case NkEventType::NK_WINDOW_MOVE_BEGIN:
		case NkEventType::NK_WINDOW_MOVE_END:
		case NkEventType::NK_WINDOW_FOCUS_GAINED:
		case NkEventType::NK_WINDOW_FOCUS_LOST:
		case NkEventType::NK_WINDOW_MINIMIZE:
		case NkEventType::NK_WINDOW_MAXIMIZE:
		case NkEventType::NK_WINDOW_RESTORE:
		case NkEventType::NK_WINDOW_FULLSCREEN:
		case NkEventType::NK_WINDOW_WINDOWED:
		case NkEventType::NK_WINDOW_DPI_CHANGE:
		case NkEventType::NK_WINDOW_THEME_CHANGE:
		case NkEventType::NK_WINDOW_SHOWN:
		case NkEventType::NK_WINDOW_HIDDEN:
			return NkEventCategory::NK_CAT_WINDOW;

		case NkEventType::NK_KEY_PRESS:
		case NkEventType::NK_KEY_REPEAT:
		case NkEventType::NK_KEY_RELEASE:
		case NkEventType::NK_TEXT_INPUT:
			return NkEventCategory::NK_CAT_KEYBOARD;

		case NkEventType::NK_MOUSE_MOVE:
		case NkEventType::NK_MOUSE_RAW:
		case NkEventType::NK_MOUSE_BUTTON_PRESS:
		case NkEventType::NK_MOUSE_BUTTON_RELEASE:
		case NkEventType::NK_MOUSE_DOUBLE_CLICK:
		case NkEventType::NK_MOUSE_WHEEL_VERTICAL:
		case NkEventType::NK_MOUSE_WHEEL_HORIZONTAL:
		case NkEventType::NK_MOUSE_ENTER:
		case NkEventType::NK_MOUSE_LEAVE:
		case NkEventType::NK_MOUSE_CAPTURE_BEGIN:
		case NkEventType::NK_MOUSE_CAPTURE_END:
			return NkEventCategory::NK_CAT_MOUSE;

		case NkEventType::NK_TOUCH_BEGIN:
		case NkEventType::NK_TOUCH_MOVE:
		case NkEventType::NK_TOUCH_END:
		case NkEventType::NK_TOUCH_CANCEL:
		case NkEventType::NK_GESTURE_PINCH:
		case NkEventType::NK_GESTURE_ROTATE:
		case NkEventType::NK_GESTURE_PAN:
		case NkEventType::NK_GESTURE_SWIPE:
		case NkEventType::NK_GESTURE_TAP:
		case NkEventType::NK_GESTURE_LONG_PRESS:
			return NkEventCategory::NK_CAT_TOUCH;

		case NkEventType::NK_GAMEPAD_CONNECT:
		case NkEventType::NK_GAMEPAD_DISCONNECT:
		case NkEventType::NK_GAMEPAD_BUTTON_PRESS:
		case NkEventType::NK_GAMEPAD_BUTTON_RELEASE:
		case NkEventType::NK_GAMEPAD_AXIS_MOVE:
		case NkEventType::NK_GAMEPAD_RUMBLE:
			return NkEventCategory::NK_CAT_GAMEPAD;

		case NkEventType::NK_DROP_ENTER:
		case NkEventType::NK_DROP_OVER:
		case NkEventType::NK_DROP_LEAVE:
		case NkEventType::NK_DROP_FILE:
		case NkEventType::NK_DROP_TEXT:
		case NkEventType::NK_DROP_IMAGE:
			return NkEventCategory::NK_CAT_DROP;

		case NkEventType::NK_SYSTEM_POWER_SUSPEND:
		case NkEventType::NK_SYSTEM_POWER_RESUME:
		case NkEventType::NK_SYSTEM_LOW_MEMORY:
		case NkEventType::NK_SYSTEM_APP_PAUSE:
		case NkEventType::NK_SYSTEM_APP_RESUME:
		case NkEventType::NK_SYSTEM_LOCALE_CHANGE:
		case NkEventType::NK_SYSTEM_DISPLAY_CHANGE:
			return NkEventCategory::NK_CAT_SYSTEM;

		case NkEventType::NK_CUSTOM:
			return NkEventCategory::NK_CAT_CUSTOM;

		default:
			return NkEventCategory::NK_CAT_NONE;
	}
}

// ===========================================================================
// NkEventTypeToString
// ===========================================================================

const char *NkEventTypeToString(NkEventType type) {
	switch (type) {
		case NkEventType::NK_NONE:
			return "NONE";
		// Fenêtre
		case NkEventType::NK_WINDOW_CREATE:
			return "WINDOW_CREATE";
		case NkEventType::NK_WINDOW_CLOSE:
			return "WINDOW_CLOSE";
		case NkEventType::NK_WINDOW_DESTROY:
			return "WINDOW_DESTROY";
		case NkEventType::NK_WINDOW_PAINT:
			return "WINDOW_PAINT";
		case NkEventType::NK_WINDOW_RESIZE:
			return "WINDOW_RESIZE";
		case NkEventType::NK_WINDOW_RESIZE_BEGIN:
			return "WINDOW_RESIZE_BEGIN";
		case NkEventType::NK_WINDOW_RESIZE_END:
			return "WINDOW_RESIZE_END";
		case NkEventType::NK_WINDOW_MOVE:
			return "WINDOW_MOVE";
		case NkEventType::NK_WINDOW_MOVE_BEGIN:
			return "WINDOW_MOVE_BEGIN";
		case NkEventType::NK_WINDOW_MOVE_END:
			return "WINDOW_MOVE_END";
		case NkEventType::NK_WINDOW_FOCUS_GAINED:
			return "WINDOW_FOCUS_GAINED";
		case NkEventType::NK_WINDOW_FOCUS_LOST:
			return "WINDOW_FOCUS_LOST";
		case NkEventType::NK_WINDOW_MINIMIZE:
			return "WINDOW_MINIMIZE";
		case NkEventType::NK_WINDOW_MAXIMIZE:
			return "WINDOW_MAXIMIZE";
		case NkEventType::NK_WINDOW_RESTORE:
			return "WINDOW_RESTORE";
		case NkEventType::NK_WINDOW_FULLSCREEN:
			return "WINDOW_FULLSCREEN";
		case NkEventType::NK_WINDOW_WINDOWED:
			return "WINDOW_WINDOWED";
		case NkEventType::NK_WINDOW_DPI_CHANGE:
			return "WINDOW_DPI_CHANGE";
		case NkEventType::NK_WINDOW_THEME_CHANGE:
			return "WINDOW_THEME_CHANGE";
		case NkEventType::NK_WINDOW_SHOWN:
			return "WINDOW_SHOWN";
		case NkEventType::NK_WINDOW_HIDDEN:
			return "WINDOW_HIDDEN";
		// Clavier
		case NkEventType::NK_KEY_PRESS:
			return "KEY_PRESS";
		case NkEventType::NK_KEY_REPEAT:
			return "KEY_REPEAT";
		case NkEventType::NK_KEY_RELEASE:
			return "KEY_RELEASE";
		case NkEventType::NK_TEXT_INPUT:
			return "TEXT_INPUT";
		// Souris
		case NkEventType::NK_MOUSE_MOVE:
			return "MOUSE_MOVE";
		case NkEventType::NK_MOUSE_RAW:
			return "MOUSE_RAW";
		case NkEventType::NK_MOUSE_BUTTON_PRESS:
			return "MOUSE_BUTTON_PRESS";
		case NkEventType::NK_MOUSE_BUTTON_RELEASE:
			return "MOUSE_BUTTON_RELEASE";
		case NkEventType::NK_MOUSE_DOUBLE_CLICK:
			return "MOUSE_DOUBLE_CLICK";
		case NkEventType::NK_MOUSE_WHEEL_VERTICAL:
			return "MOUSE_WHEEL_VERTICAL";
		case NkEventType::NK_MOUSE_WHEEL_HORIZONTAL:
			return "MOUSE_WHEEL_HORIZONTAL";
		case NkEventType::NK_MOUSE_ENTER:
			return "MOUSE_ENTER";
		case NkEventType::NK_MOUSE_LEAVE:
			return "MOUSE_LEAVE";
		case NkEventType::NK_MOUSE_CAPTURE_BEGIN:
			return "MOUSE_CAPTURE_BEGIN";
		case NkEventType::NK_MOUSE_CAPTURE_END:
			return "MOUSE_CAPTURE_END";
		// Tactile
		case NkEventType::NK_TOUCH_BEGIN:
			return "TOUCH_BEGIN";
		case NkEventType::NK_TOUCH_MOVE:
			return "TOUCH_MOVE";
		case NkEventType::NK_TOUCH_END:
			return "TOUCH_END";
		case NkEventType::NK_TOUCH_CANCEL:
			return "TOUCH_CANCEL";
		case NkEventType::NK_GESTURE_PINCH:
			return "GESTURE_PINCH";
		case NkEventType::NK_GESTURE_ROTATE:
			return "GESTURE_ROTATE";
		case NkEventType::NK_GESTURE_PAN:
			return "GESTURE_PAN";
		case NkEventType::NK_GESTURE_SWIPE:
			return "GESTURE_SWIPE";
		case NkEventType::NK_GESTURE_TAP:
			return "GESTURE_TAP";
		case NkEventType::NK_GESTURE_LONG_PRESS:
			return "GESTURE_LONG_PRESS";
		// Manette
		case NkEventType::NK_GAMEPAD_CONNECT:
			return "GAMEPAD_CONNECT";
		case NkEventType::NK_GAMEPAD_DISCONNECT:
			return "GAMEPAD_DISCONNECT";
		case NkEventType::NK_GAMEPAD_BUTTON_PRESS:
			return "GAMEPAD_BUTTON_PRESS";
		case NkEventType::NK_GAMEPAD_BUTTON_RELEASE:
			return "GAMEPAD_BUTTON_RELEASE";
		case NkEventType::NK_GAMEPAD_AXIS_MOVE:
			return "GAMEPAD_AXIS_MOVE";
		case NkEventType::NK_GAMEPAD_RUMBLE:
			return "GAMEPAD_RUMBLE";
		// Drop
		case NkEventType::NK_DROP_ENTER:
			return "DROP_ENTER";
		case NkEventType::NK_DROP_OVER:
			return "DROP_OVER";
		case NkEventType::NK_DROP_LEAVE:
			return "DROP_LEAVE";
		case NkEventType::NK_DROP_FILE:
			return "DROP_FILE";
		case NkEventType::NK_DROP_TEXT:
			return "DROP_TEXT";
		case NkEventType::NK_DROP_IMAGE:
			return "DROP_IMAGE";
		// Système
		case NkEventType::NK_SYSTEM_POWER_SUSPEND:
			return "SYSTEM_POWER_SUSPEND";
		case NkEventType::NK_SYSTEM_POWER_RESUME:
			return "SYSTEM_POWER_RESUME";
		case NkEventType::NK_SYSTEM_LOW_MEMORY:
			return "SYSTEM_LOW_MEMORY";
		case NkEventType::NK_SYSTEM_APP_PAUSE:
			return "SYSTEM_APP_PAUSE";
		case NkEventType::NK_SYSTEM_APP_RESUME:
			return "SYSTEM_APP_RESUME";
		case NkEventType::NK_SYSTEM_LOCALE_CHANGE:
			return "SYSTEM_LOCALE_CHANGE";
		case NkEventType::NK_SYSTEM_DISPLAY_CHANGE:
			return "SYSTEM_DISPLAY_CHANGE";
		case NkEventType::NK_CUSTOM:
			return "CUSTOM";
		default:
			return "UNKNOWN";
	}
}

// ===========================================================================
// NkKeyToString
// ===========================================================================

const char *NkKeyToString(NkKey key) {
	switch (key) {
		case NkKey::NK_UNKNOWN:
			return "UNKNOWN";
		// Fonction
		case NkKey::NK_ESCAPE:
			return "ESCAPE";
		case NkKey::NK_F1:
			return "F1";
		case NkKey::NK_F2:
			return "F2";
		case NkKey::NK_F3:
			return "F3";
		case NkKey::NK_F4:
			return "F4";
		case NkKey::NK_F5:
			return "F5";
		case NkKey::NK_F6:
			return "F6";
		case NkKey::NK_F7:
			return "F7";
		case NkKey::NK_F8:
			return "F8";
		case NkKey::NK_F9:
			return "F9";
		case NkKey::NK_F10:
			return "F10";
		case NkKey::NK_F11:
			return "F11";
		case NkKey::NK_F12:
			return "F12";
		case NkKey::NK_F13:
			return "F13";
		case NkKey::NK_F14:
			return "F14";
		case NkKey::NK_F15:
			return "F15";
		case NkKey::NK_F16:
			return "F16";
		case NkKey::NK_F17:
			return "F17";
		case NkKey::NK_F18:
			return "F18";
		case NkKey::NK_F19:
			return "F19";
		case NkKey::NK_F20:
			return "F20";
		case NkKey::NK_F21:
			return "F21";
		case NkKey::NK_F22:
			return "F22";
		case NkKey::NK_F23:
			return "F23";
		case NkKey::NK_F24:
			return "F24";
		// Ligne des chiffres
		case NkKey::NK_GRAVE:
			return "GRAVE";
		case NkKey::NK_NUM1:
			return "1";
		case NkKey::NK_NUM2:
			return "2";
		case NkKey::NK_NUM3:
			return "3";
		case NkKey::NK_NUM4:
			return "4";
		case NkKey::NK_NUM5:
			return "5";
		case NkKey::NK_NUM6:
			return "6";
		case NkKey::NK_NUM7:
			return "7";
		case NkKey::NK_NUM8:
			return "8";
		case NkKey::NK_NUM9:
			return "9";
		case NkKey::NK_NUM0:
			return "0";
		case NkKey::NK_MINUS:
			return "MINUS";
		case NkKey::NK_EQUALS:
			return "EQUALS";
		case NkKey::NK_BACK:
			return "BACKSPACE";
		// QWERTY
		case NkKey::NK_TAB:
			return "TAB";
		case NkKey::NK_Q:
			return "Q";
		case NkKey::NK_W:
			return "W";
		case NkKey::NK_E:
			return "E";
		case NkKey::NK_R:
			return "R";
		case NkKey::NK_T:
			return "T";
		case NkKey::NK_Y:
			return "Y";
		case NkKey::NK_U:
			return "U";
		case NkKey::NK_I:
			return "I";
		case NkKey::NK_O:
			return "O";
		case NkKey::NK_P:
			return "P";
		case NkKey::NK_LBRACKET:
			return "LBRACKET";
		case NkKey::NK_RBRACKET:
			return "RBRACKET";
		case NkKey::NK_BACKSLASH:
			return "BACKSLASH";
		// ASDF
		case NkKey::NK_CAPSLOCK:
			return "CAPSLOCK";
		case NkKey::NK_A:
			return "A";
		case NkKey::NK_S:
			return "S";
		case NkKey::NK_D:
			return "D";
		case NkKey::NK_F:
			return "F";
		case NkKey::NK_G:
			return "G";
		case NkKey::NK_H:
			return "H";
		case NkKey::NK_J:
			return "J";
		case NkKey::NK_K:
			return "K";
		case NkKey::NK_L:
			return "L";
		case NkKey::NK_SEMICOLON:
			return "SEMICOLON";
		case NkKey::NK_APOSTROPHE:
			return "APOSTROPHE";
		case NkKey::NK_ENTER:
			return "ENTER";
		// ZXCV
		case NkKey::NK_LSHIFT:
			return "LSHIFT";
		case NkKey::NK_Z:
			return "Z";
		case NkKey::NK_X:
			return "X";
		case NkKey::NK_C:
			return "C";
		case NkKey::NK_V:
			return "V";
		case NkKey::NK_B:
			return "B";
		case NkKey::NK_N:
			return "N";
		case NkKey::NK_M:
			return "M";
		case NkKey::NK_COMMA:
			return "COMMA";
		case NkKey::NK_PERIOD:
			return "PERIOD";
		case NkKey::NK_SLASH:
			return "SLASH";
		case NkKey::NK_RSHIFT:
			return "RSHIFT";
		// Rangée du bas
		case NkKey::NK_LCTRL:
			return "LCTRL";
		case NkKey::NK_LSUPER:
			return "LSUPER";
		case NkKey::NK_LALT:
			return "LALT";
		case NkKey::NK_SPACE:
			return "SPACE";
		case NkKey::NK_RALT:
			return "RALT";
		case NkKey::NK_RSUPER:
			return "RSUPER";
		case NkKey::NK_MENU:
			return "MENU";
		case NkKey::NK_RCTRL:
			return "RCTRL";
		// Navigation
		case NkKey::NK_PRINT_SCREEN:
			return "PRINT_SCREEN";
		case NkKey::NK_SCROLL_LOCK:
			return "SCROLL_LOCK";
		case NkKey::NK_PAUSE_BREAK:
			return "PAUSE_BREAK";
		case NkKey::NK_INSERT:
			return "INSERT";
		case NkKey::NK_DELETE:
			return "DELETE";
		case NkKey::NK_HOME:
			return "HOME";
		case NkKey::NK_END:
			return "END";
		case NkKey::NK_PAGE_UP:
			return "PAGE_UP";
		case NkKey::NK_PAGE_DOWN:
			return "PAGE_DOWN";
		// Flèches
		case NkKey::NK_UP:
			return "UP";
		case NkKey::NK_DOWN:
			return "DOWN";
		case NkKey::NK_LEFT:
			return "LEFT";
		case NkKey::NK_RIGHT:
			return "RIGHT";
		// Pavé numérique
		case NkKey::NK_NUM_LOCK:
			return "NUM_LOCK";
		case NkKey::NK_NUMPAD_DIV:
			return "NUMPAD_/";
		case NkKey::NK_NUMPAD_MUL:
			return "NUMPAD_*";
		case NkKey::NK_NUMPAD_SUB:
			return "NUMPAD_-";
		case NkKey::NK_NUMPAD_ADD:
			return "NUMPAD_+";
		case NkKey::NK_NUMPAD_ENTER:
			return "NUMPAD_ENTER";
		case NkKey::NK_NUMPAD_DOT:
			return "NUMPAD_.";
		case NkKey::NK_NUMPAD_0:
			return "NUMPAD_0";
		case NkKey::NK_NUMPAD_1:
			return "NUMPAD_1";
		case NkKey::NK_NUMPAD_2:
			return "NUMPAD_2";
		case NkKey::NK_NUMPAD_3:
			return "NUMPAD_3";
		case NkKey::NK_NUMPAD_4:
			return "NUMPAD_4";
		case NkKey::NK_NUMPAD_5:
			return "NUMPAD_5";
		case NkKey::NK_NUMPAD_6:
			return "NUMPAD_6";
		case NkKey::NK_NUMPAD_7:
			return "NUMPAD_7";
		case NkKey::NK_NUMPAD_8:
			return "NUMPAD_8";
		case NkKey::NK_NUMPAD_9:
			return "NUMPAD_9";
		case NkKey::NK_NUMPAD_EQUALS:
			return "NUMPAD_=";
		// Médias
		case NkKey::NK_MEDIA_PLAY_PAUSE:
			return "MEDIA_PLAY_PAUSE";
		case NkKey::NK_MEDIA_STOP:
			return "MEDIA_STOP";
		case NkKey::NK_MEDIA_NEXT:
			return "MEDIA_NEXT";
		case NkKey::NK_MEDIA_PREV:
			return "MEDIA_PREV";
		case NkKey::NK_MEDIA_VOLUME_UP:
			return "VOLUME_UP";
		case NkKey::NK_MEDIA_VOLUME_DOWN:
			return "VOLUME_DOWN";
		case NkKey::NK_MEDIA_MUTE:
			return "MUTE";
		// Navigateur
		case NkKey::NK_BROWSER_BACK:
			return "BROWSER_BACK";
		case NkKey::NK_BROWSER_FORWARD:
			return "BROWSER_FORWARD";
		case NkKey::NK_BROWSER_REFRESH:
			return "BROWSER_REFRESH";
		case NkKey::NK_BROWSER_HOME:
			return "BROWSER_HOME";
		case NkKey::NK_BROWSER_SEARCH:
			return "BROWSER_SEARCH";
		case NkKey::NK_BROWSER_FAVORITES:
			return "BROWSER_FAVORITES";
		// IME
		case NkKey::NK_KANA:
			return "KANA";
		case NkKey::NK_KANJI:
			return "KANJI";
		case NkKey::NK_CONVERT:
			return "CONVERT";
		case NkKey::NK_NONCONVERT:
			return "NONCONVERT";
		case NkKey::NK_HANGUL:
			return "HANGUL";
		case NkKey::NK_HANJA:
			return "HANJA";
		// Misc
		case NkKey::NK_SLEEP:
			return "SLEEP";
		case NkKey::NK_CLEAR:
			return "CLEAR";
		case NkKey::NK_SEPARATOR:
			return "SEPARATOR";
		default:
			return "OEM";
	}
}

// ===========================================================================
// NkKeyIsXxx
// ===========================================================================

bool NkKeyIsModifier(NkKey key) {
	switch (key) {
		case NkKey::NK_LSHIFT:
		case NkKey::NK_RSHIFT:
		case NkKey::NK_LCTRL:
		case NkKey::NK_RCTRL:
		case NkKey::NK_LALT:
		case NkKey::NK_RALT:
		case NkKey::NK_LSUPER:
		case NkKey::NK_RSUPER:
		case NkKey::NK_CAPSLOCK:
		case NkKey::NK_NUM_LOCK:
		case NkKey::NK_SCROLL_LOCK:
			return true;
		default:
			return false;
	}
}

bool NkKeyIsNumpad(NkKey key) {
	return key >= NkKey::NK_NUM_LOCK && key <= NkKey::NK_NUMPAD_EQUALS;
}

bool NkKeyIsFunctionKey(NkKey key) {
	return key >= NkKey::NK_F1 && key <= NkKey::NK_F24;
}

// ===========================================================================
// NkModifierState::ToString
// ===========================================================================

std::string NkModifierState::ToString() const {
	std::string s;
	if (ctrl)
		s += "Ctrl+";
	if (alt)
		s += "Alt+";
	if (altGr)
		s += "AltGr+";
	if (shift)
		s += "Shift+";
	if (super)
		s += "Super+";
	if (!s.empty())
		s.pop_back(); // enlève le dernier '+'
	return s.empty() ? "None" : s;
}

} // namespace nkentseu
