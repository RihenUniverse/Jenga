// =============================================================================
// camera_full_example.cpp — Démo complète:
//   1. Énumération multi-caméras
//   2. Sélection par index (chiffres 1-4)
//   3. Streaming avec conversion de format automatique
//   4. Capture photo (Espace) + enregistrement vidéo (R)
//   5. CAMÉRA VIRTUELLE mappée sur la caméra physique (IMU)
//      → bouger le téléphone déplace la NkCamera2D
// =============================================================================

#include <NkWindow/NkWindow.h>
#include <NkWindow/Core/NkMain.h>
#include <algorithm>
#include <string>

using namespace nkentseu;

// =============================================================================
// Configuration du mapping caméra virtuelle ← physique
// =============================================================================
struct CameraVirtualDemo {
    NkCamera2D    virtualCam;             // caméra 2D pilotée par l'IMU
    float         worldWidth  = 2000.f;   // taille du "monde" à explorer
    float         worldHeight = 1500.f;
};

// =============================================================================
int nkmain(const NkEntryState& state)
{
    NkAppData app;
    app.appName           = "NkCamera Full Demo";
    app.preferredRenderer = NkRendererApi::NK_SOFTWARE;
    NkInitialise(app);

    NkWindowConfig wCfg;
    wCfg.title  = "NkCamera — Multi + Virtuelle";
    wCfg.width  = 1280;
    wCfg.height = 720;
    Window window(wCfg);
    Renderer renderer(window);
    renderer.SetBackgroundColor(0x0A0A1AFF);

    // =========================================================================
    // 1. ACCÈS MULTI-CAMÉRAS
    //    EnumerateDevices() retourne TOUTES les caméras du système.
    //    Pour en ouvrir une spécifique: cfg.deviceIndex = N
    //    Pour plusieurs simultanées: utiliser NkMultiCamera
    // =========================================================================
    auto& cam     = NkCamera();
    auto  devices = cam.EnumerateDevices();

    // Afficher les caméras disponibles
    // devices[0] = première caméra (webcam principale, ou caméra arrière mobile)
    // devices[1] = deuxième caméra (caméra frontale mobile, ou deuxième webcam)
    // etc.

    // Ouvrir la caméra 0 par défaut
    NkCameraConfig camCfg;
    camCfg.deviceIndex   = 0;
    camCfg.preset        = NkCameraResolution::NK_CAM_RES_HD;
    camCfg.fps           = 30;
    camCfg.flipHorizontal = true;
    cam.StartStreaming(camCfg);
    cam.EnableFrameQueue(4);

    // =========================================================================
    // 2. CAMÉRA VIRTUELLE MAPPÉE SUR LA CAMÉRA PHYSIQUE (IMU)
    //    Déplacer l'appareil physique → déplace la NkCamera2D dans le monde 2D
    // =========================================================================
    CameraVirtualDemo vDemo;
    vDemo.virtualCam.SetViewport((float)wCfg.width, (float)wCfg.height);
    vDemo.virtualCam.SetPosition(vDemo.worldWidth/2.f, vDemo.worldHeight/2.f);
    vDemo.virtualCam.SetZoom(1.f);

    // Lier la caméra virtuelle au système caméra physique
    cam.SetVirtualCameraTarget(&vDemo.virtualCam);

    // Config du mapping:
    NkCameraSystem::VirtualCameraMapConfig mapCfg;
    mapCfg.yawSensitivity   = 5.f;   // 1° mouvement physique → 5px déplacement
    mapCfg.pitchSensitivity = 5.f;
    mapCfg.translationScale = 10.f;  // > 0 → mode translation (pan)
    mapCfg.smoothing        = true;
    mapCfg.smoothFactor     = 0.12f;
    mapCfg.invertX          = false;
    mapCfg.invertY          = true;   // inversion Y naturelle
    cam.SetVirtualCameraMapConfig(mapCfg);
    cam.SetVirtualCameraMapping(true);  // ACTIVER le mapping

    // =========================================================================
    // 3. EXEMPLE MULTI-CAMÉRA SIMULTANÉ (2 caméras)
    //    Décommenter si vous avez 2 caméras
    // =========================================================================
    // NkMultiCamera multi;
    // if (devices.size() >= 2) {
    //     NkCameraConfig cfg0; cfg0.deviceIndex=0; cfg0.preset=NK_CAM_RES_HD;
    //     NkCameraConfig cfg1; cfg1.deviceIndex=1; cfg1.preset=NK_CAM_RES_VGA;
    //     auto& s0 = multi.Open(0, cfg0);
    //     auto& s1 = multi.Open(1, cfg1);
    //     s0.EnableQueue(4);
    //     s1.EnableQueue(4);
    //     // Dans la boucle:
    //     // NkCameraFrame f0, f1;
    //     // s0.DrainFrame(f0); renderFrame(renderer, f0, 0, 0, 640, 360);
    //     // s1.DrainFrame(f1); renderFrame(renderer, f1, 640, 0, 640, 360);
    // }

    // =========================================================================
    // État
    // =========================================================================
    NkU32  currentDevice    = 0;
    bool   isRecording      = false;
    bool   showVirtualWorld = true;  // true=monde virtuel, false=preview caméra
    float  virtualZoom      = 1.f;
    NkCameraFrame displayFrame;
    bool   hasFrame         = false;
    NkCameraOrientation lastOrient{};
    float  dt               = 1.f/60.f;

    auto& es = EventSystem::Instance();
    es.SetEventCallback<NkWindowCloseEvent>([&](auto*){ window.Close(); });

    es.SetEventCallback<NkKeyEvent>([&](NkKeyEvent* ev)
    {
        if (!ev->IsPress()) return;
        switch (ev->GetKey())
        {
        case NK_ESCAPE: window.Close(); break;

        // --- Changer de caméra (1, 2, 3, 4) ---
        case NK_1: case NK_2: case NK_3: case NK_4:
        {
            NkU32 idx = (NkU32)(ev->GetKey() - NK_1);
            if (idx < (NkU32)devices.size() && idx != currentDevice) {
                cam.StopStreaming();
                currentDevice        = idx;
                camCfg.deviceIndex   = idx;
                // Sur mobile: alterner caméra front/back
                camCfg.facing = (devices[idx].facing==NkCameraFacing::NK_CAMERA_FACING_FRONT)
                              ? NkCameraFacing::NK_CAMERA_FACING_FRONT
                              : NkCameraFacing::NK_CAMERA_FACING_BACK;
                cam.StartStreaming(camCfg);
                cam.EnableFrameQueue(4);
                // Réinitialiser le mapping IMU sur la nouvelle caméra
                cam.SetVirtualCameraTarget(&vDemo.virtualCam);
                cam.SetVirtualCameraMapping(true);
            }
            break;
        }

        // --- Capture photo ---
        case NK_SPACE:
        {
            std::string path = cam.CapturePhotoToFile(""); // nom auto horodaté
            break;
        }

        // --- Enregistrement vidéo ---
        case NK_R:
        {
            if (!isRecording) {
                NkVideoRecordConfig vrCfg;
                vrCfg.outputPath = ""; // nom auto
                vrCfg.bitrateBps = 4000000;
                vrCfg.videoCodec = "h264";
                vrCfg.container  = "mp4";
                isRecording = cam.StartVideoRecord(vrCfg);
            } else {
                cam.StopVideoRecord();
                isRecording = false;
            }
            break;
        }

        // --- Bascule affichage ---
        case NK_V:
            showVirtualWorld = !showVirtualWorld;
            break;

        // --- Reset caméra virtuelle ---
        case NK_Z:
            vDemo.virtualCam.SetPosition(vDemo.worldWidth/2.f, vDemo.worldHeight/2.f);
            vDemo.virtualCam.Reset();
            cam.SetVirtualCameraMapping(false);
            cam.SetVirtualCameraMapping(true); // re-capturer référence IMU
            break;

        // --- Zoom caméra virtuelle (molette simulée) ---
        case NK_EQUALS:
            virtualZoom = std::min(virtualZoom + 0.25f, 4.f);
            vDemo.virtualCam.SetZoom(virtualZoom);
            break;
        case NK_MINUS:
            virtualZoom = std::max(virtualZoom - 0.25f, 0.25f);
            vDemo.virtualCam.SetZoom(virtualZoom);
            break;

        // --- Torch/Flash ---
        case NK_T: { static bool ton=false; ton=!ton; cam.SetTorch(ton); break; }
        case NK_F: cam.SetAutoFocus(true); break;

        default: break;
        }
    });

    // Molette → zoom caméra physique
    es.SetEventCallback<NkMouseWheelEvent>([&](NkMouseWheelEvent* ev) {
        static float pZoom = 1.f;
        pZoom = std::max(1.f, std::min(pZoom + ev->GetDeltaY() * 0.1f, 5.f));
        cam.SetZoom(pZoom);
    });

    // Clic → focus point
    es.SetEventCallback<NkMouseButtonEvent>([&](NkMouseButtonEvent* ev) {
        if (ev->GetButton()==NK_MOUSE_LEFT && ev->IsPress()) {
            float nx = (float)ev->GetX() / (float)wCfg.width;
            float ny = (float)ev->GetY() / (float)wCfg.height;
            cam.SetFocusPoint(nx, ny);
        }
    });

    // =========================================================================
    // Boucle principale
    // =========================================================================
    auto prevTime = std::chrono::steady_clock::now();

    while (window.IsOpen())
    {
        auto now = std::chrono::steady_clock::now();
        dt = std::chrono::duration<float>(now - prevTime).count();
        prevTime = now;

        es.PollEvents();

        // ----- Récupérer la frame caméra -----
        NkCameraFrame raw;
        if (cam.DrainFrameQueue(raw)) {
            NkCameraSystem::ConvertToRGBA8(raw);
            displayFrame = std::move(raw);
            hasFrame = true;
        }

        // ----- Mettre à jour la caméra virtuelle depuis l'IMU -----
        // Si l'IMU est disponible (mobile/tablette), bouge automatiquement
        // Sur desktop sans IMU → UpdateVirtualCamera est un no-op
        cam.UpdateVirtualCamera(dt);

        // Lire l'orientation courante pour l'affichage debug
        cam.GetCurrentOrientation(lastOrient);

        // -----  Rendu -----
        renderer.BeginFrame();

        if (showVirtualWorld)
        {
            // === MODE MONDE VIRTUEL ===
            // Appliquer la transformation de la caméra virtuelle
            renderer.SetTransform(vDemo.virtualCam.GetTransform());

            // Dessiner le "monde" 2D exploré avec la caméra physique
            float W = vDemo.worldWidth, H = vDemo.worldHeight;

            // Fond du monde
            renderer.FillRect(0, 0, (NkU32)W, (NkU32)H, 0x1A2A3AFF);

            // Grille du monde
            for (float x = 0; x <= W; x += 100)
                renderer.DrawLine((NkI32)x,0,(NkI32)x,(NkI32)H,0x223344FF);
            for (float y = 0; y <= H; y += 100)
                renderer.DrawLine(0,(NkI32)y,(NkI32)W,(NkI32)y,0x223344FF);

            // Points d'intérêt dans le monde
            struct POI { float x,y; NkU32 color; const char* label; };
            POI pois[] = {
                {200,200,   0xFF4444FF, "Rouge"},
                {1000,750,  0x44FF44FF, "Vert"},
                {1800,200,  0x4444FFFF, "Bleu"},
                {200,1300,  0xFFFF44FF, "Jaune"},
                {1800,1300, 0xFF44FFFF, "Magenta"},
                {1000,750,  0xFF8844FF, "Centre"},
            };
            for (auto& p : pois) {
                renderer.FillCircle((NkI32)p.x,(NkI32)p.y,30,p.color);
                renderer.DrawCircle((NkI32)p.x,(NkI32)p.y,35,0xFFFFFFFF);
            }

            // Cadre du monde
            renderer.DrawRect(0,0,(NkU32)W,(NkU32)H,0x446688FF);

            // Réinitialiser le transform pour l'UI overlay
            renderer.SetTransform(NkTransform2D{});
        }
        else
        {
            // === MODE PREVIEW CAMÉRA ===
            if (hasFrame && displayFrame.IsValid()) {
                NkU32 fw=displayFrame.width, fh=displayFrame.height;
                float sx=(float)wCfg.width/fw, sy=(float)wCfg.height/fh;
                // Rendu sous-échantillonné (software renderer)
                NkU32 step=2;
                for (NkU32 y=0;y<fh;y+=step) for (NkU32 x=0;x<fw;x+=step) {
                    NkU32 pix=displayFrame.GetPixelRGBA(x,y);
                    renderer.FillRect((NkI32)(x*sx),(NkI32)(y*sy),
                                      (NkU32)(step*sx)+1,(NkU32)(step*sy)+1,pix);
                }
            }
        }

        // === HUD (toujours en espace écran) ===
        NkU32 W=wCfg.width, H=wCfg.height;

        // Barre inférieure
        renderer.FillRect(0,H-50,W,50,0x000000CC);

        // Indicateur enregistrement
        if (isRecording) {
            float dur=cam.GetRecordingDurationSeconds();
            bool blink=(NkI32)(dur*2)%2==0;
            if (blink) renderer.FillCircle(W-25,H-25,10,0xFF2222FF);
        }

        // Indicateur mapping IMU actif
        if (cam.IsVirtualCameraMappingEnabled()) {
            // Cercle boussole montrant la rotation
            renderer.DrawCircle(W-60, 30, 20, 0x44AAFFFF);
            float yaw_r = lastOrient.yaw * 3.14159f / 180.f;
            renderer.DrawLine(W-60,30,
                W-60+(NkI32)(sinf(yaw_r)*18),
                30-(NkI32)(cosf(yaw_r)*18),
                0xFF4444FF);
        }

        // Barre mode
        renderer.DrawLine(10,H-25,W/4,H-25,showVirtualWorld?0x44FF44FF:0xFF8844FF);

        // Indicateur caméra courante
        // (barres = nombre de caméras disponibles)
        for (NkU32 i=0;i<(NkU32)devices.size()&&i<4;++i) {
            NkU32 col = (i==currentDevice) ? 0x44FF44FF : 0x334455FF;
            renderer.FillRect(10+i*18,H-15,14,8,col);
        }

        renderer.EndFrame();
        renderer.Present();
    }

    // Nettoyage
    cam.StopVideoRecord();
    cam.StopStreaming();
    NkClose();
    return 0;
}
