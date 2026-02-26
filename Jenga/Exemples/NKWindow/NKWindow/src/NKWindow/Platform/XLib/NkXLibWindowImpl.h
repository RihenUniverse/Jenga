#pragma once

// =============================================================================
// NkXLibWindowImpl.h  —  Fenêtre XLib
// Aucun pointeur vers EventImpl, aucun callback d'événement ici.
// =============================================================================

#include "../../Core/IWindowImpl.h"
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/cursorfont.h>

/**
 * @brief Namespace nkentseu.
 */
namespace nkentseu {

extern Display *nk_xlib_global_display;

/**
 * @brief Struct NkXLibData.
 */
struct NkXLibData {
	Display *display = nullptr;
	::Window window = 0;
	int screen = 0;
	GC gc = nullptr;
	Atom wmDelete = 0;
	Atom wmProtocols = 0;
	Cursor blankCursor = 0;
	bool isOpen = false;
	NkU32 width = 0;
	NkU32 height = 0;
};

/**
 * @brief Class NkXLibWindowImpl.
 */
class NkXLibWindowImpl : public IWindowImpl {
public:
	NkXLibWindowImpl() = default;
	~NkXLibWindowImpl() override;

	bool Create(const NkWindowConfig &config) override;
	void Close() override;
	bool IsOpen() const override;

	std::string GetTitle() const override;
	void SetTitle(const std::string &t) override;
	NkVec2u GetSize() const override;
	NkVec2u GetPosition() const override;
	float GetDpiScale() const override {
		return 1.f;
	}
	NkVec2u GetDisplaySize() const override;
	NkVec2u GetDisplayPosition() const override {
		return {};
	}
	NkError GetLastError() const override;

	void SetSize(NkU32 w, NkU32 h) override;
	void SetPosition(NkI32 x, NkI32 y) override;
	void SetVisible(bool v) override;
	void Minimize() override;
	void Maximize() override;
	void Restore() override;
	void SetFullscreen(bool fs) override;
	void SetMousePosition(NkU32 x, NkU32 y) override;
	void ShowMouse(bool show) override;
	void CaptureMouse(bool cap) override;
	void SetProgress(float) override {
	}
	void SetBackgroundColor(NkU32 c);
	NkU32 GetBackgroundColor() const;

	NkSurfaceDesc GetSurfaceDesc() const override;

	::Window GetXlibWindow() const {
		return mData.window;
	}
	Display *GetDisplay() const {
		return mData.display;
	}
	Atom GetWmDeleteAtom() const {
		return mData.wmDelete;
	}
	Atom GetWmProtocolsAtom() const {
		return mData.wmProtocols;
	}

private:
	NkXLibData mData;
	NkU32 mBgColor = 0x141414FF;
};

} // namespace nkentseu
