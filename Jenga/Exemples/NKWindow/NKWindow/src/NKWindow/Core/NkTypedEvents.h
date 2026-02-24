#pragma once

// =============================================================================
// NkTypedEvents.h - classes evenements types complets (tous types)
// =============================================================================

#include "NkEvent.h"

namespace nkentseu
{

// ===========================================================================
// FENETRE
// ===========================================================================

class NkWindowCreateEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_CREATE;
    NkU32 GetWidth()  const { return data.windowCreate.width; }
    NkU32 GetHeight() const { return data.windowCreate.height; }
};

class NkWindowCloseEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_CLOSE;
    bool    IsForced()  const { return data.windowClose.forced; }
    Window* GetWindow() const { return window; }
};

class NkWindowDestroyEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_DESTROY;
};

class NkWindowPaintEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_PAINT;
    bool  IsFullPaint() const { return data.windowPaint.IsFullPaint(); }
    NkI32 GetDirtyX()   const { return data.windowPaint.dirtyX; }
    NkI32 GetDirtyY()   const { return data.windowPaint.dirtyY; }
    NkU32 GetDirtyW()   const { return data.windowPaint.dirtyW; }
    NkU32 GetDirtyH()   const { return data.windowPaint.dirtyH; }
};

class NkWindowResizeEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_RESIZE;
    NkU32 GetWidth()      const { return data.windowResize.width;      }
    NkU32 GetHeight()     const { return data.windowResize.height;     }
    NkU32 GetPrevWidth()  const { return data.windowResize.prevWidth;  }
    NkU32 GetPrevHeight() const { return data.windowResize.prevHeight; }
    bool  GotSmaller()    const { return data.windowResize.GotSmaller(); }
};

class NkWindowResizeBeginEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_RESIZE_BEGIN;
};

class NkWindowResizeEndEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_RESIZE_END;
};

class NkWindowMoveEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_MOVE;
    NkI32 GetX()     const { return data.windowMove.x;     }
    NkI32 GetY()     const { return data.windowMove.y;     }
    NkI32 GetPrevX() const { return data.windowMove.prevX; }
    NkI32 GetPrevY() const { return data.windowMove.prevY; }
};

class NkWindowMoveBeginEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_MOVE_BEGIN;
};

class NkWindowMoveEndEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_MOVE_END;
};

class NkWindowFocusGainedEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_FOCUS_GAINED;
    bool IsFocused() const { return true; }
};

class NkWindowFocusLostEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_FOCUS_LOST;
    bool IsFocused() const { return false; }
};

class NkWindowMinimizeEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_MINIMIZE;
    bool IsMinimized() const { return true; }
};

class NkWindowMaximizeEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_MAXIMIZE;
    bool IsMaximized() const { return true; }
};

class NkWindowRestoreEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_RESTORE;
    bool IsRestored() const { return true; }
};

class NkWindowFullscreenEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_FULLSCREEN;
    bool IsFullscreen() const { return true; }
};

class NkWindowWindowedEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_WINDOWED;
    bool IsWindowed() const { return true; }
};

class NkWindowDpiEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_DPI_CHANGE;
    float GetScale()     const { return data.windowDpi.scale;     }
    float GetPrevScale() const { return data.windowDpi.prevScale; }
    NkU32 GetDpi()       const { return data.windowDpi.dpi;       }
};

class NkWindowThemeEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_THEME_CHANGE;
    NkWindowTheme GetTheme() const { return data.windowTheme.theme; }
    bool IsDark()  const { return data.windowTheme.theme == NkWindowTheme::NK_THEME_DARK;  }
    bool IsLight() const { return data.windowTheme.theme == NkWindowTheme::NK_THEME_LIGHT; }
};

class NkWindowShownEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_SHOWN;
    bool IsVisible() const { return true; }
};

class NkWindowHiddenEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_WINDOW_HIDDEN;
    bool IsVisible() const { return false; }
};

// ===========================================================================
// CLAVIER
// ===========================================================================

class NkKeyEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_KEY_PRESS;
    NkKey           GetKey()       const { return data.key.key;       }
    NkButtonState   GetState()     const { return data.key.state;     }
    NkModifierState GetModifiers() const { return data.key.modifiers; }
    NkScancode      GetScancode()  const { return data.key.scancode;  }
    NkU32           GetNativeKey() const { return data.key.nativeKey; }
    bool IsPress()    const { return type == NkEventType::NK_KEY_PRESS;   }
    bool IsRelease()  const { return type == NkEventType::NK_KEY_RELEASE; }
    bool IsRepeat()   const { return type == NkEventType::NK_KEY_REPEAT;  }
    bool IsExtended() const { return data.key.extended; }
    bool HasCtrl()    const { return data.key.modifiers.ctrl;  }
    bool HasAlt()     const { return data.key.modifiers.alt;   }
    bool HasShift()   const { return data.key.modifiers.shift; }
    bool HasSuper()   const { return data.key.modifiers.super; }
    bool HasAltGr()   const { return data.key.modifiers.altGr; }
};

class NkKeyPressEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_KEY_PRESS;

    NkKey           GetKey()       const { return data.key.key;       }
    NkButtonState   GetState()     const { return data.key.state;     }
    NkModifierState GetModifiers() const { return data.key.modifiers; }
    NkScancode      GetScancode()  const { return data.key.scancode;  }
    NkU32           GetNativeKey() const { return data.key.nativeKey; }
    bool IsExtended() const { return data.key.extended; }
    bool HasCtrl()    const { return data.key.modifiers.ctrl;  }
    bool HasAlt()     const { return data.key.modifiers.alt;   }
    bool HasShift()   const { return data.key.modifiers.shift; }
    bool HasSuper()   const { return data.key.modifiers.super; }
    bool HasAltGr()   const { return data.key.modifiers.altGr; }
};

class NkKeyReleaseEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_KEY_RELEASE;

    NkKey           GetKey()       const { return data.key.key;       }
    NkButtonState   GetState()     const { return data.key.state;     }
    NkModifierState GetModifiers() const { return data.key.modifiers; }
    NkScancode      GetScancode()  const { return data.key.scancode;  }
    NkU32           GetNativeKey() const { return data.key.nativeKey; }
    bool IsExtended() const { return data.key.extended; }
    bool HasCtrl()    const { return data.key.modifiers.ctrl;  }
    bool HasAlt()     const { return data.key.modifiers.alt;   }
    bool HasShift()   const { return data.key.modifiers.shift; }
    bool HasSuper()   const { return data.key.modifiers.super; }
    bool HasAltGr()   const { return data.key.modifiers.altGr; }
};

class NkKeyRepeatEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_KEY_REPEAT;

    NkKey           GetKey()       const { return data.key.key;       }
    NkButtonState   GetState()     const { return data.key.state;     }
    NkModifierState GetModifiers() const { return data.key.modifiers; }
    NkScancode      GetScancode()  const { return data.key.scancode;  }
    NkU32           GetNativeKey() const { return data.key.nativeKey; }
    bool IsExtended() const { return data.key.extended; }
    bool HasCtrl()    const { return data.key.modifiers.ctrl;  }
    bool HasAlt()     const { return data.key.modifiers.alt;   }
    bool HasShift()   const { return data.key.modifiers.shift; }
    bool HasSuper()   const { return data.key.modifiers.super; }
    bool HasAltGr()   const { return data.key.modifiers.altGr; }
};

class NkTextInputEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_TEXT_INPUT;
    NkU32       GetCodepoint() const { return data.textInput.codepoint; }
    const char* GetUtf8()      const { return data.textInput.utf8;      }
    bool        IsPrintable()  const { return data.textInput.IsPrintable(); }
    bool        IsAscii()      const { return data.textInput.IsAscii();     }
};

// ===========================================================================
// SOURIS
// ===========================================================================

class NkMouseMoveEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_MOUSE_MOVE;
    NkI32 GetX()        const { return data.mouseMove.x;       }
    NkI32 GetY()        const { return data.mouseMove.y;       }
    NkI32 GetScreenX()  const { return data.mouseMove.screenX; }
    NkI32 GetScreenY()  const { return data.mouseMove.screenY; }
    NkI32 GetDeltaX()   const { return data.mouseMove.deltaX;  }
    NkI32 GetDeltaY()   const { return data.mouseMove.deltaY;  }
    NkModifierState GetModifiers() const { return data.mouseMove.modifiers; }
    bool IsButtonDown(NkMouseButton b) const { return data.mouseMove.IsButtonDown(b); }
};

class NkMouseRawEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_MOUSE_RAW;
    NkI32 GetDeltaX() const { return data.mouseRaw.deltaX; }
    NkI32 GetDeltaY() const { return data.mouseRaw.deltaY; }
    NkI32 GetDeltaZ() const { return data.mouseRaw.deltaZ; }
};

class NkMouseButtonEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_MOUSE_BUTTON_PRESS;
    NkMouseButton   GetButton()     const { return data.mouseButton.button;     }
    NkButtonState   GetState()      const { return data.mouseButton.state;      }
    NkModifierState GetModifiers()  const { return data.mouseButton.modifiers;  }
    NkI32           GetX()          const { return data.mouseButton.x;          }
    NkI32           GetY()          const { return data.mouseButton.y;          }
    NkI32           GetScreenX()    const { return data.mouseButton.screenX;    }
    NkI32           GetScreenY()    const { return data.mouseButton.screenY;    }
    NkU32           GetClickCount() const { return data.mouseButton.clickCount; }
    bool IsPress()       const { return type == NkEventType::NK_MOUSE_BUTTON_PRESS;   }
    bool IsRelease()     const { return type == NkEventType::NK_MOUSE_BUTTON_RELEASE; }
    bool IsDoubleClick() const { return type == NkEventType::NK_MOUSE_DOUBLE_CLICK;   }
    bool IsLeft()   const { return data.mouseButton.button == NkMouseButton::NK_MB_LEFT;   }
    bool IsRight()  const { return data.mouseButton.button == NkMouseButton::NK_MB_RIGHT;  }
    bool IsMiddle() const { return data.mouseButton.button == NkMouseButton::NK_MB_MIDDLE; }
};

class NkMouseButtonPressEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_MOUSE_BUTTON_PRESS;

    NkMouseButton   GetButton()     const { return data.mouseButton.button;     }
    NkButtonState   GetState()      const { return data.mouseButton.state;      }
    NkModifierState GetModifiers()  const { return data.mouseButton.modifiers;  }
    NkI32           GetX()          const { return data.mouseButton.x;          }
    NkI32           GetY()          const { return data.mouseButton.y;          }
    NkI32           GetScreenX()    const { return data.mouseButton.screenX;    }
    NkI32           GetScreenY()    const { return data.mouseButton.screenY;    }
    NkU32           GetClickCount() const { return data.mouseButton.clickCount; }
    bool IsLeft()   const { return data.mouseButton.button == NkMouseButton::NK_MB_LEFT;   }
    bool IsRight()  const { return data.mouseButton.button == NkMouseButton::NK_MB_RIGHT;  }
    bool IsMiddle() const { return data.mouseButton.button == NkMouseButton::NK_MB_MIDDLE; }
};

class NkMouseButtonReleaseEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_MOUSE_BUTTON_RELEASE;

    NkMouseButton   GetButton()     const { return data.mouseButton.button;     }
    NkButtonState   GetState()      const { return data.mouseButton.state;      }
    NkModifierState GetModifiers()  const { return data.mouseButton.modifiers;  }
    NkI32           GetX()          const { return data.mouseButton.x;          }
    NkI32           GetY()          const { return data.mouseButton.y;          }
    NkI32           GetScreenX()    const { return data.mouseButton.screenX;    }
    NkI32           GetScreenY()    const { return data.mouseButton.screenY;    }
    NkU32           GetClickCount() const { return data.mouseButton.clickCount; }
    bool IsLeft()   const { return data.mouseButton.button == NkMouseButton::NK_MB_LEFT;   }
    bool IsRight()  const { return data.mouseButton.button == NkMouseButton::NK_MB_RIGHT;  }
    bool IsMiddle() const { return data.mouseButton.button == NkMouseButton::NK_MB_MIDDLE; }
};

class NkMouseDoubleClickEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_MOUSE_DOUBLE_CLICK;

    NkMouseButton   GetButton()     const { return data.mouseButton.button;     }
    NkButtonState   GetState()      const { return data.mouseButton.state;      }
    NkModifierState GetModifiers()  const { return data.mouseButton.modifiers;  }
    NkI32           GetX()          const { return data.mouseButton.x;          }
    NkI32           GetY()          const { return data.mouseButton.y;          }
    NkI32           GetScreenX()    const { return data.mouseButton.screenX;    }
    NkI32           GetScreenY()    const { return data.mouseButton.screenY;    }
    NkU32           GetClickCount() const { return data.mouseButton.clickCount; }
    bool IsLeft()   const { return data.mouseButton.button == NkMouseButton::NK_MB_LEFT;   }
    bool IsRight()  const { return data.mouseButton.button == NkMouseButton::NK_MB_RIGHT;  }
    bool IsMiddle() const { return data.mouseButton.button == NkMouseButton::NK_MB_MIDDLE; }
};

class NkMouseWheelVerticalEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_MOUSE_WHEEL_VERTICAL;
    double GetDelta()        const { return data.mouseWheel.deltaY;      }
    double GetPixelDelta()   const { return data.mouseWheel.pixelDeltaY; }
    NkI32  GetX()            const { return data.mouseWheel.x;           }
    NkI32  GetY()            const { return data.mouseWheel.y;           }
    bool   IsHighPrecision() const { return data.mouseWheel.highPrecision; }
    bool   ScrollsUp()       const { return data.mouseWheel.deltaY > 0;    }
    bool   ScrollsDown()     const { return data.mouseWheel.deltaY < 0;    }
    NkModifierState GetModifiers() const { return data.mouseWheel.modifiers; }
};

class NkMouseWheelHorizontalEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_MOUSE_WHEEL_HORIZONTAL;
    double GetDelta()        const { return data.mouseWheel.deltaX;      }
    double GetPixelDelta()   const { return data.mouseWheel.pixelDeltaX; }
    NkI32  GetX()            const { return data.mouseWheel.x;           }
    NkI32  GetY()            const { return data.mouseWheel.y;           }
    bool   IsHighPrecision() const { return data.mouseWheel.highPrecision; }
    bool   ScrollsLeft()     const { return data.mouseWheel.deltaX < 0;    }
    bool   ScrollsRight()    const { return data.mouseWheel.deltaX > 0;    }
    NkModifierState GetModifiers() const { return data.mouseWheel.modifiers; }
};

class NkMouseEnterEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_MOUSE_ENTER;
    bool IsEnter() const { return true; }
};

class NkMouseLeaveEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_MOUSE_LEAVE;
    bool IsLeave() const { return true; }
};

class NkMouseCaptureBeginEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_MOUSE_CAPTURE_BEGIN;
};

class NkMouseCaptureEndEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_MOUSE_CAPTURE_END;
};

// ===========================================================================
// TACTILE
// ===========================================================================

class NkTouchEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_TOUCH_BEGIN;
    NkU32 GetNumTouches() const { return data.touch.numTouches; }
    const NkTouchPoint& GetTouch(NkU32 i) const { return data.touch.touches[i]; }
    float GetCentroidX()  const { return data.touch.centroidX; }
    float GetCentroidY()  const { return data.touch.centroidY; }
    bool  IsBegin()  const { return type == NkEventType::NK_TOUCH_BEGIN;  }
    bool  IsMove()   const { return type == NkEventType::NK_TOUCH_MOVE;   }
    bool  IsEnd()    const { return type == NkEventType::NK_TOUCH_END;    }
    bool  IsCancel() const { return type == NkEventType::NK_TOUCH_CANCEL; }
};

class NkTouchBeginEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_TOUCH_BEGIN;
    NkU32 GetNumTouches() const { return data.touch.numTouches; }
    const NkTouchPoint& GetTouch(NkU32 i) const { return data.touch.touches[i]; }
    float GetCentroidX()  const { return data.touch.centroidX; }
    float GetCentroidY()  const { return data.touch.centroidY; }
};

class NkTouchMoveEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_TOUCH_MOVE;
    NkU32 GetNumTouches() const { return data.touch.numTouches; }
    const NkTouchPoint& GetTouch(NkU32 i) const { return data.touch.touches[i]; }
    float GetCentroidX()  const { return data.touch.centroidX; }
    float GetCentroidY()  const { return data.touch.centroidY; }
};

class NkTouchEndEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_TOUCH_END;
    NkU32 GetNumTouches() const { return data.touch.numTouches; }
    const NkTouchPoint& GetTouch(NkU32 i) const { return data.touch.touches[i]; }
    float GetCentroidX()  const { return data.touch.centroidX; }
    float GetCentroidY()  const { return data.touch.centroidY; }
};

class NkTouchCancelEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_TOUCH_CANCEL;
    NkU32 GetNumTouches() const { return data.touch.numTouches; }
    const NkTouchPoint& GetTouch(NkU32 i) const { return data.touch.touches[i]; }
    float GetCentroidX()  const { return data.touch.centroidX; }
    float GetCentroidY()  const { return data.touch.centroidY; }
};

class NkGesturePinchEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_GESTURE_PINCH;
    float GetScale()      const { return data.gesturePinch.scale;      }
    float GetScaleDelta() const { return data.gesturePinch.scaleDelta; }
    float GetCenterX()    const { return data.gesturePinch.centerX;    }
    float GetCenterY()    const { return data.gesturePinch.centerY;    }
    bool  IsZoomIn()      const { return data.gesturePinch.IsZoomIn(); }
    bool  IsZoomOut()     const { return data.gesturePinch.IsZoomOut();}
};

class NkGestureRotateEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_GESTURE_ROTATE;
    float GetAngle()      const { return data.gestureRotate.angleDegrees;      }
    float GetAngleDelta() const { return data.gestureRotate.angleDeltaDegrees; }
    bool  IsClockwise()   const { return data.gestureRotate.IsClockwise();     }
};

class NkGesturePanEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_GESTURE_PAN;
    float GetDeltaX()    const { return data.gesturePan.deltaX;    }
    float GetDeltaY()    const { return data.gesturePan.deltaY;    }
    float GetVelocityX() const { return data.gesturePan.velocityX; }
    float GetVelocityY() const { return data.gesturePan.velocityY; }
    NkU32 GetNumFingers()const { return data.gesturePan.numFingers;}
};

class NkGestureSwipeEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_GESTURE_SWIPE;
    NkSwipeDirection GetDirection() const { return data.gestureSwipe.direction; }
    float            GetSpeed()     const { return data.gestureSwipe.speed;     }
    bool IsLeft()  const { return data.gestureSwipe.direction == NkSwipeDirection::NK_SWIPE_LEFT;  }
    bool IsRight() const { return data.gestureSwipe.direction == NkSwipeDirection::NK_SWIPE_RIGHT; }
    bool IsUp()    const { return data.gestureSwipe.direction == NkSwipeDirection::NK_SWIPE_UP;    }
    bool IsDown()  const { return data.gestureSwipe.direction == NkSwipeDirection::NK_SWIPE_DOWN;  }
};

class NkGestureTapEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_GESTURE_TAP;
    NkU32 GetTapCount()   const { return data.gestureTap.tapCount;   }
    NkU32 GetNumFingers() const { return data.gestureTap.numFingers; }
    float GetX()          const { return data.gestureTap.x;          }
    float GetY()          const { return data.gestureTap.y;          }
    bool  IsDoubleTap()   const { return data.gestureTap.tapCount >= 2; }
};

class NkGestureLongPressEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_GESTURE_LONG_PRESS;
    float GetX()          const { return data.gestureLongPress.x;          }
    float GetY()          const { return data.gestureLongPress.y;          }
    float GetDurationMs() const { return data.gestureLongPress.durationMs; }
};

// ===========================================================================
// MANETTE
// ===========================================================================

class NkGamepadConnectEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_GAMEPAD_CONNECT;
    bool IsConnected()           const { return data.gamepadConnect.connected;  }
    const NkGamepadInfo& GetInfo()const { return data.gamepadConnect.info;      }
    NkU32 GetIndex()             const { return data.gamepadConnect.info.index; }
};

class NkGamepadDisconnectEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_GAMEPAD_DISCONNECT;
    bool IsConnected()           const { return false; }
    NkU32 GetIndex()             const { return data.gamepadConnect.info.index; }
    const NkGamepadInfo& GetInfo()const { return data.gamepadConnect.info; }
};

class NkGamepadButtonEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_GAMEPAD_BUTTON_PRESS;
    NkU32           GetGamepadIndex() const { return data.gamepadButton.gamepadIndex; }
    NkGamepadButton GetButton()       const { return data.gamepadButton.button;       }
    NkButtonState   GetState()        const { return data.gamepadButton.state;        }
    float           GetAnalogValue()  const { return data.gamepadButton.analogValue;  }
    bool IsPress()   const { return type == NkEventType::NK_GAMEPAD_BUTTON_PRESS;   }
    bool IsRelease() const { return type == NkEventType::NK_GAMEPAD_BUTTON_RELEASE; }
};

class NkGamepadButtonPressEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_GAMEPAD_BUTTON_PRESS;

    NkU32           GetGamepadIndex() const { return data.gamepadButton.gamepadIndex; }
    NkGamepadButton GetButton()       const { return data.gamepadButton.button;       }
    NkButtonState   GetState()        const { return data.gamepadButton.state;        }
    float           GetAnalogValue()  const { return data.gamepadButton.analogValue;  }
};

class NkGamepadButtonReleaseEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_GAMEPAD_BUTTON_RELEASE;

    NkU32           GetGamepadIndex() const { return data.gamepadButton.gamepadIndex; }
    NkGamepadButton GetButton()       const { return data.gamepadButton.button;       }
    NkButtonState   GetState()        const { return data.gamepadButton.state;        }
    float           GetAnalogValue()  const { return data.gamepadButton.analogValue;  }
};

class NkGamepadAxisEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_GAMEPAD_AXIS_MOVE;
    NkU32         GetGamepadIndex() const { return data.gamepadAxis.gamepadIndex; }
    NkGamepadAxis GetAxis()         const { return data.gamepadAxis.axis;         }
    float         GetValue()        const { return data.gamepadAxis.value;        }
    float         GetPrevValue()    const { return data.gamepadAxis.prevValue;    }
    float         GetDelta()        const { return data.gamepadAxis.delta;        }
    bool          IsInDeadzone()    const { return data.gamepadAxis.IsInDeadzone(); }
};

class NkGamepadRumbleEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_GAMEPAD_RUMBLE;
    NkU32 GetGamepadIndex() const { return data.gamepadRumble.gamepadIndex; }
    float GetMotorLow()     const { return data.gamepadRumble.motorLow;     }
    float GetMotorHigh()    const { return data.gamepadRumble.motorHigh;    }
    float GetTriggerLeft()  const { return data.gamepadRumble.triggerLeft;  }
    float GetTriggerRight() const { return data.gamepadRumble.triggerRight; }
    NkU32 GetDurationMs()   const { return data.gamepadRumble.durationMs;   }
};

// ===========================================================================
// DRAG & DROP
// ===========================================================================

class NkDropEnterEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_DROP_ENTER;
    NkI32 GetX()        const { return data.dropEnter.x;        }
    NkI32 GetY()        const { return data.dropEnter.y;        }
    bool  HasText()     const { return data.dropEnter.hasText;  }
    bool  HasImage()    const { return data.dropEnter.hasImage; }
    NkU32 GetNumFiles() const { return data.dropEnter.numFiles; }
    NkDropType  GetType()     const { return data.dropEnter.dropType;  }
};

class NkDropOverEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_DROP_OVER;
    NkI32 GetX()        const { return data.dropOver.x;        }
    NkI32 GetY()        const { return data.dropOver.y;        }
    NkDropType  GetType()     const { return data.dropOver.dropType;  }
};

class NkDropLeaveEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_DROP_LEAVE;
};

class NkDropFileEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_DROP_FILE;
    NkDropFileData* GetDropData() const { return dropFile; }
    NkU32 GetCount() const { return dropFile ? dropFile->Count() : 0; }
    const std::string& GetPath(NkU32 i) const {
        static const std::string sEmpty;
        return (dropFile && i < dropFile->Count()) ? dropFile->paths[i] : sEmpty;
    }
};

class NkDropTextEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_DROP_TEXT;
    NkDropTextData*    GetDropData() const { return dropText; }
    const std::string& GetText()     const { static std::string e; return dropText ? dropText->text     : e; }
    const std::string& GetMimeType() const { static std::string e; return dropText ? dropText->mimeType : e; }
};

class NkDropImageEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_DROP_IMAGE;
    NkDropImageData*   GetDropData()  const { return dropImage; }
    NkU32              GetWidth()     const { return dropImage ? dropImage->width     : 0; }
    NkU32              GetHeight()    const { return dropImage ? dropImage->height    : 0; }
    const std::string& GetMimeType()  const { static std::string e; return dropImage ? dropImage->mimeType : e; }
    bool               HasPixels()    const { return dropImage && dropImage->HasPixels(); }
};

// ===========================================================================
// SYSTEME
// ===========================================================================

class NkSystemPowerEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_SYSTEM_POWER_SUSPEND;
    NkPowerState GetPowerState()   const { return data.systemPower.state;        }
    float        GetBatteryLevel() const { return data.systemPower.batteryLevel; }
    bool         IsPluggedIn()     const { return data.systemPower.pluggedIn;    }
    bool IsSuspend() const { return data.systemPower.state == NkPowerState::NK_POWER_SUSPENDED; }
    bool IsResume()  const { return data.systemPower.state == NkPowerState::NK_POWER_RESUMED;   }
};

class NkSystemPowerSuspendEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_SYSTEM_POWER_SUSPEND;
    float GetBatteryLevel() const { return data.systemPower.batteryLevel; }
    bool  IsPluggedIn()     const { return data.systemPower.pluggedIn;    }
};

class NkSystemPowerResumeEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_SYSTEM_POWER_RESUME;
    float GetBatteryLevel() const { return data.systemPower.batteryLevel; }
    bool  IsPluggedIn()     const { return data.systemPower.pluggedIn;    }
};

class NkSystemLowMemoryEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_SYSTEM_LOW_MEMORY;
    NkSystemMemoryData::Level GetLevel()        const { return data.systemMemory.level;          }
    NkU64                     GetAvailableBytes()const { return data.systemMemory.availableBytes; }
    bool IsCritical() const { return data.systemMemory.level == NkSystemMemoryData::Level::Critical; }
};

class NkSystemAppPauseEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_SYSTEM_APP_PAUSE;
};

class NkSystemAppResumeEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_SYSTEM_APP_RESUME;
};

class NkSystemLocaleChangeEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_SYSTEM_LOCALE_CHANGE;
    const char* GetNewLocale() const { return data.systemLocale.locale; }
};

class NkSystemDisplayEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_SYSTEM_DISPLAY_CHANGE;
    NkU32 GetDisplayIndex() const { return data.systemDisplay.displayIndex; }
    NkU32 GetWidth()        const { return data.systemDisplay.width;        }
    NkU32 GetHeight()       const { return data.systemDisplay.height;       }
    NkU32 GetRefreshRate()  const { return data.systemDisplay.refreshRate;  }
    float GetDpiScale()     const { return data.systemDisplay.dpiScale;     }
};

class NkSystemMemoryEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_SYSTEM_LOW_MEMORY;
    NkSystemMemoryData::Level GetLevel()        const { return data.systemMemory.level;          }
    NkU64                     GetAvailableBytes()const { return data.systemMemory.availableBytes; }
    bool IsCritical() const { return data.systemMemory.level == NkSystemMemoryData::Level::Critical; }
};

// ===========================================================================
// PERSONNALISE
// ===========================================================================

class NkCustomEvent : public NkEvent {
public:
    static constexpr NkEventType TYPE = NkEventType::NK_CUSTOM;
    NkU32       GetCustomType() const { return data.custom.customType; }
    void*       GetUserPtr()    const { return data.custom.userPtr;    }
    NkU32       GetDataSize()   const { return data.custom.dataSize;   }
    const NkU8* GetPayload()    const { return data.custom.payload;    }
    template<typename T>
    bool GetPayload(T& out) const { return data.custom.GetPayload(out); }
};

} // namespace nkentseu