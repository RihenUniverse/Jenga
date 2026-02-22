// =============================================================================
// camera_example.cpp — Exemple complet du système de capture caméra NkWindow
//
// Démontre :
//   1. Énumération des caméras disponibles
//   2. Streaming webcam → rendu logiciel en temps réel (preview)
//   3. Capture photo → sauvegarde PNG
//   4. Enregistrement vidéo → MP4 (Win32/macOS) ou WebM (WASM)
//   5. Contrôles : zoom, torche, focus point
//   6. Conversion de format : NV12/YUV420 → RGBA8 pour le rendu
// =============================================================================

#include <NkWindow/NkWindow.h>
#include <NkWindow/Core/NkMain.h>

using namespace nkentseu;

int nkmain(const NkEntryState& state)
{
    // =========================================================================
    // 1. Initialiser le framework (initialise aussi NkCameraSystem)
    // =========================================================================
    NkAppData app;
    app.appName           = "NkWindow Camera Example";
    app.preferredRenderer = NkRendererApi::NK_SOFTWARE;
    NkInitialise(app);

    // =========================================================================
    // 2. Fenêtre
    // =========================================================================
    NkWindowConfig wCfg;
    wCfg.title  = "Camera Preview — NkWindow";
    wCfg.width  = 1280;
    wCfg.height = 720;
    Window window(wCfg);

    Renderer renderer(window);
    renderer.SetBackgroundColor(0x111111FF);

    // =========================================================================
    // 3. Énumérer les caméras
    // =========================================================================
    auto& cam     = NkCamera();          // NkCameraSystem::Instance()
    auto  devices = cam.EnumerateDevices();

    if (devices.empty())
    {
        // Pas de caméra — afficher message et quitter
        auto& es = EventSystem::Instance();
        while (window.IsOpen()) {
            es.PollEvents();
            renderer.BeginFrame();
            // Dessiner texte "No camera found" via primitives
            for (NkU32 i = 0; i < 20; ++i)
                renderer.DrawLine(640 - 100 + i, 360, 640 + 100 - i, 360, 0xFF4444FF);
            renderer.EndFrame();
            renderer.Present();
        }
        NkClose();
        return 0;
    }

    // Afficher les caméras en console
    for (const auto& d : devices)
    {
        const char* facing =
            d.facing == NkCameraFacing::NK_CAMERA_FACING_FRONT ? "Front" :
            d.facing == NkCameraFacing::NK_CAMERA_FACING_BACK  ? "Back"  : "External";
        // Log : d.index, d.name, facing, d.modes.size()
        (void)facing;
    }

    // Hot-plug : re-énumérer si une caméra est branchée/débranchée
    cam.SetHotPlugCallback([&](const std::vector<NkCameraDevice>& newDevices)
    {
        devices = newDevices;
    });

    // =========================================================================
    // 4. Ouvrir la caméra 0 en HD 30fps
    // =========================================================================
    NkCameraConfig camCfg;
    camCfg.deviceIndex     = 0;
    camCfg.preset          = NkCameraResolution::NK_CAM_RES_HD;   // 1280×720
    camCfg.fps             = 30;
    camCfg.outputFormat    = NkPixelFormat::NK_PIXEL_RGBA8;
    camCfg.flipHorizontal  = true;    // miroir (utile caméra frontale)
    camCfg.autoFocus       = true;
    camCfg.autoExposure    = true;

    if (!cam.StartStreaming(camCfg))
    {
        // Erreur d'ouverture — cam.GetLastError() contient le message
        NkClose();
        return 1;
    }

    // Activer la queue de frames pour ne pas en manquer
    cam.EnableFrameQueue(4);

    // =========================================================================
    // 5. États de l'application
    // =========================================================================
    bool       isRecording  = false;
    NkU32      selectedCam  = 0;
    float      zoomLevel    = 1.f;
    bool       torchOn      = false;

    // Texture logicielle pour afficher la frame caméra
    NkCameraFrame displayFrame;
    bool          hasDisplayFrame = false;

    // =========================================================================
    // 6. Événements
    // =========================================================================
    auto& es = EventSystem::Instance();

    es.SetEventCallback<NkWindowCloseEvent>([&](auto*) { window.Close(); });

    es.SetEventCallback<NkKeyEvent>([&](NkKeyEvent* ev)
    {
        if (!ev->IsPress()) return;

        switch (ev->GetKey())
        {
        // Échap : fermer
        case NK_ESCAPE:
            window.Close();
            break;

        // Espace : capturer une photo
        case NK_SPACE:
        {
            std::string path = cam.CapturePhotoToFile(""); // nom auto = photo_YYYYMMDD_HHMMSS.png
            // path contient le chemin de la photo sauvegardée (ou "" si erreur)
            (void)path;
            break;
        }

        // R : démarrer / arrêter l'enregistrement vidéo
        case NK_R:
        {
            if (!isRecording)
            {
                NkVideoRecordConfig vrCfg;
                vrCfg.outputPath  = "";       // nom auto = video_YYYYMMDD_HHMMSS.mp4
                vrCfg.bitrateBps  = 4000000;  // 4 Mbps
                vrCfg.videoCodec  = "h264";
                vrCfg.container   = "mp4";
                isRecording = cam.StartVideoRecord(vrCfg);
            }
            else
            {
                cam.StopVideoRecord();
                isRecording = false;
            }
            break;
        }

        // + / - : zoom
        case NK_EQUALS:
            zoomLevel = std::min(zoomLevel + 0.25f, 5.f);
            cam.SetZoom(zoomLevel);
            break;
        case NK_MINUS:
            zoomLevel = std::max(zoomLevel - 0.25f, 1.f);
            cam.SetZoom(zoomLevel);
            break;

        // T : torche LED (mobile)
        case NK_T:
            torchOn = !torchOn;
            cam.SetTorch(torchOn);
            break;

        // F : autofocus
        case NK_F:
            cam.SetAutoFocus(true);
            break;

        // Chiffre 1/2/3 : changer de caméra
        case NK_1: case NK_2: case NK_3:
        {
            NkU32 newIdx = static_cast<NkU32>(ev->GetKey() - NK_1);
            if (newIdx < devices.size() && newIdx != selectedCam)
            {
                cam.StopStreaming();
                selectedCam          = newIdx;
                camCfg.deviceIndex   = selectedCam;
                cam.StartStreaming(camCfg);
                zoomLevel = 1.f;
            }
            break;
        }

        default: break;
        }
    });

    // Clic gauche : point de focus (coordonnées normalisées)
    es.SetEventCallback<NkMouseButtonEvent>([&](NkMouseButtonEvent* ev)
    {
        if (ev->GetButton() == NK_MOUSE_LEFT && ev->IsPress())
        {
            float nx = static_cast<float>(ev->GetX()) / static_cast<float>(wCfg.width);
            float ny = static_cast<float>(ev->GetY()) / static_cast<float>(wCfg.height);
            cam.SetFocusPoint(nx, ny);
        }
    });

    // =========================================================================
    // 7. Boucle principale
    // =========================================================================
    while (window.IsOpen())
    {
        es.PollEvents();

        // --- Récupérer la frame la plus récente ---
        NkCameraFrame rawFrame;
        if (cam.DrainFrameQueue(rawFrame))
        {
            // Convertir en RGBA8 si nécessaire (NV12/YUV420/BGRA → RGBA8)
            NkCameraSystem::ConvertToRGBA8(rawFrame);
            displayFrame    = std::move(rawFrame);
            hasDisplayFrame = true;
        }

        // --- Rendu ---
        renderer.BeginFrame();

        if (hasDisplayFrame && displayFrame.IsValid())
        {
            // Afficher la frame caméra pixel par pixel dans le renderer software
            // (En production : uploader dans une texture GPU via OpenGL/Vulkan/D3D11)
            NkU32 fw = displayFrame.width;
            NkU32 fh = displayFrame.height;

            // Scale pour remplir la fenêtre
            float scaleX = static_cast<float>(wCfg.width)  / static_cast<float>(fw);
            float scaleY = static_cast<float>(wCfg.height) / static_cast<float>(fh);

            // Sous-échantillonnage simple pour le renderer software
            // (en prod on utiliserait une texture + blit GPU)
            NkU32 step = 2; // afficher 1 pixel sur 2 pour les performances
            for (NkU32 y = 0; y < fh; y += step)
            {
                for (NkU32 x = 0; x < fw; x += step)
                {
                    // Lire RGBA depuis la frame
                    NkU32 pix = displayFrame.GetPixelRGBA(x, y);

                    // Coordonnées écran
                    NkI32 sx = static_cast<NkI32>(x * scaleX);
                    NkI32 sy = static_cast<NkI32>(y * scaleY);

                    // Remplir le carré step×step (approx)
                    NkU32 sw = static_cast<NkU32>(step * scaleX) + 1;
                    NkU32 sh = static_cast<NkU32>(step * scaleY) + 1;
                    renderer.FillRect(sx, sy, sw, sh, pix);
                }
            }
        }

        // --- Overlay HUD ---
        NkU32 W = wCfg.width, H = wCfg.height;

        // Indicateur d'enregistrement (rouge clignotant)
        if (isRecording)
        {
            float dur = cam.GetRecordingDurationSeconds();
            bool  blink = static_cast<int>(dur * 2) % 2 == 0;
            if (blink)
                renderer.FillCircle(W - 30, 30, 12, 0xFF2222FF);
        }

        // Barre d'infos en bas (fond semi-transparent)
        renderer.FillRect(0, H - 40, W, 40, 0x000000AA);

        // Durée d'enregistrement (barres horizontales = secondes)
        if (isRecording)
        {
            float dur = cam.GetRecordingDurationSeconds();
            NkU32 barW = static_cast<NkU32>(dur * 10.f); // 10 px par seconde
            renderer.FillRect(10, H - 30, std::min(barW, W - 20), 6, 0xFF4444FF);
        }

        // Zone de focus (cadre vert au centre par défaut)
        NkI32 fx = W / 2 - 50, fy = H / 2 - 50;
        renderer.DrawRect(fx, fy, 100, 100, 0x44FF44FF);
        renderer.DrawLine(fx + 50, fy, fx + 50, fy + 10, 0x44FF44FF);
        renderer.DrawLine(fx + 50, fy + 90, fx + 50, fy + 100, 0x44FF44FF);

        renderer.EndFrame();
        renderer.Present();
    }

    // =========================================================================
    // 8. Nettoyage
    // =========================================================================
    cam.StopVideoRecord();
    cam.StopStreaming();
    // NkClose() appelle aussi NkCameraSystem::Shutdown()
    NkClose();
    return 0;
}
