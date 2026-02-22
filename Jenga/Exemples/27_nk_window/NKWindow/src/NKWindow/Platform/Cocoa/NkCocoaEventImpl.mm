// =============================================================================
// NkCocoaEventImpl.mm
// Pompe d'événements NSApp pour macOS.
// =============================================================================

#import <Cocoa/Cocoa.h>
#include "NkCocoaEventImpl.h"
#include "../../Core/Events/NkScancode.h"

namespace nkentseu
{

// ---------------------------------------------------------------------------
// IEventImpl
// ---------------------------------------------------------------------------

const NkEvent& NkCocoaEventImpl::Front() const
{ return mQueue.empty() ? mDummyEvent : mQueue.front(); }

void        NkCocoaEventImpl::Pop()           { if (!mQueue.empty()) mQueue.pop(); }
bool        NkCocoaEventImpl::IsEmpty() const { return mQueue.empty(); }
std::size_t NkCocoaEventImpl::Size()    const { return mQueue.size(); }
void        NkCocoaEventImpl::PushEvent(const NkEvent& e) { mQueue.push(e); }

// ---------------------------------------------------------------------------
// PollEvents
// ---------------------------------------------------------------------------

void NkCocoaEventImpl::PollEvents()
{
    @autoreleasepool
    {
        NSEvent* ev = nil;
        while ((ev = [NSApp nextEventMatchingMask:NSEventMaskAny
                                       untilDate:[NSDate distantPast]
                                          inMode:NSDefaultRunLoopMode
                                         dequeue:YES]) != nil)
        {
            [NSApp sendEvent:ev];

            NkEvent nkEv;
            switch ([ev type])
            {
            case NSEventTypeKeyDown:
            case NSEventTypeKeyUp:
            {
                unsigned short macKC = [ev keyCode];

                // Scancode USB HID depuis le keyCode macOS
                NkScancode sc = NkScancodeFromMac(macKC);
                NkKey k = NkScancodeToKey(sc);

                // Fallback table interne si scancode inconnu
                if (k == NkKey::NK_UNKNOWN)
                    k = MacKeycodeToNkKey(macKC);

                if (k != NkKey::NK_UNKNOWN)
                {
                    bool isRepeat = ([ev isARepeat] == YES);
                    NkButtonState st = ([ev type] == NSEventTypeKeyDown)
                        ? (isRepeat ? NkButtonState::NK_REPEAT : NkButtonState::NK_PRESSED)
                        : NkButtonState::NK_RELEASED;

                    NkKeyData kd(k, st, NsModsToMods([ev modifierFlags]),
                                 sc,
                                 static_cast<NkU32>(macKC), // nativeKey = macOS keyCode
                                 false, isRepeat);
                    nkEv = NkEvent(kd);
                }
                break;
            }
            case NSEventTypeMouseMoved:
            case NSEventTypeLeftMouseDragged:
            case NSEventTypeRightMouseDragged:
            case NSEventTypeOtherMouseDragged:
            {
                NSPoint p = [ev locationInWindow];
                nkEv = NkEvent(NkMouseMoveData(
                    static_cast<NkU32>(p.x), static_cast<NkU32>(p.y),
                    static_cast<NkU32>(p.x), static_cast<NkU32>(p.y),
                    static_cast<NkI32>([ev deltaX]),
                    static_cast<NkI32>([ev deltaY])));
                break;
            }
            case NSEventTypeLeftMouseDown:
            case NSEventTypeLeftMouseUp:
            {
                NkButtonState st = ([ev type] == NSEventTypeLeftMouseDown)
                    ? NkButtonState::NK_PRESSED : NkButtonState::NK_RELEASED;
                nkEv = NkEvent(NkMouseInputData(
                    NkMouseButton::NK_LEFT, st,
                    NsModsToMods([ev modifierFlags])));
                break;
            }
            case NSEventTypeRightMouseDown:
            case NSEventTypeRightMouseUp:
            {
                NkButtonState st = ([ev type] == NSEventTypeRightMouseDown)
                    ? NkButtonState::NK_PRESSED : NkButtonState::NK_RELEASED;
                nkEv = NkEvent(NkMouseInputData(
                    NkMouseButton::NK_RIGHT, st,
                    NsModsToMods([ev modifierFlags])));
                break;
            }
            case NSEventTypeOtherMouseDown:
            case NSEventTypeOtherMouseUp:
            {
                NkButtonState st = ([ev type] == NSEventTypeOtherMouseDown)
                    ? NkButtonState::NK_PRESSED : NkButtonState::NK_RELEASED;
                nkEv = NkEvent(NkMouseInputData(
                    NkMouseButton::NK_MIDDLE, st,
                    NsModsToMods([ev modifierFlags])));
                break;
            }
            case NSEventTypeScrollWheel:
                nkEv = NkEvent(NkMouseWheelData(
                    [ev scrollingDeltaY],
                    NsModsToMods([ev modifierFlags])));
                break;
            default: break;
            }

            if (nkEv.IsValid()) mQueue.push(nkEv);
        }
    }
}

// ---------------------------------------------------------------------------
// Mapping keycode macOS → NkKey
// ---------------------------------------------------------------------------

NkKey NkCocoaEventImpl::MacKeycodeToNkKey(unsigned short code)
{
    switch (code)
    {
    case 0x35: return NkKey::NK_ESCAPE;
    case 0x7A: return NkKey::NK_F1;  case 0x78: return NkKey::NK_F2;
    case 0x63: return NkKey::NK_F3;  case 0x76: return NkKey::NK_F4;
    case 0x60: return NkKey::NK_F5;  case 0x61: return NkKey::NK_F6;
    case 0x62: return NkKey::NK_F7;  case 0x64: return NkKey::NK_F8;
    case 0x65: return NkKey::NK_F9;  case 0x6D: return NkKey::NK_F10;
    case 0x67: return NkKey::NK_F11; case 0x6F: return NkKey::NK_F12;
    case 0x32: return NkKey::NK_GRAVE;
    case 0x12: return NkKey::NK_NUM1; case 0x13: return NkKey::NK_NUM2;
    case 0x14: return NkKey::NK_NUM3; case 0x15: return NkKey::NK_NUM4;
    case 0x17: return NkKey::NK_NUM5; case 0x16: return NkKey::NK_NUM6;
    case 0x1A: return NkKey::NK_NUM7; case 0x1C: return NkKey::NK_NUM8;
    case 0x19: return NkKey::NK_NUM9; case 0x1D: return NkKey::NK_NUM0;
    case 0x1B: return NkKey::NK_MINUS;
    case 0x18: return NkKey::NK_EQUALS;
    case 0x33: return NkKey::NK_BACK;
    case 0x30: return NkKey::NK_TAB;
    case 0x0C: return NkKey::NK_Q; case 0x0D: return NkKey::NK_W;
    case 0x0E: return NkKey::NK_E; case 0x0F: return NkKey::NK_R;
    case 0x11: return NkKey::NK_T; case 0x10: return NkKey::NK_Y;
    case 0x20: return NkKey::NK_U; case 0x22: return NkKey::NK_I;
    case 0x1F: return NkKey::NK_O; case 0x23: return NkKey::NK_P;
    case 0x21: return NkKey::NK_LBRACKET;
    case 0x1E: return NkKey::NK_RBRACKET;
    case 0x2A: return NkKey::NK_BACKSLASH;
    case 0x39: return NkKey::NK_CAPITAL;
    case 0x00: return NkKey::NK_A; case 0x01: return NkKey::NK_S;
    case 0x02: return NkKey::NK_D; case 0x03: return NkKey::NK_F_KEY;
    case 0x05: return NkKey::NK_G; case 0x04: return NkKey::NK_H;
    case 0x26: return NkKey::NK_J; case 0x28: return NkKey::NK_K;
    case 0x25: return NkKey::NK_L;
    case 0x29: return NkKey::NK_SEMICOLON;
    case 0x27: return NkKey::NK_APOSTROPHE;
    case 0x24: return NkKey::NK_ENTER;
    case 0x38: return NkKey::NK_LSHIFT;
    case 0x3C: return NkKey::NK_RSHIFT;
    case 0x06: return NkKey::NK_Z; case 0x07: return NkKey::NK_X;
    case 0x08: return NkKey::NK_C; case 0x09: return NkKey::NK_V;
    case 0x0B: return NkKey::NK_B; case 0x2D: return NkKey::NK_N;
    case 0x2E: return NkKey::NK_M;
    case 0x2B: return NkKey::NK_COMMA;
    case 0x2F: return NkKey::NK_PERIOD;
    case 0x2C: return NkKey::NK_SLASH;
    case 0x3B: return NkKey::NK_LCONTROL;
    case 0x3E: return NkKey::NK_RCONTROL;
    case 0x37: return NkKey::NK_LWIN;
    case 0x36: return NkKey::NK_RWIN;
    case 0x3A: return NkKey::NK_LALT;
    case 0x3D: return NkKey::NK_RALT;
    case 0x31: return NkKey::NK_SPACE;
    case 0x72: return NkKey::NK_INSERT;
    case 0x75: return NkKey::NK_DELETE;
    case 0x73: return NkKey::NK_HOME;
    case 0x77: return NkKey::NK_END;
    case 0x74: return NkKey::NK_PGUP;
    case 0x79: return NkKey::NK_PGDN;
    case 0x7E: return NkKey::NK_UP;
    case 0x7D: return NkKey::NK_DOWN;
    case 0x7B: return NkKey::NK_LEFT;
    case 0x7C: return NkKey::NK_RIGHT;
    case 0x71: return NkKey::NK_SCROLL;
    case 0x69: return NkKey::NK_PRINT_SCREEN;
    default:   return NkKey::NK_KEY_MAX;
    }
}

NkModifierState NkCocoaEventImpl::NsModsToMods(unsigned long flags)
{
    return NkModifierState(
        !!(flags & NSEventModifierFlagControl),
        !!(flags & NSEventModifierFlagOption),
        !!(flags & NSEventModifierFlagShift),
        !!(flags & NSEventModifierFlagCommand));
}

} // namespace nkentseu
