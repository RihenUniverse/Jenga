#pragma once
// NkUIKitEventImpl.h — stub UIKit/iOS
#include "../../Core/IEventImpl.h"
/**
 * @brief Namespace nkentseu.
 */
namespace nkentseu {
/**
 * @brief Class NkUIKitEventImpl.
 */
class NkUIKitEventImpl : public IEventImpl {
public:
	void Initialize(IWindowImpl *, void *) override {
	}
	void Shutdown(void *) override {
	}
	void PollEvents() override {
	}
	const NkEvent &Front() const override {
		return mDummyEvent;
	}
	void Pop() override {
	}
	bool IsEmpty() const override {
		return true;
	}
	void PushEvent(const NkEvent &) override {
	}
	std::size_t Size() const override {
		return 0;
	}
	void SetEventCallback(NkEventCallback) override {
	}
	void SetWindowCallback(void *, NkEventCallback) override {
	}
	void DispatchEvent(NkEvent &, void *) override {
	}
};
} // namespace nkentseu
