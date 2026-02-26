// =============================================================================
// Sandbox/src/main.cpp
// Exemple complet NkWindow — fenêtre, renderer software, events, gamepad,
// safe area, transforms 2D.
//
// Compile sur : Win32, macOS Cocoa, Linux XCB/XLib, WASM, Android*, iOS*
// (*) Adapter l'entry point via NkMain.h
// =============================================================================

#include "NKWindow/NkWindow.h"
#include "NKWindow/Core/NkMain.h"
#include <cstdio>

#if defined(NKENTSEU_PLATFORM_WASM) && defined(__EMSCRIPTEN__)
#   include <emscripten.h>
#endif

// --------------------------------------------------------------------------
// nkmain — point d'entrée cross-platform
// --------------------------------------------------------------------------

int nkmain(const nkentseu::NkEntryState& /*state*/)
{
    using namespace nkentseu;

    // ========================================================================
    // 1. Initialisation du framework
    // ========================================================================

    NkAppData app;
    app.appName           = "NkWindow Sandbox";
    app.preferredRenderer = NkRendererApi::NK_SOFTWARE;

    if (!NkInitialise(app))
        return -1;

    // ========================================================================
    // 2. Fenêtre principale
    // ========================================================================

    NkWindowConfig cfg;
    cfg.title   = "NkWindow Sandbox";
    cfg.width   = 1280;
    cfg.height  = 720;
    cfg.centered = true;
    cfg.resizable    = true;
    cfg.dropEnabled  = true;  // Activer le drag & drop

    nkentseu::Window window(cfg);
    if (!window.IsOpen())
    {
        std::fprintf(stderr, "[Sandbox] Window creation failed: %s\n", window.GetLastError().ToString().c_str());
        return -2;
    }

    // Safe area (utile sur mobile)
    NkSafeAreaInsets safeArea = window.GetSafeAreaInsets();

    // ========================================================================
    // 3. Renderer
    // ========================================================================

    NkRendererConfig rcfg;
    rcfg.api = NkRendererApi::NK_SOFTWARE;
    rcfg.autoResizeFramebuffer = true; // framebuffer suit la fenêtre automatiquement

    Renderer renderer(window, rcfg);
    if (!renderer.IsValid())
        return -3;

    renderer.SetBackgroundColor(Renderer::PackColor(20, 20, 30));

    // ========================================================================
    // 4. Système d'événements
    // ========================================================================

    auto& es = EventSystem::Instance();
    bool  running = true;

    // ========================================================================
    // 5. Système gamepad
    // ========================================================================

    auto& gp = NkGamepads();

    gp.SetConnectCallback([](const NkGamepadInfo& info, bool connected)
    {
        // En production : afficher un message
        (void)info; (void)connected;
    });

    gp.SetButtonCallback([](NkU32 /*idx*/, NkGamepadButton btn, NkButtonState st)
    {
        if (btn == NkGamepadButton::NK_GP_SOUTH && st == NkButtonState::NK_PRESSED)
        {
            // A/Cross pressé
        }
    });

    gp.SetAxisCallback([](NkU32 /*idx*/, NkGamepadAxis ax, float value)
    {
        (void)ax; (void)value;
        // Traiter les axes (sticks, gâchettes)
    });

    // ========================================================================
    // 6. Transforms 2D
    // ========================================================================

    NkTransform2D spinnerTransform;
    spinnerTransform.position = {
        static_cast<float>(cfg.width)  / 2.f,
        static_cast<float>(cfg.height) / 2.f
    };
    spinnerTransform.scale = { 1.f, 1.f };

    float angle = 0.f; // degrés, incrémenté chaque trame

    // Caméra 2D utilisée pour le view matrix (shake + pan/zoom possibles)
    NkCamera2D camera(cfg.width, cfg.height);
    camera.SetPosition(
        static_cast<float>(cfg.width) * 0.5f,
        static_cast<float>(cfg.height) * 0.5f
    );

    // ========================================================================
    // 7. Boucle principale
    // ========================================================================

#if defined(NKENTSEU_PLATFORM_NOOP)
    int headlessFrames = 2;
#endif

    while (running && window.IsOpen())
    {
#if defined(NKENTSEU_PLATFORM_NOOP)
        if (--headlessFrames <= 0)
        {
            window.Close();
            running = false;
        }
#endif
        // --- Événements ---
        while (NkEvent* event = es.PollEvent())
        {
            if (auto* e = event->As<NkWindowCloseEvent>())
            {
                (void)e;
                window.Close();
                running = false;
                continue;
            }

            if (auto* e = event->As<NkWindowResizeEvent>())
            {
                renderer.Resize(e->GetWidth(), e->GetHeight());
                continue;
            }

            if (auto* e = event->As<NkKeyEvent>())
            {
                if (!e->IsPress())
                    continue;

                if (e->GetKey() == NkKey::NK_ESCAPE)
                {
                    window.Close();
                    running = false;
                }
                else if (e->GetKey() == NkKey::NK_F11)
                {
                    window.SetFullscreen(!window.GetConfig().fullscreen);
                }
            }
        }
        if (!window.IsOpen())
        {
            running = false;
            break;
        }

        // --- Gamepad polling ---
        gp.PollGamepads();

        // Déplacement avec stick gauche (joueur 0)
        if (gp.IsConnected(0))
        {
            float lx = gp.GetAxis(0, NkGamepadAxis::NK_GP_AXIS_LX);
            float ly = gp.GetAxis(0, NkGamepadAxis::NK_GP_AXIS_LY);
            spinnerTransform.position.x += lx * 4.f;
            spinnerTransform.position.y += ly * 4.f;

            // Vibration si bouton A
            if (gp.IsButtonDown(0, NkGamepadButton::NK_GP_SOUTH))
                gp.Rumble(0, 0.3f, 0.3f, 0.f, 0.f, 16);
        }

        // --- Mise à jour ---
        angle += 1.5f;
        if (angle >= 360.f) angle -= 360.f;
        spinnerTransform.rotation = angle;

        // --- Rendu ---
        // Mise à jour caméra shake
        camera.Update(1.f / 60.f);  // dt fixe pour l'exemple

        renderer.BeginFrame(); // utilise SetBackgroundColor

        renderer.EndFrame();
        renderer.Present(); // blit vers la fenêtre

#if defined(NKENTSEU_PLATFORM_WASM) && defined(__EMSCRIPTEN__)
        // Yield to the browser for ~16 ms (≈60 fps) so the compositor has
        // time to paint the canvas before the next frame starts.
        emscripten_sleep(16);
#endif
    }

    // ========================================================================
    // 8. Nettoyage
    // ========================================================================

    renderer.Shutdown();
    NkClose();
    return 0;
}
