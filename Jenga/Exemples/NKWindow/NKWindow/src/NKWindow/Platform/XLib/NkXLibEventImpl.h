#pragma once

// =============================================================================
// NkXLibEventImpl.h  —  Système d'événements XLib
// Table Window → NkXLibWindowImpl*, poll XLib, keysym → NkKey.
// =============================================================================

#include "../../Core/IEventImpl.h"
#include "../../Core/Events/NkKeycodeMap.h"
#include <X11/Xlib.h>
#include <X11/keysym.h>
#include <unordered_map>

/**
 * @brief Namespace nkentseu.
 */
namespace nkentseu {

class NkXLibWindowImpl;

/**
 * @brief Class NkXLibEventImpl.
 */
class NkXLibEventImpl : public IEventImpl {
public:
	NkXLibEventImpl() = default;
	~NkXLibEventImpl() override = default;

	// Cycle de vie
	void Initialize(IWindowImpl *owner, void *nativeHandle) override;
	void Shutdown(void *nativeHandle) override;

	// Queue
	void PollEvents() override;
	const NkEvent &Front() const override;
	void Pop() override;
	bool IsEmpty() const override;
	void PushEvent(const NkEvent &event) override;
	std::size_t Size() const override;

	// Callbacks
	void SetEventCallback(NkEventCallback cb) override;
	void SetWindowCallback(void *nativeHandle, NkEventCallback cb) override;
	void DispatchEvent(NkEvent &event, void *nativeHandle) override;

private:
	static NkKey XlibKeysymToNkKey(KeySym ks);
	static NkModifierState XlibMods(unsigned int state);

	/**
	 * @brief Struct WindowEntry.
	 */
	struct WindowEntry {
		NkXLibWindowImpl *window = nullptr;
		NkEventCallback callback;
	};

	Display *mDisplay = nullptr;
	NkEventCallback mGlobalCallback;
	std::unordered_map<::Window, WindowEntry> mWindowMap;
};

} // namespace nkentseu
