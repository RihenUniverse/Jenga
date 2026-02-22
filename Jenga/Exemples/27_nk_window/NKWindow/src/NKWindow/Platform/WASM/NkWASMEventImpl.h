#pragma once

// =============================================================================
// NkWASMEventImpl.h  —  Système d'événements WebAssembly / Emscripten
// =============================================================================

#include "../../Core/IEventImpl.h"
#include <emscripten.h>
#include <emscripten/html5.h>
#include <unordered_map>

namespace nkentseu
{
class NkWASMWindowImpl;

class NkWASMEventImpl : public IEventImpl
{
public:
    NkWASMEventImpl();
    ~NkWASMEventImpl() override = default;

    void Initialize(IWindowImpl* owner, void* nativeHandle) override;
    void Shutdown  (void* nativeHandle)                     override;

    void           PollEvents()                    override;
    const NkEvent& Front()    const                override;
    void           Pop()                           override;
    bool           IsEmpty()  const                override;
    void           PushEvent(const NkEvent& event) override;
    std::size_t    Size()     const                override;

    void SetEventCallback(NkEventCallback cb)                            override;
    void SetWindowCallback(void* nativeHandle, NkEventCallback cb)       override;
    void DispatchEvent(NkEvent& event, void* nativeHandle)               override;

private:
    static EM_BOOL OnKeyDown  (int, const EmscriptenKeyboardEvent*, void*);
    static EM_BOOL OnKeyUp    (int, const EmscriptenKeyboardEvent*, void*);
    static EM_BOOL OnMouseMove(int, const EmscriptenMouseEvent*,    void*);
    static EM_BOOL OnMouseDown(int, const EmscriptenMouseEvent*,    void*);
    static EM_BOOL OnMouseUp  (int, const EmscriptenMouseEvent*,    void*);
    static EM_BOOL OnWheel    (int, const EmscriptenWheelEvent*,    void*);
    static NkKey   DomVkToNkKey(unsigned long kc);

    struct WindowEntry { NkWASMWindowImpl* window = nullptr; NkEventCallback callback; };
    std::unordered_map<void*, WindowEntry> mWindowMap;
    static NkWASMEventImpl* sInstance;
};
} // namespace nkentseu
