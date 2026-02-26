#pragma once

// =============================================================================
// NkWin32EventImpl.h
// ImplÃ©mentation Win32 de IEventImpl.
//
// ResponsabilitÃ©s (V2 refonte) :
//   - Table HWND â†’ (NkWin32WindowImpl*, callback) â€” thread_local
//   - WindowProcStatic / ProcessWin32Message â€” WndProc ici
//   - RegisterPending() â€” phase bootstrap pendant CreateWindowEx
//   - Initialize() / Shutdown() â€” enregistrement/dÃ©senregistrement fenÃªtres
//   - RawInput â€” enregistrÃ© Ã  l'Initialize de la premiÃ¨re fenÃªtre
//   - BlitSoftwareFramebuffer â€” dÃ©lÃ©guÃ© depuis IRendererImpl::Present()
//   - SetEventCallback / SetWindowCallback / DispatchEvent
// =============================================================================

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <windowsx.h>
#include <unordered_map>
#include <functional>
#include <vector>

#include "../../Core/IEventImpl.h"
#include "../../Core/Events/NkEventTypes.h"

/**
 * @brief Namespace nkentseu.
 */
namespace nkentseu {

class NkWin32WindowImpl;

/**
 * @brief Class NkWin32EventImpl.
 */
class NkWin32EventImpl : public IEventImpl {
public:
	NkWin32EventImpl() = default;
	~NkWin32EventImpl() override = default;

	// -----------------------------------------------------------------------
	// IEventImpl â€” Cycle de vie
	// -----------------------------------------------------------------------

	void Initialize(IWindowImpl *owner, void *nativeHandle) override;
	void Shutdown(void *nativeHandle) override;

	// -----------------------------------------------------------------------
	// IEventImpl â€” Queue
	// -----------------------------------------------------------------------

	void PollEvents() override;
	const NkEvent &Front() const override;
	void Pop() override;
	bool IsEmpty() const override;
	void PushEvent(const NkEvent &event) override;
	std::size_t Size() const override;

	// -----------------------------------------------------------------------
	// IEventImpl â€” Callbacks
	// -----------------------------------------------------------------------

	void SetEventCallback(NkEventCallback cb) override;
	void SetWindowCallback(void *nativeHandle, NkEventCallback cb) override;
	void DispatchEvent(NkEvent &event, void *nativeHandle) override;

	// -----------------------------------------------------------------------
	// Bootstrap CreateWindowEx (appelÃ© par NkWin32WindowImpl::Create)
	// -----------------------------------------------------------------------

	/**
	 * Enregistre la fenÃªtre en attente AVANT CreateWindowEx.
	 * Pendant WM_CREATE, WindowProcStatic l'insÃ¨re dans la table.
	 */
	void RegisterPending(NkWin32WindowImpl *owner);

	// -----------------------------------------------------------------------
	// WndProc statique â€” publique pour que NkWin32WindowImpl puisse la passer
	// Ã  RegisterClassEx.
	// -----------------------------------------------------------------------

	static LRESULT CALLBACK WindowProcStatic(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp);

	// -----------------------------------------------------------------------
	// Blit software (appelÃ© depuis NkSoftwareRendererImpl::Present)
	// -----------------------------------------------------------------------

	static void BlitToHwnd(HWND hwnd, const NkU8 *rgbaPixels, NkU32 w, NkU32 h);

	// -----------------------------------------------------------------------
	// AccÃ¨s
	// -----------------------------------------------------------------------

	NkWin32WindowImpl *FindWindow(HWND hwnd) const;

private:
	LRESULT ProcessWin32Message(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp, NkWin32WindowImpl *owner);

	static NkKey VkeyToNkKey(WPARAM vk, LPARAM flags);
	static NkModifierState CurrentMods();

	// -----------------------------------------------------------------------
	// Table thread_local : HWND â†’ entrÃ©e (WindowImpl + callback)
	// -----------------------------------------------------------------------

	struct WindowEntry {
		NkWin32WindowImpl *window = nullptr;
		NkEventCallback callback;
	};

	// Thread_local car les fenÃªtres Win32 appartiennent au thread crÃ©ateur.
	static thread_local std::unordered_map<HWND, WindowEntry> sWindowMap;

	// Bootstrap : pendant CreateWindowEx le HWND n'est pas encore dans la map.
	static thread_local NkWin32WindowImpl *sPendingOwner;
	static thread_local NkWin32EventImpl *sPendingEventImpl;

	NkEventCallback mGlobalCallback;
	bool mRawInputRegistered = false;
	NkI32 mPrevMouseX = 0;
	NkI32 mPrevMouseY = 0;
};

} // namespace nkentseu

