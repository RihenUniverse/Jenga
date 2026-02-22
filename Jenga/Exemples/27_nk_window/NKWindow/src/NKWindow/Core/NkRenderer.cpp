// =============================================================================
// NkRenderer.cpp
// Implémentation de la façade Renderer.
// =============================================================================

#include "NkRenderer.h"
#include "NkWindow.h"
#include "IRendererImpl.h"
#include "../Renderer/Software/NkSoftwareRendererImpl.h"
#include "../Renderer/NkRendererStubs.h"

#include <cmath>
#include <algorithm>
#include <stdexcept>

namespace nkentseu
{

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

static std::unique_ptr<INkRendererImpl> CreateRendererImpl(NkRendererApi api)
{
    switch (api)
    {
    case NkRendererApi::NK_SOFTWARE:  return std::make_unique<NkSoftwareRendererImpl>();
    case NkRendererApi::NK_VULKAN:    return std::make_unique<NkVulkanRendererImpl>();
    case NkRendererApi::NK_OPENGL:    return std::make_unique<NkOpenGLRendererImpl>();
    case NkRendererApi::NK_DIRECTX11: return std::make_unique<NkDX11RendererImpl>();
    case NkRendererApi::NK_DIRECTX12: return std::make_unique<NkDX12RendererImpl>();
    case NkRendererApi::NK_METAL:     return std::make_unique<NkMetalRendererImpl>();
    default:                          return std::make_unique<NkSoftwareRendererImpl>();
    }
}

// ---------------------------------------------------------------------------
// Construction
// ---------------------------------------------------------------------------

NkRenderer::NkRenderer()
    : mImpl(std::make_unique<NkSoftwareRendererImpl>())
{}

NkRenderer::NkRenderer(Window& window, const NkRendererConfig& config)
    : mImpl(CreateRendererImpl(config.api))
    , mWindow(&window)
{
    Create(window, config);
}

NkRenderer::~NkRenderer() { Shutdown(); }

bool NkRenderer::Create(Window& window, const NkRendererConfig& config)
{
    mWindow = &window;
    mImpl   = CreateRendererImpl(config.api);
    return mImpl->Init(config, window.GetSurfaceDesc());
}

void NkRenderer::Shutdown()      { if (mImpl) mImpl->Shutdown(); }
bool NkRenderer::IsValid() const { return mImpl && mImpl->IsValid(); }

// ---------------------------------------------------------------------------
// Informations
// ---------------------------------------------------------------------------

NkRendererApi NkRenderer::GetApi()                const { return mImpl ? mImpl->GetApi()     : NkRendererApi::NK_NONE; }
std::string   NkRenderer::GetApiName()            const { return mImpl ? mImpl->GetApiName() : "None"; }
bool          NkRenderer::IsHardwareAccelerated() const { return mImpl && mImpl->IsHardwareAccelerated(); }
NkError       NkRenderer::GetLastError()          const { return mImpl ? mImpl->GetLastError() : NkError::Ok(); }

const NkFramebufferInfo& NkRenderer::GetFramebufferInfo() const
{
    static NkFramebufferInfo sDummy;
    return mImpl ? mImpl->GetFramebufferInfo() : sDummy;
}

// ---------------------------------------------------------------------------
// Couleur de fond
// ---------------------------------------------------------------------------

void  NkRenderer::SetBackgroundColor(NkU32 rgba)
{ if (mImpl) mImpl->SetBackgroundColor(rgba); }

NkU32 NkRenderer::GetBackgroundColor() const
{ return mImpl ? mImpl->GetBackgroundColor() : 0x141414FF; }

// ---------------------------------------------------------------------------
// Trame
// ---------------------------------------------------------------------------

void NkRenderer::BeginFrame(NkU32 clearColor)
{
    if (!mImpl) return;
    // 0xFFFFFFFF est la sentinelle "utilise bgColor"
    NkU32 color = (clearColor == 0xFFFFFFFF)
                ? mImpl->GetBackgroundColor()
                : clearColor;
    mImpl->BeginFrame(color);
}

void NkRenderer::EndFrame()   { if (mImpl) mImpl->EndFrame(); }

void NkRenderer::Present()
{
    if (!mImpl || !mWindow) return;
    mImpl->Present(mWindow->GetSurfaceDesc());
}

void NkRenderer::Resize(NkU32 w, NkU32 h)
{
    if (mImpl) mImpl->Resize(w, h);
}

// ---------------------------------------------------------------------------
// Couleur utilitaires
// ---------------------------------------------------------------------------

NkU32 NkRenderer::PackColor(NkU8 r, NkU8 g, NkU8 b, NkU8 a)
{ return (static_cast<NkU32>(r)<<24)|(static_cast<NkU32>(g)<<16)|
         (static_cast<NkU32>(b)<<8) | a; }

void NkRenderer::UnpackColor(NkU32 rgba, NkU8& r, NkU8& g, NkU8& b, NkU8& a)
{ r=(rgba>>24)&0xFF; g=(rgba>>16)&0xFF; b=(rgba>>8)&0xFF; a=rgba&0xFF; }

// ---------------------------------------------------------------------------
// Transformation 2D
// ---------------------------------------------------------------------------

void NkRenderer::SetTransform(const NkTransform2D& t)
{ mTransform = t; mUseTransform = true; }

void NkRenderer::ResetTransform()
{ mTransform.Reset(); mUseTransform = false; }

const NkTransform2D& NkRenderer::GetTransform() const { return mTransform; }

// ---------------------------------------------------------------------------
// Primitives de base
// ---------------------------------------------------------------------------

void NkRenderer::SetPixel(NkI32 x, NkI32 y, NkU32 rgba)
{ if (mImpl) mImpl->SetPixel(x, y, rgba); }

void NkRenderer::DrawPixel(NkI32 x, NkI32 y, NkU32 rgba)
{ SetPixel(x, y, rgba); }

void NkRenderer::DrawLine(NkI32 x0, NkI32 y0, NkI32 x1, NkI32 y1, NkU32 rgba)
{
    if (!mImpl) return;
    NkI32 dx = std::abs(x1-x0), dy = std::abs(y1-y0);
    NkI32 sx = (x0 < x1) ? 1 : -1;
    NkI32 sy = (y0 < y1) ? 1 : -1;
    NkI32 err = dx - dy;
    while (true)
    {
        mImpl->SetPixel(x0, y0, rgba);
        if (x0 == x1 && y0 == y1) break;
        NkI32 e2 = 2 * err;
        if (e2 > -dy) { err -= dy; x0 += sx; }
        if (e2 <  dx) { err += dx; y0 += sy; }
    }
}

void NkRenderer::DrawRect(NkI32 x, NkI32 y, NkU32 w, NkU32 h, NkU32 rgba)
{
    DrawLine(x,     y,     x+w-1, y,     rgba);
    DrawLine(x+w-1, y,     x+w-1, y+h-1, rgba);
    DrawLine(x+w-1, y+h-1, x,     y+h-1, rgba);
    DrawLine(x,     y+h-1, x,     y,     rgba);
}

void NkRenderer::FillRect(NkI32 x, NkI32 y, NkU32 w, NkU32 h, NkU32 rgba)
{
    if (!mImpl) return;
    for (NkU32 row = 0; row < h; ++row)
        for (NkU32 col = 0; col < w; ++col)
            mImpl->SetPixel(x + static_cast<NkI32>(col),
                            y + static_cast<NkI32>(row), rgba);
}

void NkRenderer::DrawCircle(NkI32 cx, NkI32 cy, NkI32 r, NkU32 rgba)
{
    if (!mImpl) return;
    NkI32 x = r, y = 0, err = 0;
    while (x >= y)
    {
        mImpl->SetPixel(cx+x, cy+y, rgba); mImpl->SetPixel(cx+y, cy+x, rgba);
        mImpl->SetPixel(cx-y, cy+x, rgba); mImpl->SetPixel(cx-x, cy+y, rgba);
        mImpl->SetPixel(cx-x, cy-y, rgba); mImpl->SetPixel(cx-y, cy-x, rgba);
        mImpl->SetPixel(cx+y, cy-x, rgba); mImpl->SetPixel(cx+x, cy-y, rgba);
        if (err <= 0) { ++y; err += 2*y + 1; }
        if (err >  0) { --x; err -= 2*x + 1; }
    }
}

void NkRenderer::FillCircle(NkI32 cx, NkI32 cy, NkI32 r, NkU32 rgba)
{
    if (!mImpl || r <= 0) return;
    NkI32 x = r, y = 0, err = 0;
    while (x >= y)
    {
        for (NkI32 i = cx-x; i <= cx+x; ++i)
        { mImpl->SetPixel(i, cy+y, rgba); mImpl->SetPixel(i, cy-y, rgba); }
        for (NkI32 i = cx-y; i <= cx+y; ++i)
        { mImpl->SetPixel(i, cy+x, rgba); mImpl->SetPixel(i, cy-x, rgba); }
        if (err <= 0) { ++y; err += 2*y + 1; }
        if (err >  0) { --x; err -= 2*x + 1; }
    }
}

void NkRenderer::FillTriangle(
    NkI32 x0, NkI32 y0, NkI32 x1, NkI32 y1, NkI32 x2, NkI32 y2, NkU32 rgba)
{
    // Tri par Y croissant
    auto Sort = [](NkI32& ax,NkI32& ay,NkI32& bx,NkI32& by)
    { if (ay > by){ std::swap(ax,bx); std::swap(ay,by); } };
    Sort(x0,y0,x1,y1); Sort(x0,y0,x2,y2); Sort(x1,y1,x2,y2);

    auto Interp = [](NkI32 ya, NkI32 yb, NkI32 xa, NkI32 xb, NkI32 y) -> NkI32
    {
        if (yb == ya) return xa;
        return xa + (xb - xa) * (y - ya) / (yb - ya);
    };

    for (NkI32 y = y0; y <= y2; ++y)
    {
        NkI32 xa = (y <= y1)
            ? Interp(y0, y1, x0, x1, y)
            : Interp(y1, y2, x1, x2, y);
        NkI32 xb = Interp(y0, y2, x0, x2, y);
        if (xa > xb) std::swap(xa, xb);
        for (NkI32 xi = xa; xi <= xb; ++xi)
            mImpl->SetPixel(xi, y, rgba);
    }
}

// ---------------------------------------------------------------------------
// Primitives transformées
// ---------------------------------------------------------------------------

void NkRenderer::DrawLineTransformed(NkVec2f p0, NkVec2f p1, NkU32 rgba)
{
    NkMat3f mat = mTransform.GetMatrix();
    NkVec2f wp0 = mat.TransformPoint(p0);
    NkVec2f wp1 = mat.TransformPoint(p1);
    DrawLine(static_cast<NkI32>(wp0.x), static_cast<NkI32>(wp0.y),
             static_cast<NkI32>(wp1.x), static_cast<NkI32>(wp1.y), rgba);
}

void NkRenderer::FillRectTransformed(NkVec2f origin, float w, float h, NkU32 rgba)
{
    // Transforme les 4 coins et dessine 2 triangles
    NkMat3f mat = mTransform.GetMatrix();
    NkVec2f tl = mat.TransformPoint(origin);
    NkVec2f tr = mat.TransformPoint({origin.x + w, origin.y});
    NkVec2f br = mat.TransformPoint({origin.x + w, origin.y + h});
    NkVec2f bl = mat.TransformPoint({origin.x,     origin.y + h});

    auto Pi = [](NkVec2f v){ return std::make_pair(
        static_cast<NkI32>(v.x), static_cast<NkI32>(v.y)); };
    auto [tlx,tly] = Pi(tl); auto [trx,try_] = Pi(tr);
    auto [brx,bry] = Pi(br); auto [blx,bly]  = Pi(bl);
    FillTriangle(tlx,tly, trx,try_, brx,bry, rgba);
    FillTriangle(tlx,tly, brx,bry,  blx,bly, rgba);
}

void NkRenderer::FillTriangleTransformed(
    NkVec2f p0, NkVec2f p1, NkVec2f p2, NkU32 rgba)
{
    NkMat3f mat = mTransform.GetMatrix();
    NkVec2f wp0 = mat.TransformPoint(p0);
    NkVec2f wp1 = mat.TransformPoint(p1);
    NkVec2f wp2 = mat.TransformPoint(p2);
    FillTriangle(
        static_cast<NkI32>(wp0.x), static_cast<NkI32>(wp0.y),
        static_cast<NkI32>(wp1.x), static_cast<NkI32>(wp1.y),
        static_cast<NkI32>(wp2.x), static_cast<NkI32>(wp2.y), rgba);
}


// ---------------------------------------------------------------------------
// Camera 2D
// ---------------------------------------------------------------------------

void NkRenderer::SetViewMatrix(const NkMat3f& viewMatrix)
{
    // mViewMatrix = viewMatrix;
    // mUseCamera  = true;
}

void NkRenderer::ResetViewMatrix()
{
    // mViewMatrix = NkMat3f::Identity();
    // mUseCamera  = false;
}

} // namespace nkentseu
