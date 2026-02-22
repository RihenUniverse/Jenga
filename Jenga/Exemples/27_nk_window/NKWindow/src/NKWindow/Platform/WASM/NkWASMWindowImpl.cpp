// =============================================================================
// NkWASMWindowImpl.cpp
// =============================================================================

#include "NkWASMWindowImpl.h"
#include "../../Core/NkSystem.h"

namespace nkentseu
{

bool NkWASMWindowImpl::Create(const NkWindowConfig& config, IEventImpl&)
{
    mConfig  = config;
    mBgColor = config.bgColor;
    emscripten_set_canvas_element_size("#canvas",
        static_cast<int>(config.width), static_cast<int>(config.height));
    SetTitle(config.title);
    mIsOpen = true;
    return true;
}

void NkWASMWindowImpl::SetTitle(const std::string& t)
{
    mConfig.title = t;
    EM_ASM({ document.title = UTF8ToString($0); }, t.c_str());
}

NkVec2u NkWASMWindowImpl::GetSize() const
{
    int w=0, h=0;
    emscripten_get_canvas_element_size("#canvas", &w, &h);
    return { static_cast<NkU32>(w), static_cast<NkU32>(h) };
}

float NkWASMWindowImpl::GetDpiScale() const
{
    return static_cast<float>(emscripten_get_device_pixel_ratio());
}

NkVec2u NkWASMWindowImpl::GetDisplaySize() const
{
    int w = EM_ASM_INT({ return window.screen.width; });
    int h = EM_ASM_INT({ return window.screen.height; });
    return { static_cast<NkU32>(w), static_cast<NkU32>(h) };
}

void NkWASMWindowImpl::SetSize(NkU32 w, NkU32 h)
{
    emscripten_set_canvas_element_size("#canvas",
        static_cast<int>(w), static_cast<int>(h));
}

void NkWASMWindowImpl::SetVisible(bool v)
{
    EM_ASM({
        var c = document.querySelector('#canvas');
        if(c) c.style.display = $0 ? '' : 'none';
    }, v ? 1 : 0);
}

void NkWASMWindowImpl::SetFullscreen(bool fs)
{
    if (fs)
    {
        EmscriptenFullscreenStrategy s{};
        s.scaleMode = EMSCRIPTEN_FULLSCREEN_SCALE_STRETCH;
        s.canvasResolutionScaleMode = EMSCRIPTEN_FULLSCREEN_CANVAS_SCALE_NONE;
        s.filteringMode  = EMSCRIPTEN_FULLSCREEN_FILTERING_DEFAULT;
        emscripten_enter_soft_fullscreen("#canvas", &s);
    }
    else
    {
        emscripten_exit_soft_fullscreen();
    }
    mConfig.fullscreen = fs;
}

void NkWASMWindowImpl::ShowMouse(bool show)
{
    EM_ASM({
        var c = document.querySelector('#canvas');
        if(c) c.style.cursor = $0 ? 'auto' : 'none';
    }, show ? 1 : 0);
}

void NkWASMWindowImpl::CaptureMouse(bool cap)
{
    if (cap)
        emscripten_request_pointerlock("#canvas", 1);
    else
        emscripten_exit_pointerlock();
}

NkSurfaceDesc NkWASMWindowImpl::GetSurfaceDesc() const
{
    NkSurfaceDesc sd;
    auto sz   = GetSize();
    sd.width  = sz.x;
    sd.height = sz.y;
    sd.canvasId = "#canvas";
    return sd;
}

void NkWASMWindowImpl::BlitSoftwareFramebuffer(const NkU8* rgba8, NkU32 w, NkU32 h)
{
    if (!rgba8) return;
    EM_ASM({
        var c = document.querySelector('#canvas');
        if (!c) return;
        var ctx = c.getContext('2d');
        if (!ctx) return;
        var imgData = ctx.createImageData($1, $2);
        var src = new Uint8Array(Module.HEAPU8.buffer, $0, $1 * $2 * 4);
        imgData.data.set(src);
        ctx.putImageData(imgData, 0, 0);
    }, rgba8, w, h);
}

} // namespace nkentseu
