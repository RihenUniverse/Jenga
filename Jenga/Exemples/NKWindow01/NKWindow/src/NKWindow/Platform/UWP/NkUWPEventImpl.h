#pragma once
// NkUWPEventImpl.h — stub UWP
#include "../../Core/IEventImpl.h"
namespace nkentseu {
class NkUWPEventImpl : public IEventImpl {
public:
    void Initialize(IWindowImpl*,void*) override {}
    void Shutdown(void*)                override {}
    void PollEvents()                   override {}
    const NkEvent& Front() const override { return mDummyEvent; }
    void Pop()             override {}
    bool IsEmpty() const   override { return true; }
    void PushEvent(const NkEvent&) override {}
    std::size_t Size() const override { return 0; }
    void SetEventCallback(NkEventCallback)         override {}
    void SetWindowCallback(void*,NkEventCallback)  override {}
    void DispatchEvent(NkEvent&,void*)             override {}
};
}
