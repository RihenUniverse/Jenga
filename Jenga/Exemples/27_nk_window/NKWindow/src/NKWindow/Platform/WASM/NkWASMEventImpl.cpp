// =============================================================================
// NkWASMEventImpl.cpp
// =============================================================================

#include "NkWASMEventImpl.h"
#include "NkWASMWindowImpl.h"
#include "../../Core/Events/NkScancode.h"

namespace nkentseu
{

NkWASMEventImpl* NkWASMEventImpl::sInstance = nullptr;

NkWASMEventImpl::NkWASMEventImpl()
{
    sInstance = this;
    emscripten_set_keydown_callback(EMSCRIPTEN_EVENT_TARGET_WINDOW, this, 1, OnKeyDown);
    emscripten_set_keyup_callback(EMSCRIPTEN_EVENT_TARGET_WINDOW, this, 1, OnKeyUp);
    emscripten_set_mousemove_callback("#canvas", this, 1, OnMouseMove);
    emscripten_set_mousedown_callback("#canvas", this, 1, OnMouseDown);
    emscripten_set_mouseup_callback("#canvas", this, 1, OnMouseUp);
    emscripten_set_wheel_callback("#canvas", this, 1, OnWheel);
}

const NkEvent& NkWASMEventImpl::Front() const
{ return mQueue.empty() ? mDummyEvent : mQueue.front(); }
void        NkWASMEventImpl::Pop()           { if (!mQueue.empty()) mQueue.pop(); }
bool        NkWASMEventImpl::IsEmpty() const { return mQueue.empty(); }
std::size_t NkWASMEventImpl::Size()    const { return mQueue.size(); }
void        NkWASMEventImpl::PushEvent(const NkEvent& e) { mQueue.push(e); }

void NkWASMEventImpl::PollEvents()
{
    emscripten_sleep(0);
}

EM_BOOL NkWASMEventImpl::OnKeyDown(int, const EmscriptenKeyboardEvent* ke, void*)
{
    if (!sInstance) return EM_TRUE;

    // Préférer DOM code (ex: "KeyQ") au keyCode numérique — layout-agnostic
    NkScancode sc = NkScancodeFromDOMCode(ke->code);
    NkKey k = NkScancodeToKey(sc);
    if (k == NkKey::NK_UNKNOWN)
        k = DomVkToNkKey(ke->keyCode);  // Fallback keyCode numérique

    if (k != NkKey::NK_UNKNOWN)
    {
        NkModifierState mods(ke->ctrlKey, ke->altKey, ke->shiftKey, ke->metaKey);
        bool isRepeat = ke->repeat;
        NkButtonState st = isRepeat ? NkButtonState::NK_REPEAT : NkButtonState::NK_PRESSED;
        NkKeyData kd(k, st, mods, sc, static_cast<NkU32>(ke->keyCode), false, isRepeat);
        NkEvent ev(kd);
        sInstance->mQueue.push(ev);
        if (sInstance->mOwner) sInstance->mOwner->DispatchEvent(ev);
    }
    return EM_TRUE;
}

EM_BOOL NkWASMEventImpl::OnKeyUp(int, const EmscriptenKeyboardEvent* ke, void*)
{
    if (!sInstance) return EM_TRUE;

    NkScancode sc = NkScancodeFromDOMCode(ke->code);
    NkKey k = NkScancodeToKey(sc);
    if (k == NkKey::NK_UNKNOWN)
        k = DomVkToNkKey(ke->keyCode);

    if (k != NkKey::NK_UNKNOWN)
    {
        NkModifierState mods(ke->ctrlKey, ke->altKey, ke->shiftKey, ke->metaKey);
        NkKeyData kd(k, NkButtonState::NK_RELEASED, mods,
                     sc, static_cast<NkU32>(ke->keyCode), false, false);
        NkEvent ev(kd);
        sInstance->mQueue.push(ev);
        if (sInstance->mOwner) sInstance->mOwner->DispatchEvent(ev);
    }
    return EM_TRUE;
}

EM_BOOL NkWASMEventImpl::OnMouseMove(int, const EmscriptenMouseEvent* me, void*)
{
    if (!sInstance) return EM_TRUE;
    NkEvent ev(NkMouseMoveData(
        static_cast<NkU32>(me->targetX), static_cast<NkU32>(me->targetY),
        static_cast<NkU32>(me->screenX), static_cast<NkU32>(me->screenY),
        static_cast<NkI32>(me->movementX), static_cast<NkI32>(me->movementY)));
    sInstance->mQueue.push(ev);
    if (sInstance->mOwner) sInstance->mOwner->DispatchEvent(ev);
    return EM_TRUE;
}

EM_BOOL NkWASMEventImpl::OnMouseDown(int, const EmscriptenMouseEvent* me, void*)
{
    if (!sInstance) return EM_TRUE;
    NkMouseButton btn = me->button == 0 ? NkMouseButton::NK_LEFT
                      : me->button == 1 ? NkMouseButton::NK_MIDDLE
                      :                   NkMouseButton::NK_RIGHT;
    NkEvent ev(NkMouseInputData(btn, NkButtonState::NK_PRESSED, {}));
    sInstance->mQueue.push(ev);
    if (sInstance->mOwner) sInstance->mOwner->DispatchEvent(ev);
    return EM_TRUE;
}

EM_BOOL NkWASMEventImpl::OnMouseUp(int, const EmscriptenMouseEvent* me, void*)
{
    if (!sInstance) return EM_TRUE;
    NkMouseButton btn = me->button == 0 ? NkMouseButton::NK_LEFT
                      : me->button == 1 ? NkMouseButton::NK_MIDDLE
                      :                   NkMouseButton::NK_RIGHT;
    NkEvent ev(NkMouseInputData(btn, NkButtonState::NK_RELEASED, {}));
    sInstance->mQueue.push(ev);
    if (sInstance->mOwner) sInstance->mOwner->DispatchEvent(ev);
    return EM_TRUE;
}

EM_BOOL NkWASMEventImpl::OnWheel(int, const EmscriptenWheelEvent* we, void*)
{
    if (!sInstance) return EM_TRUE;
    NkEvent ev(NkMouseWheelData(-we->deltaY / 100.0, {}));
    sInstance->mQueue.push(ev);
    if (sInstance->mOwner) sInstance->mOwner->DispatchEvent(ev);
    return EM_TRUE;
}

NkKey NkWASMEventImpl::DomVkToNkKey(unsigned long kc)
{
    switch (kc)
    {
    case 27: return NkKey::NK_ESCAPE;
    case 112: return NkKey::NK_F1;  case 113: return NkKey::NK_F2;
    case 114: return NkKey::NK_F3;  case 115: return NkKey::NK_F4;
    case 116: return NkKey::NK_F5;  case 117: return NkKey::NK_F6;
    case 118: return NkKey::NK_F7;  case 119: return NkKey::NK_F8;
    case 120: return NkKey::NK_F9;  case 121: return NkKey::NK_F10;
    case 122: return NkKey::NK_F11; case 123: return NkKey::NK_F12;
    case 48: return NkKey::NK_NUM0; case 49: return NkKey::NK_NUM1;
    case 50: return NkKey::NK_NUM2; case 51: return NkKey::NK_NUM3;
    case 52: return NkKey::NK_NUM4; case 53: return NkKey::NK_NUM5;
    case 54: return NkKey::NK_NUM6; case 55: return NkKey::NK_NUM7;
    case 56: return NkKey::NK_NUM8; case 57: return NkKey::NK_NUM9;
    case 65: return NkKey::NK_A; case 66: return NkKey::NK_B;
    case 67: return NkKey::NK_C; case 68: return NkKey::NK_D;
    case 69: return NkKey::NK_E; case 70: return NkKey::NK_F_KEY;
    case 71: return NkKey::NK_G; case 72: return NkKey::NK_H;
    case 73: return NkKey::NK_I; case 74: return NkKey::NK_J;
    case 75: return NkKey::NK_K; case 76: return NkKey::NK_L;
    case 77: return NkKey::NK_M; case 78: return NkKey::NK_N;
    case 79: return NkKey::NK_O; case 80: return NkKey::NK_P;
    case 81: return NkKey::NK_Q; case 82: return NkKey::NK_R;
    case 83: return NkKey::NK_S; case 84: return NkKey::NK_T;
    case 85: return NkKey::NK_U; case 86: return NkKey::NK_V;
    case 87: return NkKey::NK_W; case 88: return NkKey::NK_X;
    case 89: return NkKey::NK_Y; case 90: return NkKey::NK_Z;
    case 32: return NkKey::NK_SPACE;
    case 13: return NkKey::NK_ENTER;
    case  8: return NkKey::NK_BACK;
    case  9: return NkKey::NK_TAB;
    case 16: return NkKey::NK_LSHIFT;
    case 17: return NkKey::NK_LCONTROL;
    case 18: return NkKey::NK_LALT;
    case 37: return NkKey::NK_LEFT;  case 39: return NkKey::NK_RIGHT;
    case 38: return NkKey::NK_UP;    case 40: return NkKey::NK_DOWN;
    case 45: return NkKey::NK_INSERT;case 46: return NkKey::NK_DELETE;
    case 36: return NkKey::NK_HOME;  case 35: return NkKey::NK_END;
    case 33: return NkKey::NK_PGUP;  case 34: return NkKey::NK_PGDN;
    default: return NkKey::NK_KEY_MAX;
    }
}

} // namespace nkentseu
