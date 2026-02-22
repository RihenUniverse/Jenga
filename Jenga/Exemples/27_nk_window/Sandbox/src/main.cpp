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

    Window window(cfg);
    if (!window.IsOpen())
        return -2;

    // Safe area (utile sur mobile)
    NkSafeAreaInsets safeArea = window.GetSafeAreaInsets();

    // ========================================================================
    // 3. Renderer
    // ========================================================================

    NkRendererConfig rcfg;
    rcfg.api = NkRendererApi::NK_SOFTWARE;

    Renderer renderer(window, rcfg);
    if (!renderer.IsValid())
        return -3;

    renderer.SetBackgroundColor(Renderer::PackColor(20, 20, 30));

    // ========================================================================
    // 4. Système d'événements
    // ========================================================================

    auto& es = EventSystem::Instance();
    bool  running = true;

    // Fermeture fenêtre
    es.SetEventCallback<NkWindowCloseEvent>([&](NkWindowCloseEvent*)
    {
        window.Close();
        running = false;
    });

    // Touche Échap → quitter
    es.SetEventCallback<NkKeyEvent>([&](NkKeyEvent* ev)
    {
        if (ev->IsPress() && ev->GetKey() == NkKey::NK_ESCAPE)
        {
            window.Close();
            running = false;
        }
        if (ev->IsPress() && ev->GetKey() == NkKey::NK_F11)
            window.SetFullscreen(!window.GetConfig().fullscreen);
    });

    // Redimensionnement
    es.SetEventCallback<NkWindowResizeEvent>([&](NkWindowResizeEvent* ev)
    {
        renderer.Resize(ev->GetWidth(), ev->GetHeight());
    });

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

    // ========================================================================
    // 7. Boucle principale
    // ========================================================================

    while (running && window.IsOpen())
    {
        // --- Événements ---
        es.PollEvents();

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
        renderer.SetViewMatrix(camera.GetViewMatrix());

        renderer.BeginFrame(); // utilise SetBackgroundColor

        // Fond dégradé (quelques rectangles)
        for (NkU32 row = 0; row < 8; ++row)
        {
            NkU32 y = row * (cfg.height / 8);
            NkU32 h = cfg.height / 8;
            NkU8  b = static_cast<NkU8>(20 + row * 5);
            renderer.FillRect(0, static_cast<NkI32>(y),
                              cfg.width, h,
                              Renderer::PackColor(15, 15, b));
        }

        // Grille de points
        for (NkI32 gx = 40; gx < static_cast<NkI32>(cfg.width);  gx += 40)
        for (NkI32 gy = 40; gy < static_cast<NkI32>(cfg.height); gy += 40)
            renderer.SetPixel(gx, gy, Renderer::PackColor(60, 60, 80));

        // Cercle fixe (blanc)
        renderer.DrawCircle(200, 200, 60,
                            Renderer::PackColor(200, 200, 200));

        // Triangle rempli (cyan)
        renderer.FillTriangle(100, 400, 200, 300, 300, 450,
                              Renderer::PackColor(0, 200, 200));

        // --- Objet tournant (transform) ---
        renderer.SetTransform(spinnerTransform);

        // Carré centré sur l'origine, tournant autour de son centre
        renderer.FillRectTransformed({-60.f, -60.f}, 120.f, 120.f,
                                     Renderer::PackColor(255, 100, 50));

        // Diagonale à travers le carré
        renderer.DrawLineTransformed({-60.f, -60.f}, {60.f, 60.f},
                                     Renderer::PackColor(255, 255, 100));

        // Triangle interne
        renderer.FillTriangleTransformed(
            {0.f, -50.f}, {-43.f, 25.f}, {43.f, 25.f},
            Renderer::PackColor(50, 255, 100, 200));

        renderer.ResetTransform();

        // --- Cercle manette (si connectée) ---
        if (gp.IsConnected(0))
        {
            renderer.FillCircle(static_cast<NkI32>(cfg.width) - 40, 40, 12,
                                Renderer::PackColor(50, 220, 50));
        }
        else
        {
            renderer.DrawCircle(static_cast<NkI32>(cfg.width) - 40, 40, 12,
                                Renderer::PackColor(120, 120, 120));
        }

        // --- Safe area (overlay debug sur mobile) ---
        if (!safeArea.IsZero())
        {
            NkU32 w = window.GetSize().x;
            NkU32 h = window.GetSize().y;
            NkU32 col = Renderer::PackColor(255, 255, 0, 80);
            // Ligne basse safe area
            renderer.DrawLine(0, static_cast<NkI32>(h - safeArea.bottom),
                              static_cast<NkI32>(w), static_cast<NkI32>(h - safeArea.bottom),
                              col);
            // Ligne haute
            renderer.DrawLine(0, static_cast<NkI32>(safeArea.top),
                              static_cast<NkI32>(w), static_cast<NkI32>(safeArea.top), col);
        }

        renderer.ResetViewMatrix();  // Sortir du mode caméra pour l'UI

        renderer.EndFrame();
        renderer.Present(); // blit vers la fenêtre
    }

    // ========================================================================
    // 8. Nettoyage
    // ========================================================================

    renderer.Shutdown();
    NkClose();
    return 0;
}
