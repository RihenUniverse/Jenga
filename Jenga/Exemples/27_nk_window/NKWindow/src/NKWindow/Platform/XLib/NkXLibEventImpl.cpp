// =============================================================================
// NkXLibEventImpl.cpp
// =============================================================================

#include "NkXLibEventImpl.h"
#include "NkXLibWindowImpl.h"
#include "../../Core/Events/NkScancode.h"
#include <X11/keysym.h>

namespace nkentseu
{

void NkXLibEventImpl::SetDisplay(Display* d, NkXLibWindowImpl* owner)
{ mDisplay = d; mOwner = owner; }

const NkEvent& NkXLibEventImpl::Front() const
{ return mQueue.empty() ? mDummyEvent : mQueue.front(); }
void        NkXLibEventImpl::Pop()           { if (!mQueue.empty()) mQueue.pop(); }
bool        NkXLibEventImpl::IsEmpty() const { return mQueue.empty(); }
std::size_t NkXLibEventImpl::Size()    const { return mQueue.size(); }
void        NkXLibEventImpl::PushEvent(const NkEvent& e) { mQueue.push(e); }

void NkXLibEventImpl::PollEvents()
{
    if (!mDisplay) return;

    while (XPending(mDisplay) > 0)
    {
        XEvent xev{};
        XNextEvent(mDisplay, &xev);

        NkEvent nkEv;
        switch (xev.type)
        {
        case KeyPress: case KeyRelease:
        {
            // Scancode USB HID depuis le keycode XLib (evdev = keycode - 8)
            NkScancode sc = NkScancodeFromXKeycode(xev.xkey.keycode);
            NkKey k = NkScancodeToKey(sc);

            // Fallback keysym si scancode inconnu
            if (k == NkKey::NK_UNKNOWN)
            {
                KeySym ks = XLookupKeysym(&xev.xkey, 0);
                k = XlibKeysymToNkKey(ks);
            }

            if (k != NkKey::NK_UNKNOWN)
            {
                NkButtonState st = (xev.type == KeyPress)
                    ? NkButtonState::NK_PRESSED : NkButtonState::NK_RELEASED;
                NkKeyData kd(k, st, XlibMods(xev.xkey.state),
                             sc,
                             static_cast<NkU32>(xev.xkey.keycode),
                             false, false);
                nkEv = NkEvent(kd);
            }
            break;
        }
        case ButtonPress: case ButtonRelease:
        {
            NkButtonState st = (xev.type == ButtonPress)
                ? NkButtonState::NK_PRESSED : NkButtonState::NK_RELEASED;
            switch (xev.xbutton.button)
            {
            case Button1:
                nkEv = NkEvent(NkMouseInputData(NkMouseButton::NK_LEFT, st, XlibMods(xev.xbutton.state))); break;
            case Button2:
                nkEv = NkEvent(NkMouseInputData(NkMouseButton::NK_MIDDLE, st, XlibMods(xev.xbutton.state))); break;
            case Button3:
                nkEv = NkEvent(NkMouseInputData(NkMouseButton::NK_RIGHT, st, XlibMods(xev.xbutton.state))); break;
            case Button4:
                if (xev.type == ButtonPress)
                    nkEv = NkEvent(NkMouseWheelData(1.0, XlibMods(xev.xbutton.state)));
                break;
            case Button5:
                if (xev.type == ButtonPress)
                    nkEv = NkEvent(NkMouseWheelData(-1.0, XlibMods(xev.xbutton.state)));
                break;
            default: break;
            }
            break;
        }
        case MotionNotify:
            nkEv = NkEvent(NkMouseMoveData(
                static_cast<NkU32>(xev.xmotion.x), static_cast<NkU32>(xev.xmotion.y),
                static_cast<NkU32>(xev.xmotion.x_root), static_cast<NkU32>(xev.xmotion.y_root),
                0, 0));
            break;
        case FocusIn:  nkEv = NkEvent(NkFocusData(true));  break;
        case FocusOut: nkEv = NkEvent(NkFocusData(false)); break;
        case ConfigureNotify:
            nkEv = NkEvent(NkResizeData(
                static_cast<NkU32>(xev.xconfigure.width),
                static_cast<NkU32>(xev.xconfigure.height), false));
            break;
        case ClientMessage:
            if (mOwner && (Atom)xev.xclient.data.l[0] == mOwner->GetXlibWindow())
                nkEv = NkEvent(NkEventType::NK_CLOSE);
            else
                nkEv = NkEvent(NkEventType::NK_CLOSE);
            break;
        default: break;
        }

        if (nkEv.IsValid())
        {
            mQueue.push(nkEv);
            if (mOwner) mOwner->DispatchEvent(nkEv);
        }
    }
}

NkKey NkXLibEventImpl::XlibKeysymToNkKey(KeySym ks)
{
    switch (ks)
    {
    case XK_Escape: return NkKey::NK_ESCAPE;
    case XK_F1:  return NkKey::NK_F1;  case XK_F2:  return NkKey::NK_F2;
    case XK_F3:  return NkKey::NK_F3;  case XK_F4:  return NkKey::NK_F4;
    case XK_F5:  return NkKey::NK_F5;  case XK_F6:  return NkKey::NK_F6;
    case XK_F7:  return NkKey::NK_F7;  case XK_F8:  return NkKey::NK_F8;
    case XK_F9:  return NkKey::NK_F9;  case XK_F10: return NkKey::NK_F10;
    case XK_F11: return NkKey::NK_F11; case XK_F12: return NkKey::NK_F12;
    case XK_grave:     return NkKey::NK_GRAVE;
    case XK_1: return NkKey::NK_NUM1; case XK_2: return NkKey::NK_NUM2;
    case XK_3: return NkKey::NK_NUM3; case XK_4: return NkKey::NK_NUM4;
    case XK_5: return NkKey::NK_NUM5; case XK_6: return NkKey::NK_NUM6;
    case XK_7: return NkKey::NK_NUM7; case XK_8: return NkKey::NK_NUM8;
    case XK_9: return NkKey::NK_NUM9; case XK_0: return NkKey::NK_NUM0;
    case XK_minus: return NkKey::NK_MINUS; case XK_equal: return NkKey::NK_EQUALS;
    case XK_BackSpace: return NkKey::NK_BACK;
    case XK_Tab:       return NkKey::NK_TAB;
    case XK_q: case XK_Q: return NkKey::NK_Q;
    case XK_w: case XK_W: return NkKey::NK_W;
    case XK_e: case XK_E: return NkKey::NK_E;
    case XK_r: case XK_R: return NkKey::NK_R;
    case XK_t: case XK_T: return NkKey::NK_T;
    case XK_y: case XK_Y: return NkKey::NK_Y;
    case XK_u: case XK_U: return NkKey::NK_U;
    case XK_i: case XK_I: return NkKey::NK_I;
    case XK_o: case XK_O: return NkKey::NK_O;
    case XK_p: case XK_P: return NkKey::NK_P;
    case XK_bracketleft: return NkKey::NK_LBRACKET;
    case XK_bracketright:return NkKey::NK_RBRACKET;
    case XK_backslash:   return NkKey::NK_BACKSLASH;
    case XK_Caps_Lock:   return NkKey::NK_CAPITAL;
    case XK_a: case XK_A: return NkKey::NK_A;
    case XK_s: case XK_S: return NkKey::NK_S;
    case XK_d: case XK_D: return NkKey::NK_D;
    case XK_f: case XK_F: return NkKey::NK_F_KEY;
    case XK_g: case XK_G: return NkKey::NK_G;
    case XK_h: case XK_H: return NkKey::NK_H;
    case XK_j: case XK_J: return NkKey::NK_J;
    case XK_k: case XK_K: return NkKey::NK_K;
    case XK_l: case XK_L: return NkKey::NK_L;
    case XK_semicolon: return NkKey::NK_SEMICOLON;
    case XK_apostrophe:return NkKey::NK_APOSTROPHE;
    case XK_Return:    return NkKey::NK_ENTER;
    case XK_Shift_L:   return NkKey::NK_LSHIFT;  case XK_Shift_R: return NkKey::NK_RSHIFT;
    case XK_z: case XK_Z: return NkKey::NK_Z;
    case XK_x: case XK_X: return NkKey::NK_X;
    case XK_c: case XK_C: return NkKey::NK_C;
    case XK_v: case XK_V: return NkKey::NK_V;
    case XK_b: case XK_B: return NkKey::NK_B;
    case XK_n: case XK_N: return NkKey::NK_N;
    case XK_m: case XK_M: return NkKey::NK_M;
    case XK_comma: return NkKey::NK_COMMA; case XK_period: return NkKey::NK_PERIOD;
    case XK_slash: return NkKey::NK_SLASH;
    case XK_Control_L: return NkKey::NK_LCONTROL; case XK_Control_R: return NkKey::NK_RCONTROL;
    case XK_Super_L:   return NkKey::NK_LWIN;     case XK_Super_R:   return NkKey::NK_RWIN;
    case XK_Alt_L:     return NkKey::NK_LALT;     case XK_Alt_R:     return NkKey::NK_RALT;
    case XK_space:     return NkKey::NK_SPACE;
    case XK_Insert: return NkKey::NK_INSERT; case XK_Delete: return NkKey::NK_DELETE;
    case XK_Home:   return NkKey::NK_HOME;   case XK_End:    return NkKey::NK_END;
    case XK_Page_Up: return NkKey::NK_PGUP;  case XK_Page_Down: return NkKey::NK_PGDN;
    case XK_Up:    return NkKey::NK_UP;    case XK_Down: return NkKey::NK_DOWN;
    case XK_Left:  return NkKey::NK_LEFT;  case XK_Right:return NkKey::NK_RIGHT;
    default: return NkKey::NK_KEY_MAX;
    }
}

NkModifierState NkXLibEventImpl::XlibMods(unsigned int state)
{
    return NkModifierState(
        !!(state & ControlMask), !!(state & Mod1Mask),
        !!(state & (ShiftMask|LockMask)), !!(state & Mod4Mask));
}

} // namespace nkentseu
