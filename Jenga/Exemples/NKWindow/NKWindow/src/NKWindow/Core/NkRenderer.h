#pragma once

// =============================================================================
// NkNkRenderer.h
// Classe publique NkRenderer — façade PIMPL vers INkRendererImpl.
//
// Usage :
//   nkentseu::NkInitialise();
//   nkentseu::Window window(cfg);
//
//   nkentseu::NkNkRendererConfig rcfg;
//   rcfg.api = nkentseu::NkNkRendererApi::NK_SOFTWARE;
//   nkentseu::NkRenderer NkRenderer(window, rcfg);
//   NkRenderer.SetBackgroundColor(0x141414FF);
//
//   while (window.IsOpen()) {
//       nkentseu::EventSystem::Instance().PollEvents();
//       NkRenderer.BeginFrame();
//       NkRenderer.FillCircle(cx, cy, 30, NkRenderer.PackColor(255,100,50));
//       NkRenderer.EndFrame();
//       NkRenderer.Present();
//   }
// =============================================================================

#include "NkSurface.h"
#include "NkTypes.h"
#include <memory>
#include <string>
#include <vector>

namespace nkentseu
{

class Window;
class INkRendererImpl;

// ---------------------------------------------------------------------------
// NkRenderTexture - cible de rendu CPU offscreen (RGBA8)
// ---------------------------------------------------------------------------

struct NkRenderTexture
{
    NkU32              width  = 0;
    NkU32              height = 0;
    NkU32              pitch  = 0; // bytes per row
    std::vector<NkU8>  pixels;
};

// ---------------------------------------------------------------------------
// NkRenderer
// ---------------------------------------------------------------------------

class NkRenderer
{
public:
    NkRenderer();
    NkRenderer(Window& window, const NkRendererConfig& config = {});
    ~NkRenderer();

    NkRenderer(const NkRenderer&)            = delete;
    NkRenderer& operator=(const NkRenderer&) = delete;

    // --- Cycle de vie ---

    bool Create(Window& window, const NkRendererConfig& config = {});
    void Shutdown();
    bool IsValid() const;

    // --- Informations ---

    NkRendererApi GetApi()                const;
    std::string   GetApiName()            const;
    bool          IsHardwareAccelerated() const;
    NkError       GetLastError()          const;

    const NkFramebufferInfo& GetFramebufferInfo() const;

    // --- Couleur de fond (anciennement dans Window) ---

    void  SetBackgroundColor(NkU32 rgba);
    NkU32 GetBackgroundColor() const;

    // --- Trame ---

    void BeginFrame(NkU32 clearColor = 0xFFFFFFFF); ///< 0xFFFFFFFF → utilise bgColor
    void EndFrame();
    void Present();
    void Resize(NkU32 width, NkU32 height);

    // --- Sortie ---

    /**
     * @brief Active/désactive la présentation vers la fenêtre.
     *        Si désactivé, le renderer peut fonctionner en offscreen.
     */
    void SetWindowPresentEnabled(bool enabled);
    bool IsWindowPresentEnabled() const;

    /**
     * @brief Cible offscreen optionnelle (copie du framebuffer CPU à chaque Present()).
     *        Utile pour préparer un pipeline "render-to-texture".
     */
    void SetExternalRenderTarget(NkRenderTexture* target);
    NkRenderTexture* GetExternalRenderTarget() const;
    bool ResolveToExternalRenderTarget();

    // --- Utilitaires couleur ---

    static NkU32 PackColor(NkU8 r, NkU8 g, NkU8 b, NkU8 a = 255);
    static void  UnpackColor(NkU32 rgba, NkU8& r, NkU8& g, NkU8& b, NkU8& a);

    // --- Primitives 2D (Software + stubs pour les autres) ---

    void SetPixel     (NkI32 x, NkI32 y, NkU32 rgba);
    void DrawPixel    (NkI32 x, NkI32 y, NkU32 rgba);

    // --- Accès impl ---

    INkRendererImpl*       GetImpl()       { return mImpl.get(); }
    const INkRendererImpl* GetImpl() const { return mImpl.get(); }

private:
    std::unique_ptr<INkRendererImpl> mImpl;
    Window*                        mWindow     = nullptr;
    NkRenderTexture*               mExternalTarget = nullptr;
    bool                           mWindowPresentEnabled = true;
    NkRendererConfig               mConfig;
};

// Backward-compatible alias kept for existing examples.
using Renderer = NkRenderer;

} // namespace nkentseu
