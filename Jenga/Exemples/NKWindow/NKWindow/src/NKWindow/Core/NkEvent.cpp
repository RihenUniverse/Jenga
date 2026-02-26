// =============================================================================
// NkEvent.cpp
// Implémentation de NkEvent::ToString().
// =============================================================================

#include "NkEvent.h"

/**
 * @brief Namespace nkentseu.
 */
namespace nkentseu {

std::string NkEvent::ToString() const {
	std::string prefix = "[";
	prefix += NkEventTypeToString(type);
	prefix += "@" + std::to_string(timestamp) + "ms] ";

	switch (type) {
		// Fenêtre
		case NkEventType::NK_WINDOW_CREATE:
			return prefix + data.windowCreate.ToString();
		case NkEventType::NK_WINDOW_CLOSE:
			return prefix + data.windowClose.ToString();
		case NkEventType::NK_WINDOW_DESTROY:
			return prefix + data.windowDestroy.ToString();
		case NkEventType::NK_WINDOW_PAINT:
			return prefix + data.windowPaint.ToString();
		case NkEventType::NK_WINDOW_RESIZE:
		case NkEventType::NK_WINDOW_RESIZE_BEGIN:
		case NkEventType::NK_WINDOW_RESIZE_END:
			return prefix + data.windowResize.ToString();
		case NkEventType::NK_WINDOW_MOVE:
		case NkEventType::NK_WINDOW_MOVE_BEGIN:
		case NkEventType::NK_WINDOW_MOVE_END:
			return prefix + data.windowMove.ToString();
		case NkEventType::NK_WINDOW_FOCUS_GAINED:
		case NkEventType::NK_WINDOW_FOCUS_LOST:
			return prefix + data.windowFocus.ToString();
		case NkEventType::NK_WINDOW_DPI_CHANGE:
			return prefix + data.windowDpi.ToString();
		case NkEventType::NK_WINDOW_THEME_CHANGE:
			return prefix + data.windowTheme.ToString();
		case NkEventType::NK_WINDOW_MINIMIZE:
		case NkEventType::NK_WINDOW_MAXIMIZE:
		case NkEventType::NK_WINDOW_RESTORE:
		case NkEventType::NK_WINDOW_FULLSCREEN:
		case NkEventType::NK_WINDOW_WINDOWED:
			return prefix + data.windowState.ToString();
		case NkEventType::NK_WINDOW_SHOWN:
		case NkEventType::NK_WINDOW_HIDDEN:
			return prefix + data.windowVisibility.ToString();
		// Clavier
		case NkEventType::NK_KEY_PRESS:
		case NkEventType::NK_KEY_REPEAT:
		case NkEventType::NK_KEY_RELEASE:
			return prefix + data.key.ToString();
		case NkEventType::NK_TEXT_INPUT:
			return prefix + data.textInput.ToString();
		// Souris
		case NkEventType::NK_MOUSE_MOVE:
			return prefix + data.mouseMove.ToString();
		case NkEventType::NK_MOUSE_RAW:
			return prefix + data.mouseRaw.ToString();
		case NkEventType::NK_MOUSE_BUTTON_PRESS:
		case NkEventType::NK_MOUSE_BUTTON_RELEASE:
		case NkEventType::NK_MOUSE_DOUBLE_CLICK:
			return prefix + data.mouseButton.ToString();
		case NkEventType::NK_MOUSE_WHEEL_VERTICAL:
		case NkEventType::NK_MOUSE_WHEEL_HORIZONTAL:
			return prefix + data.mouseWheel.ToString();
		case NkEventType::NK_MOUSE_ENTER:
		case NkEventType::NK_MOUSE_LEAVE:
			return prefix + data.mouseCross.ToString();
		case NkEventType::NK_MOUSE_CAPTURE_BEGIN:
		case NkEventType::NK_MOUSE_CAPTURE_END:
			return prefix + data.mouseCapture.ToString();
		// Tactile
		case NkEventType::NK_TOUCH_BEGIN:
		case NkEventType::NK_TOUCH_MOVE:
		case NkEventType::NK_TOUCH_END:
		case NkEventType::NK_TOUCH_CANCEL:
			return prefix + data.touch.ToString();
		case NkEventType::NK_GESTURE_PINCH:
			return prefix + data.gesturePinch.ToString();
		case NkEventType::NK_GESTURE_ROTATE:
			return prefix + data.gestureRotate.ToString();
		case NkEventType::NK_GESTURE_PAN:
			return prefix + data.gesturePan.ToString();
		case NkEventType::NK_GESTURE_SWIPE:
			return prefix + data.gestureSwipe.ToString();
		case NkEventType::NK_GESTURE_TAP:
			return prefix + data.gestureTap.ToString();
		case NkEventType::NK_GESTURE_LONG_PRESS:
			return prefix + data.gestureLongPress.ToString();
		// Manette
		case NkEventType::NK_GAMEPAD_CONNECT:
		case NkEventType::NK_GAMEPAD_DISCONNECT:
			return prefix + data.gamepadConnect.ToString();
		case NkEventType::NK_GAMEPAD_BUTTON_PRESS:
		case NkEventType::NK_GAMEPAD_BUTTON_RELEASE:
			return prefix + data.gamepadButton.ToString();
		case NkEventType::NK_GAMEPAD_AXIS_MOVE:
			return prefix + data.gamepadAxis.ToString();
		case NkEventType::NK_GAMEPAD_RUMBLE:
			return prefix + data.gamepadRumble.ToString();
		// Drop
		case NkEventType::NK_DROP_ENTER:
			return prefix + data.dropEnter.ToString();
		case NkEventType::NK_DROP_OVER:
			return prefix + data.dropOver.ToString();
		case NkEventType::NK_DROP_LEAVE:
			return prefix + data.dropLeave.ToString();
		case NkEventType::NK_DROP_FILE:
			return prefix + (dropFile ? dropFile->ToString() : "DropFile(null)");
		case NkEventType::NK_DROP_TEXT:
			return prefix + (dropText ? dropText->ToString() : "DropText(null)");
		case NkEventType::NK_DROP_IMAGE:
			return prefix + (dropImage ? dropImage->ToString() : "DropImage(null)");
		// Système
		case NkEventType::NK_SYSTEM_POWER_SUSPEND:
		case NkEventType::NK_SYSTEM_POWER_RESUME:
			return prefix + data.systemPower.ToString();
		case NkEventType::NK_SYSTEM_LOW_MEMORY:
			return prefix + data.systemMemory.ToString();
		case NkEventType::NK_SYSTEM_APP_PAUSE:
			return prefix + "SystemAppPause";
		case NkEventType::NK_SYSTEM_APP_RESUME:
			return prefix + "SystemAppResume";
		case NkEventType::NK_SYSTEM_LOCALE_CHANGE:
			return prefix + data.systemLocale.ToString();
		case NkEventType::NK_SYSTEM_DISPLAY_CHANGE:
			return prefix + data.systemDisplay.ToString();
		// Personnalisé
		case NkEventType::NK_CUSTOM:
			return prefix + data.custom.ToString();
		default:
			return prefix + "UnknownEvent(" + std::to_string(static_cast<NkU32>(type)) + ")";
	}
}

} // namespace nkentseu
