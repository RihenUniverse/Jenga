// =============================================================================
// NkEventSystem.cpp
// Implémentation de EventSystem.
// =============================================================================

#include "NkEventSystem.h"

namespace nkentseu
{

// ---------------------------------------------------------------------------
// Singleton
// ---------------------------------------------------------------------------

EventSystem& EventSystem::Instance()
{
    static EventSystem sInstance;
    return sInstance;
}

// ---------------------------------------------------------------------------
// AttachImpl / DetachImpl
// ---------------------------------------------------------------------------

void EventSystem::AttachImpl(IEventImpl* impl)
{
    if (impl && std::find(mImpls.begin(), mImpls.end(), impl) == mImpls.end())
        mImpls.push_back(impl);
}

void EventSystem::DetachImpl(IEventImpl* impl)
{
    mImpls.erase(std::remove(mImpls.begin(), mImpls.end(), impl), mImpls.end());
}

// ---------------------------------------------------------------------------
// PollEvents
// ---------------------------------------------------------------------------

void EventSystem::PollEvents()
{
    // 1. Pomper les messages OS depuis chaque impl
    for (auto* impl : mImpls)
        impl->PollEvents();

    // 2. Vider le buffer de lecture de la trame précédente
    mEventBuffer.clear();
    mReadHead = 0;

    // 3. Collecter tous les événements en attente
    for (auto* impl : mImpls)
    {
        while (!impl->IsEmpty())
        {
            NkEvent ev = impl->Front();
            impl->Pop();

            // Callbacks immédiat
            if (mGlobalCallback)
                mGlobalCallback(&ev);

            FireTypedCallback(&ev);

            // Mise en buffer FIFO pour PollEvent()
            mEventBuffer.push_back(std::move(ev));
        }
    }
}

// ---------------------------------------------------------------------------
// PollEvent
// ---------------------------------------------------------------------------

NkEvent* EventSystem::PollEvent()
{
    if (mReadHead >= mEventBuffer.size())
        return nullptr;
    return &mEventBuffer[mReadHead++];
}

// ---------------------------------------------------------------------------
// Callbacks
// ---------------------------------------------------------------------------

void EventSystem::SetGlobalEventCallback(NkGlobalEventCallback callback)
{
    mGlobalCallback = std::move(callback);
}

void EventSystem::DispatchEvent(NkEvent& event)
{
    if (mGlobalCallback)
        mGlobalCallback(&event);
    FireTypedCallback(&event);
}

void EventSystem::FireTypedCallback(NkEvent* ev)
{
    auto tryFire = [&](std::type_index idx)
    {
        auto it = mTypedCallbacks.find(idx);
        if (it != mTypedCallbacks.end())
            it->second(ev);
    };

    switch (ev->type)
    {
    // Fenêtre
    case NkEventType::NK_WINDOW_CREATE:
        tryFire(std::type_index(typeid(NkWindowCreateEvent))); break;
    case NkEventType::NK_WINDOW_CLOSE:
        tryFire(std::type_index(typeid(NkWindowCloseEvent))); break;
    case NkEventType::NK_WINDOW_DESTROY:
        tryFire(std::type_index(typeid(NkWindowDestroyEvent))); break;
    case NkEventType::NK_WINDOW_PAINT:
        tryFire(std::type_index(typeid(NkWindowPaintEvent))); break;
    case NkEventType::NK_WINDOW_RESIZE:
        tryFire(std::type_index(typeid(NkWindowResizeEvent))); break;
    case NkEventType::NK_WINDOW_RESIZE_BEGIN:
        tryFire(std::type_index(typeid(NkWindowResizeBeginEvent))); break;
    case NkEventType::NK_WINDOW_RESIZE_END:
        tryFire(std::type_index(typeid(NkWindowResizeEndEvent))); break;
    case NkEventType::NK_WINDOW_MOVE:
        tryFire(std::type_index(typeid(NkWindowMoveEvent))); break;
    case NkEventType::NK_WINDOW_MOVE_BEGIN:
        tryFire(std::type_index(typeid(NkWindowMoveBeginEvent))); break;
    case NkEventType::NK_WINDOW_MOVE_END:
        tryFire(std::type_index(typeid(NkWindowMoveEndEvent))); break;
    case NkEventType::NK_WINDOW_FOCUS_GAINED:
        tryFire(std::type_index(typeid(NkWindowFocusGainedEvent))); break;
    case NkEventType::NK_WINDOW_FOCUS_LOST:
        tryFire(std::type_index(typeid(NkWindowFocusLostEvent))); break;
    case NkEventType::NK_WINDOW_MINIMIZE:
        tryFire(std::type_index(typeid(NkWindowMinimizeEvent))); break;
    case NkEventType::NK_WINDOW_MAXIMIZE:
        tryFire(std::type_index(typeid(NkWindowMaximizeEvent))); break;
    case NkEventType::NK_WINDOW_RESTORE:
        tryFire(std::type_index(typeid(NkWindowRestoreEvent))); break;
    case NkEventType::NK_WINDOW_FULLSCREEN:
        tryFire(std::type_index(typeid(NkWindowFullscreenEvent))); break;
    case NkEventType::NK_WINDOW_WINDOWED:
        tryFire(std::type_index(typeid(NkWindowWindowedEvent))); break;
    case NkEventType::NK_WINDOW_DPI_CHANGE:
        tryFire(std::type_index(typeid(NkWindowDpiEvent))); break;
    case NkEventType::NK_WINDOW_THEME_CHANGE:
        tryFire(std::type_index(typeid(NkWindowThemeEvent))); break;
    case NkEventType::NK_WINDOW_SHOWN:
        tryFire(std::type_index(typeid(NkWindowShownEvent))); break;
    case NkEventType::NK_WINDOW_HIDDEN:
        tryFire(std::type_index(typeid(NkWindowHiddenEvent))); break;

    // Clavier
    case NkEventType::NK_KEY_PRESS:
        tryFire(std::type_index(typeid(NkKeyPressEvent))); break;
    case NkEventType::NK_KEY_REPEAT:
        tryFire(std::type_index(typeid(NkKeyRepeatEvent))); break;
    case NkEventType::NK_KEY_RELEASE:
        tryFire(std::type_index(typeid(NkKeyReleaseEvent))); break;
    case NkEventType::NK_TEXT_INPUT:
        tryFire(std::type_index(typeid(NkTextInputEvent))); break;

    // Souris
    case NkEventType::NK_MOUSE_MOVE:
        tryFire(std::type_index(typeid(NkMouseMoveEvent))); break;
    case NkEventType::NK_MOUSE_RAW:
        tryFire(std::type_index(typeid(NkMouseRawEvent))); break;
    case NkEventType::NK_MOUSE_BUTTON_PRESS:
        tryFire(std::type_index(typeid(NkMouseButtonPressEvent))); break;
    case NkEventType::NK_MOUSE_BUTTON_RELEASE:
        tryFire(std::type_index(typeid(NkMouseButtonReleaseEvent))); break;
    case NkEventType::NK_MOUSE_DOUBLE_CLICK:
        tryFire(std::type_index(typeid(NkMouseDoubleClickEvent))); break;
    case NkEventType::NK_MOUSE_WHEEL_VERTICAL:
        tryFire(std::type_index(typeid(NkMouseWheelVerticalEvent))); break;
    case NkEventType::NK_MOUSE_WHEEL_HORIZONTAL:
        tryFire(std::type_index(typeid(NkMouseWheelHorizontalEvent))); break;
    case NkEventType::NK_MOUSE_ENTER:
        tryFire(std::type_index(typeid(NkMouseEnterEvent))); break;
    case NkEventType::NK_MOUSE_LEAVE:
        tryFire(std::type_index(typeid(NkMouseLeaveEvent))); break;
    case NkEventType::NK_MOUSE_CAPTURE_BEGIN:
        tryFire(std::type_index(typeid(NkMouseCaptureBeginEvent))); break;
    case NkEventType::NK_MOUSE_CAPTURE_END:
        tryFire(std::type_index(typeid(NkMouseCaptureEndEvent))); break;

    // Tactile
    case NkEventType::NK_TOUCH_BEGIN:
        tryFire(std::type_index(typeid(NkTouchBeginEvent))); break;
    case NkEventType::NK_TOUCH_MOVE:
        tryFire(std::type_index(typeid(NkTouchMoveEvent))); break;
    case NkEventType::NK_TOUCH_END:
        tryFire(std::type_index(typeid(NkTouchEndEvent))); break;
    case NkEventType::NK_TOUCH_CANCEL:
        tryFire(std::type_index(typeid(NkTouchCancelEvent))); break;
    case NkEventType::NK_GESTURE_PINCH:
        tryFire(std::type_index(typeid(NkGesturePinchEvent))); break;
    case NkEventType::NK_GESTURE_ROTATE:
        tryFire(std::type_index(typeid(NkGestureRotateEvent))); break;
    case NkEventType::NK_GESTURE_PAN:
        tryFire(std::type_index(typeid(NkGesturePanEvent))); break;
    case NkEventType::NK_GESTURE_SWIPE:
        tryFire(std::type_index(typeid(NkGestureSwipeEvent))); break;
    case NkEventType::NK_GESTURE_TAP:
        tryFire(std::type_index(typeid(NkGestureTapEvent))); break;
    case NkEventType::NK_GESTURE_LONG_PRESS:
        tryFire(std::type_index(typeid(NkGestureLongPressEvent))); break;

    // Manette
    case NkEventType::NK_GAMEPAD_CONNECT:
        tryFire(std::type_index(typeid(NkGamepadConnectEvent))); break;
    case NkEventType::NK_GAMEPAD_DISCONNECT:
        tryFire(std::type_index(typeid(NkGamepadDisconnectEvent))); break;
    case NkEventType::NK_GAMEPAD_BUTTON_PRESS:
        tryFire(std::type_index(typeid(NkGamepadButtonPressEvent))); break;
    case NkEventType::NK_GAMEPAD_BUTTON_RELEASE:
        tryFire(std::type_index(typeid(NkGamepadButtonReleaseEvent))); break;
    case NkEventType::NK_GAMEPAD_AXIS_MOVE:
        tryFire(std::type_index(typeid(NkGamepadAxisEvent))); break;
    case NkEventType::NK_GAMEPAD_RUMBLE:
        tryFire(std::type_index(typeid(NkGamepadRumbleEvent))); break;

    // Drag & Drop
    case NkEventType::NK_DROP_ENTER:
        tryFire(std::type_index(typeid(NkDropEnterEvent))); break;
    case NkEventType::NK_DROP_OVER:
        tryFire(std::type_index(typeid(NkDropOverEvent))); break;
    case NkEventType::NK_DROP_LEAVE:
        tryFire(std::type_index(typeid(NkDropLeaveEvent))); break;
    case NkEventType::NK_DROP_FILE:
        tryFire(std::type_index(typeid(NkDropFileEvent))); break;
    case NkEventType::NK_DROP_TEXT:
        tryFire(std::type_index(typeid(NkDropTextEvent))); break;
    case NkEventType::NK_DROP_IMAGE:
        tryFire(std::type_index(typeid(NkDropImageEvent))); break;

    // Système
    case NkEventType::NK_SYSTEM_POWER_SUSPEND:
        tryFire(std::type_index(typeid(NkSystemPowerSuspendEvent))); break;
    case NkEventType::NK_SYSTEM_POWER_RESUME:
        tryFire(std::type_index(typeid(NkSystemPowerResumeEvent))); break;
    case NkEventType::NK_SYSTEM_LOW_MEMORY:
        tryFire(std::type_index(typeid(NkSystemLowMemoryEvent))); break;
    case NkEventType::NK_SYSTEM_APP_PAUSE:
        tryFire(std::type_index(typeid(NkSystemAppPauseEvent))); break;
    case NkEventType::NK_SYSTEM_APP_RESUME:
        tryFire(std::type_index(typeid(NkSystemAppResumeEvent))); break;
    case NkEventType::NK_SYSTEM_LOCALE_CHANGE:
        tryFire(std::type_index(typeid(NkSystemLocaleChangeEvent))); break;
    case NkEventType::NK_SYSTEM_DISPLAY_CHANGE:
        tryFire(std::type_index(typeid(NkSystemDisplayEvent))); break;

    // Personnalisé
    case NkEventType::NK_CUSTOM:
        tryFire(std::type_index(typeid(NkCustomEvent))); break;

    default:
        // Événements non gérés (si certains n'ont pas de classe)
        break;
    }
}

} // namespace nkentseu
