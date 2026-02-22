#pragma once

// =============================================================================
// NkWindow.h
// Classe publique Window — façade PIMPL vers IWindowImpl.
//
// Usage simplifié (avec NkInitialise) :
//   nkentseu::NkInitialise();
//
//   nkentseu::NkWindowConfig cfg;
//   cfg.title = "Hello NkWindow";
//   nkentseu::Window window(cfg);
//   if (!window.IsOpen()) { /* erreur */ }
//
//   nkentseu::Renderer renderer(window);
//   while (window.IsOpen()) {
//       nkentseu::EventSystem::Instance().PollEvents();
//       renderer.BeginFrame(0x141414FF);
//       // draw...
//       renderer.EndFrame();
//       renderer.Present();
//   }
//   nkentseu::NkClose();
// =============================================================================

#include "NkWindowConfig.h"
#include "NkSafeArea.h"
#include "NkSurface.h"
#include "NkEvent.h"
#include "IWindowImpl.h"
#include "NkSystem.h"
#include <memory>
#include <string>

namespace nkentseu
{

class IEventImpl;

// ---------------------------------------------------------------------------
// Window
// ---------------------------------------------------------------------------

class Window
{
public:
    // --- Construction ---

    Window();
    explicit Window(const NkWindowConfig& config);
    ~Window();

    Window(const Window&)            = delete;
    Window& operator=(const Window&) = delete;
    Window(Window&&)                 = default;
    Window& operator=(Window&&)      = default;

    // --- Cycle de vie ---

    /**
     * Crée la fenêtre. NkInitialise() doit avoir été appelé avant.
     * Utilise automatiquement l'IEventImpl fourni par NkSystem.
     */
    bool Create(const NkWindowConfig& config);
    void Close();
    bool IsOpen()  const;
    bool IsValid() const;

    // --- Propriétés ---

    std::string    GetTitle()           const;
    void           SetTitle(const std::string& title);
    NkVec2u        GetSize()            const;
    NkVec2u        GetPosition()        const;
    float          GetDpiScale()        const;
    NkVec2u        GetDisplaySize()     const;
    NkVec2u        GetDisplayPosition() const;
    NkError        GetLastError()       const;
    NkWindowConfig GetConfig()          const;

    // --- Manipulation ---

    void SetSize(NkU32 width, NkU32 height);
    void SetPosition(NkI32 x, NkI32 y);
    void SetVisible(bool visible);
    void Minimize();
    void Maximize();
    void Restore();
    void SetFullscreen(bool fullscreen);

    // --- Souris ---

    void SetMousePosition(NkU32 x, NkU32 y);
    void ShowMouse(bool show);
    void CaptureMouse(bool capture);

    // --- OS extras ---

    void SetProgress(float progress); ///< Progression barre des tâches

    // --- Safe Area (mobile) ---

    /**
     * @brief Retourne les insets de la zone sécurisée.
     * Sur desktop : tout à 0. Sur mobile : notch, home indicator…
     * Utiliser avec NkWindowConfig::respectSafeArea = true.
     */
    NkSafeAreaInsets GetSafeAreaInsets() const;

    // --- Surface graphique (pour Renderer) ---

    NkSurfaceDesc GetSurfaceDesc() const;

    // --- Safe area (mobile) ---

    /**
     * @brief Retourne les marges de zone sûre de la fenêtre.
     * Sur desktop : retourne {0,0,0,0}.  Appelable à tout moment.
     */
    NkSafeAreaInsets GetSafeAreaInsets() const;

    // --- Callback événements (délégué à l'EventImpl) ---

    /**
     * Enregistre un callback pour les événements de CETTE fenêtre uniquement.
     * Délégué à IEventImpl::SetWindowCallback().
     */
    void SetEventCallback(NkEventCallback callback);

    // --- Accès impl interne ---

    IWindowImpl*       GetImpl()       { return mImpl.get(); }
    const IWindowImpl* GetImpl() const { return mImpl.get(); }

private:
    std::unique_ptr<IWindowImpl> mImpl;
    NkWindowConfig               mConfig;
};

} // namespace nkentseu
