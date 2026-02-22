// =============================================================================
// NkWin32WindowImpl.cpp
// Création fenêtre Win32 Unicode (RegisterClassExW / CreateWindowExW).
// Toutes les chaînes std::string sont converties en WCHAR via NkUtf8ToWide().
// =============================================================================

#include "NkWin32WindowImpl.h"
#include "NkWin32EventImpl.h"
#include "../../Core/NkSystem.h"

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <Windows.h>
#include <dwmapi.h>
#pragma comment(lib, "dwmapi.lib")
#pragma comment(lib, "uxtheme.lib")

namespace nkentseu
{

// ---------------------------------------------------------------------------
// Utilitaire : UTF-8 → WCHAR
// ---------------------------------------------------------------------------

static std::wstring NkUtf8ToWide(const std::string& s)
{
    if (s.empty()) return {};
    int len = MultiByteToWideChar(CP_UTF8, 0,
                                   s.c_str(), static_cast<int>(s.size()),
                                   nullptr, 0);
    std::wstring ws(static_cast<std::size_t>(len), L'\0');
    MultiByteToWideChar(CP_UTF8, 0,
                        s.c_str(), static_cast<int>(s.size()),
                        ws.data(), len);
    return ws;
}

static std::string NkWideToUtf8(const std::wstring& ws)
{
    if (ws.empty()) return {};
    int len = WideCharToMultiByte(CP_UTF8, 0,
                                   ws.c_str(), static_cast<int>(ws.size()),
                                   nullptr, 0, nullptr, nullptr);
    std::string s(static_cast<std::size_t>(len), '\0');
    WideCharToMultiByte(CP_UTF8, 0,
                        ws.c_str(), static_cast<int>(ws.size()),
                        s.data(), len, nullptr, nullptr);
    return s;
}

// ---------------------------------------------------------------------------

NkWin32WindowImpl::~NkWin32WindowImpl() { if (IsOpen()) Close(); }

// ---------------------------------------------------------------------------
// Create
// ---------------------------------------------------------------------------

bool NkWin32WindowImpl::Create(const NkWindowConfig& config)
{
    mConfig         = config;
    mData.hinstance = GetModuleHandle(nullptr);

    // Noms en WCHAR
    std::wstring wClassName = NkUtf8ToWide(config.name);
    std::wstring wTitle     = NkUtf8ToWide(config.title);

    // --- Styles ---
    if (config.fullscreen)
    {
        DEVMODE dm   = {};
        dm.dmSize    = sizeof(DEVMODE);
        dm.dmPelsWidth  = static_cast<DWORD>(GetSystemMetrics(SM_CXSCREEN));
        dm.dmPelsHeight = static_cast<DWORD>(GetSystemMetrics(SM_CYSCREEN));
        dm.dmBitsPerPel = 32;
        dm.dmFields  = DM_BITSPERPEL | DM_PELSWIDTH | DM_PELSHEIGHT;
        mData.dmScreen = dm;
        ChangeDisplaySettings(&mData.dmScreen, CDS_FULLSCREEN);
        mData.dwExStyle = WS_EX_APPWINDOW;
        mData.dwStyle   = WS_POPUP | WS_VISIBLE | WS_CLIPSIBLINGS | WS_CLIPCHILDREN;
    }
    else
    {
        mData.dwExStyle = WS_EX_APPWINDOW | WS_EX_WINDOWEDGE;
        mData.dwStyle   = config.frame
            ? WS_OVERLAPPEDWINDOW
            : (WS_POPUP | WS_THICKFRAME | WS_CAPTION |
               WS_SYSMENU | WS_MINIMIZEBOX | WS_MAXIMIZEBOX);
    }

    RECT rc = { config.x, config.y,
                config.x + static_cast<LONG>(config.width),
                config.y + static_cast<LONG>(config.height) };
    AdjustWindowRectEx(&rc, mData.dwStyle, FALSE, mData.dwExStyle);

    // --- Bootstrap EventImpl ---
    NkWin32EventImpl* ev =
        static_cast<NkWin32EventImpl*>(NkGetEventImpl());
    if (ev) ev->RegisterPending(this);

    // --- Enregistrement WCHAR de la classe ---
    WNDCLASSEXW wc  = {};
    wc.cbSize        = sizeof(WNDCLASSEXW);
    wc.style         = CS_HREDRAW | CS_VREDRAW | CS_DBLCLKS;
    wc.lpfnWndProc   = NkWin32EventImpl::WindowProcStatic;
    wc.hInstance     = mData.hinstance;
    wc.hIcon         = LoadIconW(nullptr, IDI_APPLICATION);
    wc.hCursor       = LoadCursorW(nullptr, IDC_ARROW);
    wc.hbrBackground = static_cast<HBRUSH>(GetStockObject(BLACK_BRUSH));
    wc.lpszClassName = wClassName.c_str();
    wc.hIconSm       = LoadIconW(nullptr, IDI_WINLOGO);
    RegisterClassExW(&wc); // peut échouer si déjà enregistrée

    // --- DPI awareness ---
    DPI_AWARENESS_CONTEXT prev =
        SetThreadDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);

    // --- Création Unicode ---
    mData.hwnd = CreateWindowExW(
        0,
        wClassName.c_str(),
        wTitle.c_str(),
        mData.dwStyle,
        0, 0,
        rc.right  - rc.left,
        rc.bottom - rc.top,
        nullptr, nullptr,
        mData.hinstance,
        nullptr);

    SetThreadDpiAwarenessContext(prev);

    if (!mData.hwnd)
    {
        mLastError = NkError(1, "CreateWindowExW failed (" +
                              std::to_string(::GetLastError()) + ")");
        return false;
    }

    // --- Centrage ---
    if (!config.fullscreen)
    {
        NkI32 sw = GetSystemMetrics(SM_CXSCREEN);
        NkI32 sh = GetSystemMetrics(SM_CYSCREEN);
        NkI32 ww = rc.right - rc.left, wh = rc.bottom - rc.top;
        if (config.centered)
            SetWindowPos(mData.hwnd, nullptr,
                         (sw-ww)/2, (sh-wh)/2, ww, wh, SWP_NOZORDER);
        else
            SetWindowPos(mData.hwnd, nullptr,
                         config.x, config.y, ww, wh, SWP_NOZORDER);
    }

    // --- DWM ombre ---
    BOOL ncr = TRUE;
    DwmSetWindowAttribute(mData.hwnd,
        DWMWA_NCRENDERING_ENABLED, &ncr, sizeof(ncr));
    const MARGINS shadow{1,1,1,1};
    DwmExtendFrameIntoClientArea(mData.hwnd, &shadow);

    // --- Taskbar ---
    CoCreateInstance(CLSID_TaskbarList, nullptr, CLSCTX_INPROC_SERVER,
                     IID_ITaskbarList3,
                     reinterpret_cast<void**>(&mData.taskbarList));

    if (config.visible)
    {
        ShowWindow(mData.hwnd, SW_SHOWNORMAL);
        SetForegroundWindow(mData.hwnd);
        SetFocus(mData.hwnd);
    }

    mData.isOpen = true;

    // Enregistrement final dans l'EventImpl (après HWND valide)
    if (ev) ev->Initialize(this, mData.hwnd);

    return true;
}

// ---------------------------------------------------------------------------
// Close
// ---------------------------------------------------------------------------

void NkWin32WindowImpl::Close()
{
    if (!mData.isOpen) return;

    NkWin32EventImpl* ev =
        static_cast<NkWin32EventImpl*>(NkGetEventImpl());
    if (ev) ev->Shutdown(mData.hwnd);

    if (mData.hwnd)
    {
        DestroyWindow(mData.hwnd);
        std::wstring wName = NkUtf8ToWide(mConfig.name);
        UnregisterClassW(wName.c_str(), mData.hinstance);
        mData.hwnd = nullptr;
    }
    if (mData.taskbarList)
    {
        mData.taskbarList->Release();
        mData.taskbarList = nullptr;
    }
    mData.isOpen = false;
}

// ---------------------------------------------------------------------------
// Propriétés
// ---------------------------------------------------------------------------

bool        NkWin32WindowImpl::IsOpen()       const { return mData.isOpen; }
NkError     NkWin32WindowImpl::GetLastError() const { return mLastError;   }

std::string NkWin32WindowImpl::GetTitle() const
{
    if (!mData.hwnd) return {};
    int len = GetWindowTextLengthW(mData.hwnd);
    if (len <= 0) return {};
    std::wstring ws(static_cast<std::size_t>(len+1), L'\0');
    GetWindowTextW(mData.hwnd, ws.data(), len+1);
    ws.resize(static_cast<std::size_t>(len));
    return NkWideToUtf8(ws);
}

void NkWin32WindowImpl::SetTitle(const std::string& t)
{
    mConfig.title = t;
    if (mData.hwnd)
        SetWindowTextW(mData.hwnd, NkUtf8ToWide(t).c_str());
}

NkVec2u NkWin32WindowImpl::GetSize() const
{
    RECT rc = {};
    if (mData.hwnd) GetClientRect(mData.hwnd, &rc);
    return { static_cast<NkU32>(rc.right - rc.left),
             static_cast<NkU32>(rc.bottom - rc.top) };
}

NkVec2u NkWin32WindowImpl::GetPosition() const
{
    RECT rc = {};
    if (mData.hwnd) GetWindowRect(mData.hwnd, &rc);
    return { static_cast<NkU32>(rc.left), static_cast<NkU32>(rc.top) };
}

float NkWin32WindowImpl::GetDpiScale() const
{
    return mData.hwnd
        ? static_cast<float>(GetDpiForWindow(mData.hwnd)) / USER_DEFAULT_SCREEN_DPI
        : 1.f;
}

NkVec2u NkWin32WindowImpl::GetDisplaySize() const
{
    return { static_cast<NkU32>(GetSystemMetrics(SM_CXSCREEN)),
             static_cast<NkU32>(GetSystemMetrics(SM_CYSCREEN)) };
}

NkVec2u NkWin32WindowImpl::GetDisplayPosition() const { return {0, 0}; }

// ---------------------------------------------------------------------------
// Manipulation
// ---------------------------------------------------------------------------

void NkWin32WindowImpl::SetSize(NkU32 w, NkU32 h)
{
    RECT rc = {0, 0, static_cast<LONG>(w), static_cast<LONG>(h)};
    AdjustWindowRectEx(&rc, mData.dwStyle, FALSE, mData.dwExStyle);
    SetWindowPos(mData.hwnd, nullptr, 0, 0,
                 rc.right - rc.left, rc.bottom - rc.top,
                 SWP_NOMOVE | SWP_NOZORDER);
}

void NkWin32WindowImpl::SetPosition(NkI32 x, NkI32 y)
{ SetWindowPos(mData.hwnd, nullptr, x, y, 0, 0, SWP_NOZORDER | SWP_NOSIZE); }

void NkWin32WindowImpl::SetVisible(bool v)
{ ShowWindow(mData.hwnd, v ? SW_SHOW : SW_HIDE); }

void NkWin32WindowImpl::Minimize()
{ ShowWindow(mData.hwnd, SW_MINIMIZE); }

void NkWin32WindowImpl::Maximize()
{ ShowWindow(mData.hwnd, IsZoomed(mData.hwnd) ? SW_RESTORE : SW_MAXIMIZE); }

void NkWin32WindowImpl::Restore()
{ ShowWindow(mData.hwnd, SW_RESTORE); }

void NkWin32WindowImpl::SetFullscreen(bool fs)
{
    if (fs)
    {
        SetWindowLongW(mData.hwnd, GWL_STYLE,
            WS_POPUP | WS_VISIBLE | WS_CLIPSIBLINGS | WS_CLIPCHILDREN);
        SetWindowPos(mData.hwnd, HWND_TOP,
            0, 0,
            GetSystemMetrics(SM_CXSCREEN),
            GetSystemMetrics(SM_CYSCREEN),
            SWP_FRAMECHANGED);
    }
    else
    {
        SetWindowLongW(mData.hwnd, GWL_STYLE,
            static_cast<LONG>(mData.dwStyle));
        SetWindowPos(mData.hwnd, nullptr,
            mConfig.x, mConfig.y,
            static_cast<int>(mConfig.width),
            static_cast<int>(mConfig.height),
            SWP_FRAMECHANGED | SWP_NOZORDER);
    }
    mConfig.fullscreen = fs;
}

void NkWin32WindowImpl::SetMousePosition(NkU32 x, NkU32 y)
{ SetCursorPos(static_cast<int>(x), static_cast<int>(y)); }

void NkWin32WindowImpl::ShowMouse(bool show)
{ ShowCursor(show ? TRUE : FALSE); }

void NkWin32WindowImpl::CaptureMouse(bool cap)
{ cap ? SetCapture(mData.hwnd) : ReleaseCapture(); }

void NkWin32WindowImpl::SetProgress(float progress)
{
    if (mData.taskbarList)
    {
        constexpr NkU32 kMax = 10000;
        mData.taskbarList->SetProgressValue(
            mData.hwnd,
            static_cast<ULONGLONG>(progress * kMax),
            kMax);
    }
}

// ---------------------------------------------------------------------------
// Surface
// ---------------------------------------------------------------------------

NkSurfaceDesc NkWin32WindowImpl::GetSurfaceDesc() const
{
    NkSurfaceDesc sd;
    auto sz      = GetSize();
    sd.width     = sz.x;
    sd.height    = sz.y;
    sd.dpi       = GetDpiScale();
    sd.hwnd      = mData.hwnd;
    sd.hinstance = mData.hinstance;
    return sd;
}

} // namespace nkentseu
