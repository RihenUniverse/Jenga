#pragma once

// =============================================================================
// NkEvent.h
// Classe centrale NkEvent et union NkEventData.
//
// Ce fichier inclut tous les fichiers de données thématiques et assemble
// la structure finale.
//
// Architecture :
//   NkEventData  : union de tous les structs de données (allocation zéro)
//   NkEvent      : classe publique avec type, catégorie, timestamp, window, data
//
// Utilisation :
//   NkEvent ev(NkMouseButtonData(NkMouseButton::NK_MB_LEFT,
//               NkButtonState::NK_PRESSED, 100, 200));
//   ev.Is<NkMouseButtonData>();        → true
//   auto* d = ev.GetData<NkMouseButtonData>(); → données typées
//   auto* typed = ev.As<NkMouseButtonPressEvent>(); → sous-type pour callbacks
// =============================================================================

#include "Events/NkEventTypes.h"
#include "Events/NkWindowEvents.h"
#include "Events/NkKeyboardEvents.h"
#include "Events/NkMouseEvents.h"
#include "Events/NkTouchEvents.h"
#include "Events/NkGamepadEvents.h"
#include "Events/NkDropEvents.h"

#include <cstring>
#include <string>
#include <chrono>
#include <memory>
#include <utility>

namespace nkentseu
{

class Window; // forward

// ===========================================================================
// NkTimestampMs
// ===========================================================================

using NkTimestampMs = NkU64; ///< Millisecondes depuis l'initialisation du système

// ===========================================================================
// NkEventData — union de toutes les données d'événements
// ===========================================================================

union NkEventData
{
    // --- Fenêtre ---
    NkWindowCreateData      windowCreate;
    NkWindowCloseData       windowClose;
    NkWindowDestroyData     windowDestroy;
    NkWindowPaintData       windowPaint;
    NkWindowResizeData      windowResize;
    NkWindowMoveData        windowMove;
    NkWindowFocusData       windowFocus;
    NkWindowDpiData         windowDpi;
    NkWindowThemeData       windowTheme;
    NkWindowStateData       windowState;
    NkWindowVisibilityData  windowVisibility;

    // --- Clavier ---
    NkKeyData               key;
    NkTextInputData         textInput;

    // --- Souris ---
    NkMouseMoveData         mouseMove;
    NkMouseRawData          mouseRaw;
    NkMouseButtonData       mouseButton;
    NkMouseWheelData        mouseWheel;
    NkMouseCrossData        mouseCross;
    NkMouseCaptureData      mouseCapture;

    // --- Tactile ---
    NkTouchData             touch;
    NkGesturePinchData      gesturePinch;
    NkGestureRotateData     gestureRotate;
    NkGesturePanData        gesturePan;
    NkGestureSwipeData      gestureSwipe;
    NkGestureTapData        gestureTap;
    NkGestureLongPressData  gestureLongPress;

    // --- Manette ---
    NkGamepadConnectData    gamepadConnect;
    NkGamepadButtonData     gamepadButton;
    NkGamepadAxisData       gamepadAxis;
    NkGamepadRumbleData     gamepadRumble;

    // --- Drop (données sans allocation dynamique dans l'union) ---
    NkDropEnterData         dropEnter;
    NkDropOverData          dropOver;
    NkDropLeaveData         dropLeave;

    // --- Système ---
    NkSystemPowerData       systemPower;
    NkSystemLocaleData      systemLocale;
    NkSystemDisplayData     systemDisplay;
    NkSystemMemoryData      systemMemory;

    // --- Personnalisé ---
    NkCustomData            custom;

    NkEventData()  { std::memset(static_cast<void*>(this), 0, sizeof(*this)); }
    ~NkEventData() {}
};

// ===========================================================================
// NkEvent — classe principale
// ===========================================================================

class NkEvent
{
public:
    NkEventType     type      = NkEventType::NK_NONE;
    NkEventCategory category  = NkEventCategory::NK_CAT_NONE;
    Window*         window    = nullptr;
    NkTimestampMs   timestamp = 0;
    bool            handled   = false;
    NkEventData     data;

    // Données auxiliaires pour les types à allocation dynamique
    NkDropFileData*   dropFile  = nullptr;
    NkDropTextData*   dropText  = nullptr;
    NkDropImageData*  dropImage = nullptr;

    // --- Constructeur de base ---
    NkEvent() = default;

    NkEvent(const NkEvent& other)
    {
        CopyFrom(other);
    }

    NkEvent& operator=(const NkEvent& other)
    {
        if (this != &other)
            CopyFrom(other);
        return *this;
    }

    NkEvent(NkEvent&& other) noexcept
    {
        MoveFrom(std::move(other));
    }

    NkEvent& operator=(NkEvent&& other) noexcept
    {
        if (this != &other)
            MoveFrom(std::move(other));
        return *this;
    }

    ~NkEvent() = default;

    explicit NkEvent(NkEventType t, Window* w = nullptr)
        : type(t), category(NkGetEventCategory(t)), window(w)
        , timestamp(CurrentTimestamp()) {}

    // --- Constructeurs fenêtre ---
    explicit NkEvent(const NkWindowCreateData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_WINDOW), window(w), timestamp(CurrentTimestamp())
    { data.windowCreate = d; }

    explicit NkEvent(const NkWindowCloseData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_WINDOW), window(w), timestamp(CurrentTimestamp())
    { data.windowClose = d; }

    explicit NkEvent(const NkWindowDestroyData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_WINDOW), window(w), timestamp(CurrentTimestamp())
    { data.windowDestroy = d; }

    explicit NkEvent(const NkWindowPaintData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_WINDOW), window(w), timestamp(CurrentTimestamp())
    { data.windowPaint = d; }

    explicit NkEvent(const NkWindowResizeData& d, NkEventType t = NkEventType::NK_WINDOW_RESIZE, Window* w = nullptr)
        : type(t), category(NkEventCategory::NK_CAT_WINDOW), window(w), timestamp(CurrentTimestamp())
    { data.windowResize = d; }

    explicit NkEvent(const NkWindowMoveData& d, NkEventType t = NkEventType::NK_WINDOW_MOVE, Window* w = nullptr)
        : type(t), category(NkEventCategory::NK_CAT_WINDOW), window(w), timestamp(CurrentTimestamp())
    { data.windowMove = d; }

    explicit NkEvent(const NkWindowFocusData& d, Window* w = nullptr)
        : type(d.focused ? NkEventType::NK_WINDOW_FOCUS_GAINED : NkEventType::NK_WINDOW_FOCUS_LOST)
        , category(NkEventCategory::NK_CAT_WINDOW), window(w), timestamp(CurrentTimestamp())
    { data.windowFocus = d; }

    explicit NkEvent(const NkWindowDpiData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_WINDOW), window(w), timestamp(CurrentTimestamp())
    { data.windowDpi = d; }

    explicit NkEvent(const NkWindowThemeData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_WINDOW), window(w), timestamp(CurrentTimestamp())
    { data.windowTheme = d; }

    explicit NkEvent(const NkWindowStateData& d, Window* w = nullptr)
        : type(StateToType(d.state)), category(NkEventCategory::NK_CAT_WINDOW), window(w), timestamp(CurrentTimestamp())
    { data.windowState = d; }

    explicit NkEvent(const NkWindowVisibilityData& d, Window* w = nullptr)
        : type(d.visible ? NkEventType::NK_WINDOW_SHOWN : NkEventType::NK_WINDOW_HIDDEN)
        , category(NkEventCategory::NK_CAT_WINDOW), window(w), timestamp(CurrentTimestamp())
    { data.windowVisibility = d; }

    // --- Constructeurs clavier ---
    explicit NkEvent(const NkKeyData& d, Window* w = nullptr)
        : type(d.repeat ? NkEventType::NK_KEY_REPEAT
               : (d.state == NkButtonState::NK_PRESSED ? NkEventType::NK_KEY_PRESS
                                                        : NkEventType::NK_KEY_RELEASE))
        , category(NkEventCategory::NK_CAT_KEYBOARD), window(w), timestamp(CurrentTimestamp())
    { data.key = d; }

    explicit NkEvent(NkEventType t, const NkKeyData& d, Window* w = nullptr)
        : type(t), category(NkEventCategory::NK_CAT_KEYBOARD), window(w), timestamp(CurrentTimestamp())
    { data.key = d; }

    explicit NkEvent(const NkTextInputData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_KEYBOARD), window(w), timestamp(CurrentTimestamp())
    { data.textInput = d; }

    // --- Constructeurs souris ---
    explicit NkEvent(const NkMouseMoveData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_MOUSE), window(w), timestamp(CurrentTimestamp())
    { data.mouseMove = d; }

    explicit NkEvent(const NkMouseRawData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_MOUSE), window(w), timestamp(CurrentTimestamp())
    { data.mouseRaw = d; }

    explicit NkEvent(const NkMouseButtonData& d, Window* w = nullptr)
        : type(d.state == NkButtonState::NK_PRESSED
               ? (d.clickCount >= 2 ? NkEventType::NK_MOUSE_DOUBLE_CLICK : NkEventType::NK_MOUSE_BUTTON_PRESS)
               : NkEventType::NK_MOUSE_BUTTON_RELEASE)
        , category(NkEventCategory::NK_CAT_MOUSE), window(w), timestamp(CurrentTimestamp())
    { data.mouseButton = d; }

    explicit NkEvent(NkEventType t, const NkMouseButtonData& d, Window* w = nullptr)
        : type(t), category(NkEventCategory::NK_CAT_MOUSE), window(w), timestamp(CurrentTimestamp())
    { data.mouseButton = d; }

    explicit NkEvent(const NkMouseWheelData& d, Window* w = nullptr)
        : type(d.deltaX != 0.0 ? NkEventType::NK_MOUSE_WHEEL_HORIZONTAL
                                : NkEventType::NK_MOUSE_WHEEL_VERTICAL)
        , category(NkEventCategory::NK_CAT_MOUSE), window(w), timestamp(CurrentTimestamp())
    { data.mouseWheel = d; }

    explicit NkEvent(NkEventType t, const NkMouseWheelData& d, Window* w = nullptr)
        : type(t), category(NkEventCategory::NK_CAT_MOUSE), window(w), timestamp(CurrentTimestamp())
    { data.mouseWheel = d; }

    explicit NkEvent(const NkMouseCrossData& d, Window* w = nullptr)
        : type(d.entered ? NkEventType::NK_MOUSE_ENTER : NkEventType::NK_MOUSE_LEAVE)
        , category(NkEventCategory::NK_CAT_MOUSE), window(w), timestamp(CurrentTimestamp())
    { data.mouseCross = d; }

    explicit NkEvent(const NkMouseCaptureData& d, Window* w = nullptr)
        : type(d.captured ? NkEventType::NK_MOUSE_CAPTURE_BEGIN : NkEventType::NK_MOUSE_CAPTURE_END)
        , category(NkEventCategory::NK_CAT_MOUSE), window(w), timestamp(CurrentTimestamp())
    { data.mouseCapture = d; }

    // --- Constructeurs tactile ---
    explicit NkEvent(const NkTouchData& d, NkEventType t, Window* w = nullptr)
        : type(t), category(NkEventCategory::NK_CAT_TOUCH), window(w), timestamp(CurrentTimestamp())
    { data.touch = d; }

    explicit NkEvent(const NkGesturePinchData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_TOUCH), window(w), timestamp(CurrentTimestamp())
    { data.gesturePinch = d; }

    explicit NkEvent(const NkGestureRotateData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_TOUCH), window(w), timestamp(CurrentTimestamp())
    { data.gestureRotate = d; }

    explicit NkEvent(const NkGesturePanData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_TOUCH), window(w), timestamp(CurrentTimestamp())
    { data.gesturePan = d; }

    explicit NkEvent(const NkGestureSwipeData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_TOUCH), window(w), timestamp(CurrentTimestamp())
    { data.gestureSwipe = d; }

    explicit NkEvent(const NkGestureTapData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_TOUCH), window(w), timestamp(CurrentTimestamp())
    { data.gestureTap = d; }

    explicit NkEvent(const NkGestureLongPressData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_TOUCH), window(w), timestamp(CurrentTimestamp())
    { data.gestureLongPress = d; }

    // --- Constructeurs manette ---
    explicit NkEvent(const NkGamepadConnectData& d, Window* w = nullptr)
        : type(d.connected ? NkEventType::NK_GAMEPAD_CONNECT : NkEventType::NK_GAMEPAD_DISCONNECT)
        , category(NkEventCategory::NK_CAT_GAMEPAD), window(w), timestamp(CurrentTimestamp())
    { data.gamepadConnect = d; }

    explicit NkEvent(const NkGamepadButtonData& d, Window* w = nullptr)
        : type(d.state == NkButtonState::NK_PRESSED
               ? NkEventType::NK_GAMEPAD_BUTTON_PRESS
               : NkEventType::NK_GAMEPAD_BUTTON_RELEASE)
        , category(NkEventCategory::NK_CAT_GAMEPAD), window(w), timestamp(CurrentTimestamp())
    { data.gamepadButton = d; }

    explicit NkEvent(const NkGamepadAxisData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_GAMEPAD), window(w), timestamp(CurrentTimestamp())
    { data.gamepadAxis = d; }

    explicit NkEvent(const NkGamepadRumbleData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_GAMEPAD), window(w), timestamp(CurrentTimestamp())
    { data.gamepadRumble = d; }

    // --- Drop ---
    explicit NkEvent(const NkDropEnterData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_DROP), window(w), timestamp(CurrentTimestamp())
    { data.dropEnter = d; }

    explicit NkEvent(const NkDropOverData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_DROP), window(w), timestamp(CurrentTimestamp())
    { data.dropOver = d; }

    explicit NkEvent(const NkDropLeaveData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_DROP), window(w), timestamp(CurrentTimestamp())
    { data.dropLeave = d; }

    explicit NkEvent(const NkDropFileData& d, Window* w = nullptr)
        : type(NkEventType::NK_DROP_FILE), category(NkEventCategory::NK_CAT_DROP)
        , window(w), timestamp(CurrentTimestamp())
    {
        mOwnedDropFile = std::make_unique<NkDropFileData>(d);
        dropFile = mOwnedDropFile.get();
    }

    explicit NkEvent(NkDropFileData* d, Window* w = nullptr)
        : type(NkEventType::NK_DROP_FILE), category(NkEventCategory::NK_CAT_DROP)
        , window(w), timestamp(CurrentTimestamp())
    {
        if (d)
        {
            mOwnedDropFile = std::make_unique<NkDropFileData>(*d);
            dropFile = mOwnedDropFile.get();
        }
    }

    explicit NkEvent(const NkDropTextData& d, Window* w = nullptr)
        : type(NkEventType::NK_DROP_TEXT), category(NkEventCategory::NK_CAT_DROP)
        , window(w), timestamp(CurrentTimestamp())
    {
        mOwnedDropText = std::make_unique<NkDropTextData>(d);
        dropText = mOwnedDropText.get();
    }

    explicit NkEvent(NkDropTextData* d, Window* w = nullptr)
        : type(NkEventType::NK_DROP_TEXT), category(NkEventCategory::NK_CAT_DROP)
        , window(w), timestamp(CurrentTimestamp())
    {
        if (d)
        {
            mOwnedDropText = std::make_unique<NkDropTextData>(*d);
            dropText = mOwnedDropText.get();
        }
    }

    explicit NkEvent(const NkDropImageData& d, Window* w = nullptr)
        : type(NkEventType::NK_DROP_IMAGE), category(NkEventCategory::NK_CAT_DROP)
        , window(w), timestamp(CurrentTimestamp())
    {
        mOwnedDropImage = std::make_unique<NkDropImageData>(d);
        dropImage = mOwnedDropImage.get();
    }

    explicit NkEvent(NkDropImageData* d, Window* w = nullptr)
        : type(NkEventType::NK_DROP_IMAGE), category(NkEventCategory::NK_CAT_DROP)
        , window(w), timestamp(CurrentTimestamp())
    {
        if (d)
        {
            mOwnedDropImage = std::make_unique<NkDropImageData>(*d);
            dropImage = mOwnedDropImage.get();
        }
    }

    // --- Système ---
    explicit NkEvent(const NkSystemPowerData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_SYSTEM), window(w), timestamp(CurrentTimestamp())
    { data.systemPower = d; }

    explicit NkEvent(const NkSystemLocaleData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_SYSTEM), window(w), timestamp(CurrentTimestamp())
    { data.systemLocale = d; }

    explicit NkEvent(const NkSystemDisplayData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_SYSTEM), window(w), timestamp(CurrentTimestamp())
    { data.systemDisplay = d; }

    explicit NkEvent(const NkSystemMemoryData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_SYSTEM), window(w), timestamp(CurrentTimestamp())
    { data.systemMemory = d; }

    // --- Personnalisé ---
    explicit NkEvent(const NkCustomData& d, Window* w = nullptr)
        : type(d.TYPE), category(NkEventCategory::NK_CAT_CUSTOM), window(w), timestamp(CurrentTimestamp())
    { data.custom = d; }

    // -----------------------------------------------------------------------
    // API
    // -----------------------------------------------------------------------

    bool IsValid()   const { return type != NkEventType::NK_NONE; }
    bool IsHandled() const { return handled; }
    void MarkHandled()     { handled = true; }

    bool IsWindow()   const { return NkCategoryHas(category, NkEventCategory::NK_CAT_WINDOW);   }
    bool IsKeyboard() const { return NkCategoryHas(category, NkEventCategory::NK_CAT_KEYBOARD); }
    bool IsMouse()    const { return NkCategoryHas(category, NkEventCategory::NK_CAT_MOUSE);    }
    bool IsTouch()    const { return NkCategoryHas(category, NkEventCategory::NK_CAT_TOUCH);    }
    bool IsGamepad()  const { return NkCategoryHas(category, NkEventCategory::NK_CAT_GAMEPAD);  }
    bool IsDrop()     const { return NkCategoryHas(category, NkEventCategory::NK_CAT_DROP);     }
    bool IsSystem()   const { return NkCategoryHas(category, NkEventCategory::NK_CAT_SYSTEM);   }

    template<typename T>
    bool Is() const { return type == T::TYPE; }

    template<typename T>
    T* As() { return (type == T::TYPE) ? static_cast<T*>(this) : nullptr; }

    template<typename T>
    const T* As() const { return (type == T::TYPE) ? static_cast<const T*>(this) : nullptr; }

    std::string ToString() const;

    static NkTimestampMs CurrentTimestamp()
    {
        using namespace std::chrono;
        static auto sStart = steady_clock::now();
        return static_cast<NkTimestampMs>(
            duration_cast<milliseconds>(steady_clock::now() - sStart).count());
    }

private:
    std::unique_ptr<NkDropFileData>  mOwnedDropFile;
    std::unique_ptr<NkDropTextData>  mOwnedDropText;
    std::unique_ptr<NkDropImageData> mOwnedDropImage;

    void ResetDropOwnership()
    {
        mOwnedDropFile.reset();
        mOwnedDropText.reset();
        mOwnedDropImage.reset();
        dropFile  = nullptr;
        dropText  = nullptr;
        dropImage = nullptr;
    }

    void CopyFrom(const NkEvent& other)
    {
        type      = other.type;
        category  = other.category;
        window    = other.window;
        timestamp = other.timestamp;
        handled   = other.handled;
        data      = other.data;

        ResetDropOwnership();

        if (other.dropFile)
        {
            mOwnedDropFile = std::make_unique<NkDropFileData>(*other.dropFile);
            dropFile = mOwnedDropFile.get();
        }
        if (other.dropText)
        {
            mOwnedDropText = std::make_unique<NkDropTextData>(*other.dropText);
            dropText = mOwnedDropText.get();
        }
        if (other.dropImage)
        {
            mOwnedDropImage = std::make_unique<NkDropImageData>(*other.dropImage);
            dropImage = mOwnedDropImage.get();
        }
    }

    void MoveFrom(NkEvent&& other)
    {
        type      = other.type;
        category  = other.category;
        window    = other.window;
        timestamp = other.timestamp;
        handled   = other.handled;
        data      = other.data;

        ResetDropOwnership();
        mOwnedDropFile  = std::move(other.mOwnedDropFile);
        mOwnedDropText  = std::move(other.mOwnedDropText);
        mOwnedDropImage = std::move(other.mOwnedDropImage);

        dropFile  = mOwnedDropFile  ? mOwnedDropFile.get()  : other.dropFile;
        dropText  = mOwnedDropText  ? mOwnedDropText.get()  : other.dropText;
        dropImage = mOwnedDropImage ? mOwnedDropImage.get() : other.dropImage;

        other.dropFile  = nullptr;
        other.dropText  = nullptr;
        other.dropImage = nullptr;
    }

    static NkEventType StateToType(NkWindowStateData::State s)
    {
        switch (s)
        {
        case NkWindowStateData::State::Minimized:  return NkEventType::NK_WINDOW_MINIMIZE;
        case NkWindowStateData::State::Maximized:  return NkEventType::NK_WINDOW_MAXIMIZE;
        case NkWindowStateData::State::Restored:   return NkEventType::NK_WINDOW_RESTORE;
        case NkWindowStateData::State::Fullscreen: return NkEventType::NK_WINDOW_FULLSCREEN;
        case NkWindowStateData::State::Windowed:   return NkEventType::NK_WINDOW_WINDOWED;
        default:                                   return NkEventType::NK_NONE;
        }
    }
};

// ===========================================================================
// Alias de compatibilité avec l'ancien NkEvent.h
// ===========================================================================

using NkFocusData      = NkWindowFocusData;
using NkResizeData     = NkWindowResizeData;
using NkMoveData       = NkWindowMoveData;
using NkDpiData        = NkWindowDpiData;
using NkKeyboardData   = NkKeyData;
using NkMouseInputData = NkMouseButtonData;

} // namespace nkentseu
