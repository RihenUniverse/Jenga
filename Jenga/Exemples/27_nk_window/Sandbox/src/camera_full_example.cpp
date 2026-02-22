// =============================================================================
// camera_full_example.cpp — Démo complète:
//   1. Énumération multi-caméras
//   2. Sélection par index (chiffres 1-4)
//   3. Streaming avec conversion de format automatique
//   4. Capture photo (Espace) + enregistrement vidéo (R)
//   5. CAMÉRA VIRTUELLE mappée sur la caméra physique (IMU)
//      → bouger le téléphone déplace la NkCamera2D
// =============================================================================

#include <NKWindow/NkWindow.h>
#include <NKWindow/Core/NkMain.h>
#include <cstdio>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <string>
#include <cstdlib>

#if defined(NKENTSEU_PLATFORM_WASM) && defined(__EMSCRIPTEN__)
#   include <emscripten.h>
#endif

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
    if (!NkInitialise(app))
    {
        std::fprintf(stderr, "[SandboxCameraFull] NkInitialise failed.\n");
        return -1;
    }

    NkWindowConfig wCfg;
    wCfg.title  = "NkCamera — Multi + Virtuelle";
    wCfg.width  = 1280;
    wCfg.height = 720;
    nkentseu::Window window(wCfg);
    if (!window.IsOpen())
    {
        std::fprintf(stderr, "[SandboxCameraFull] Window creation failed: %s\n", window.GetLastError().ToString().c_str());
        NkClose();
        return -2;
    }

#if defined(NKENTSEU_PLATFORM_NOOP)
    std::fprintf(
        stderr,
        "[SandboxCameraFull] Built with NOOP headless backend. Rebuild without --headless to use camera/window.\n"
    );
    window.Close();
    NkClose();
    return -3;
#endif

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
    bool  cameraStreaming = false;

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

    struct StartProfile
    {
        NkCameraResolution preset;
        NkU32 fps;
        const char* label;
    };
    const StartProfile startProfiles[] = {
        { NkCameraResolution::NK_CAM_RES_HD,   30, "HD@30"   },
        { NkCameraResolution::NK_CAM_RES_VGA,  30, "VGA@30"  },
        { NkCameraResolution::NK_CAM_RES_VGA,  15, "VGA@15"  },
        { NkCameraResolution::NK_CAM_RES_QVGA, 30, "QVGA@30" },
    };
    const std::size_t startProfileCount = sizeof(startProfiles) / sizeof(startProfiles[0]);
    bool preferWslSafeProfile = false;
#if defined(NKENTSEU_PLATFORM_XLIB) || defined(NKENTSEU_PLATFORM_XCB)
    preferWslSafeProfile = (std::getenv("WSL_INTEROP") != nullptr) ||
                           (std::getenv("WSL_DISTRO_NAME") != nullptr);
#endif
    std::size_t profileStartIndex = preferWslSafeProfile ? 1u : 0u;
    if (preferWslSafeProfile)
        camCfg.preset = NkCameraResolution::NK_CAM_RES_VGA;

    auto tryStartCamera = [&](NkU32 deviceIndex) -> bool
    {
        if (deviceIndex >= devices.size())
            return false;

        const NkCameraConfig baseCfg = camCfg;

        for (std::size_t attempt = 0; attempt < startProfileCount; ++attempt)
        {
            const std::size_t profileIndex = (profileStartIndex + attempt) % startProfileCount;
            const auto& p = startProfiles[profileIndex];
            NkCameraConfig tryCfg = baseCfg;
            tryCfg.deviceIndex = deviceIndex;
            tryCfg.preset      = p.preset;
            tryCfg.fps         = p.fps;
            tryCfg.facing = (devices[deviceIndex].facing == NkCameraFacing::NK_CAMERA_FACING_FRONT)
                          ? NkCameraFacing::NK_CAMERA_FACING_FRONT
                          : NkCameraFacing::NK_CAMERA_FACING_BACK;

            if (cam.StartStreaming(tryCfg))
            {
                camCfg = tryCfg;
                profileStartIndex = profileIndex;
                cam.EnableFrameQueue(4);
                std::fprintf(
                    stderr,
                    "[SandboxCameraFull] Camera %u streaming started (%s).\n",
                    deviceIndex,
                    p.label
                );
                return true;
            }

            std::fprintf(
                stderr,
                "[SandboxCameraFull] StartStreaming failed on device %u (%s): %s\n",
                deviceIndex,
                p.label,
                cam.GetLastError().c_str()
            );
        }

        return false;
    };

    if (devices.empty())
    {
        std::fprintf(
            stderr,
            "[SandboxCameraFull] No camera device found. Running virtual world mode only.\n"
        );
    }
    else
    {
        cameraStreaming = tryStartCamera(0);
        if (!cameraStreaming)
        {
            std::fprintf(
                stderr,
                "[SandboxCameraFull] Running virtual world mode only (camera stream unavailable).\n"
            );
        }
    }

    std::fprintf(
        stderr,
        "[SandboxCameraFull] Controls: SPACE=photo, R=record, M=mode(AUTO/VIDEO/MANUAL), V=toggle preview/world, ESC=quit.\n"
        "[SandboxCameraFull] Ensure window focus before pressing keys.\n"
    );

    // =========================================================================
    // 2. CAMÉRA VIRTUELLE MAPPÉE SUR LA CAMÉRA PHYSIQUE (IMU)
    //    Déplacer l'appareil physique → déplace la NkCamera2D dans le monde 2D
    // =========================================================================
    CameraVirtualDemo vDemo;
    {
        NkVec2u s = window.GetSize();
        vDemo.virtualCam.SetViewport(
            static_cast<float>(s.x ? s.x : wCfg.width),
            static_cast<float>(s.y ? s.y : wCfg.height)
        );
    }
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
    cam.SetVirtualCameraMapping(cameraStreaming);  // active uniquement si caméra physique active

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
    bool   showVirtualWorld = false; // false=preview caméra, true=monde virtuel
    float  virtualZoom      = 1.f;
    NkVideoRecordConfig::Mode recordMode = NkVideoRecordConfig::Mode::AUTO;
    auto recordModeToString = [](NkVideoRecordConfig::Mode mode) -> const char*
    {
        switch (mode)
        {
        case NkVideoRecordConfig::Mode::VIDEO_ONLY: return "VIDEO_ONLY";
        case NkVideoRecordConfig::Mode::IMAGE_SEQUENCE_ONLY: return "IMAGE_SEQUENCE_ONLY";
        case NkVideoRecordConfig::Mode::AUTO:
        default: return "AUTO";
        }
    };
    NkCameraFrame displayFrame;
    bool   hasFrame         = false;
    NkCameraFrame capturePreviewFrame;
    bool   hasCapturePreview = false;
    NkU32  capturePreviewTicks = 0;
    NkCameraOrientation lastOrient{};
    bool   warnedNoImu = false;
    bool   warnedNoFrameTransport = false;
    NkU32  fallbackTick = 0;
    auto   lastFrameTimestamp = std::chrono::steady_clock::now();
    float  dt               = 1.f/60.f;
    float  focusNx          = 0.5f;
    float  focusNy          = 0.5f;

    struct UiRect
    {
        NkI32 x = 0;
        NkI32 y = 0;
        NkU32 w = 0;
        NkU32 h = 0;

        bool IsValid() const
        {
            return w > 0 && h > 0;
        }

        bool Contains(NkI32 px, NkI32 py) const
        {
            return IsValid()
                && px >= x
                && py >= y
                && px < (x + static_cast<NkI32>(w))
                && py < (y + static_cast<NkI32>(h));
        }
    };

    NkSafeAreaInsets safeArea{};
    NkU32 windowW = wCfg.width;
    NkU32 windowH = wCfg.height;
    NkI32 contentX = 0;
    NkI32 contentY = 0;
    NkU32 contentW = wCfg.width;
    NkU32 contentH = wCfg.height;
    UiRect modeBtn{};
    UiRect toggleBtn{};
    UiRect photoBtn{};
    UiRect recordBtn{};
    UiRect switchBtn{};

    auto updateLayout = [&]()
    {
        NkVec2u s = window.GetSize();
        if (s.x > 0) windowW = s.x;
        if (s.y > 0) windowH = s.y;

        safeArea = window.GetSafeAreaInsets();

        NkU32 insetL = static_cast<NkU32>(std::max(0.0f, safeArea.left));
        NkU32 insetR = static_cast<NkU32>(std::max(0.0f, safeArea.right));
        NkU32 insetT = static_cast<NkU32>(std::max(0.0f, safeArea.top));
        NkU32 insetB = static_cast<NkU32>(std::max(0.0f, safeArea.bottom));

        if (insetL + insetR >= windowW) { insetL = 0; insetR = 0; }
        if (insetT + insetB >= windowH) { insetT = 0; insetB = 0; }

        contentX = static_cast<NkI32>(insetL);
        contentY = static_cast<NkI32>(insetT);
        contentW = windowW - insetL - insetR;
        contentH = windowH - insetT - insetB;

        if (contentW == 0) { contentX = 0; contentW = windowW; }
        if (contentH == 0) { contentY = 0; contentH = windowH; }

        vDemo.virtualCam.SetViewport(static_cast<float>(contentW), static_cast<float>(contentH));

        const NkU32 btnSize = std::max<NkU32>(54u, std::min(contentW, contentH) / 9u);
        const NkI32 padding = static_cast<NkI32>(std::max<NkU32>(12u, btnSize / 4u));
        const NkI32 bottomY = contentY + static_cast<NkI32>(contentH)
                            - static_cast<NkI32>(btnSize) - padding;

        modeBtn   = UiRect{ contentX + padding, contentY + padding, btnSize, btnSize };
        toggleBtn = UiRect{ contentX + padding, bottomY, btnSize, btnSize };
        photoBtn  = UiRect{
            contentX + static_cast<NkI32>(contentW / 2u) - static_cast<NkI32>(btnSize / 2u),
            bottomY,
            btnSize,
            btnSize
        };
        recordBtn = UiRect{
            contentX + static_cast<NkI32>(contentW) - static_cast<NkI32>(btnSize) - padding,
            bottomY,
            btnSize,
            btnSize
        };
        switchBtn = UiRect{};
        if (devices.size() > 1)
        {
            switchBtn = UiRect{
                contentX + static_cast<NkI32>(contentW) - static_cast<NkI32>(btnSize) - padding,
                contentY + padding,
                btnSize,
                btnSize
            };
        }
    };
    updateLayout();
    renderer.Resize(windowW, windowH);
    if (cameraStreaming)
        currentDevice = cam.GetCurrentDeviceIndex();

    auto& es = EventSystem::Instance();
    auto switchCameraToIndex = [&](NkU32 idx)
    {
        if (idx >= static_cast<NkU32>(devices.size()) || idx == currentDevice)
            return;

        const NkU32 oldIdx = currentDevice;
        if (cameraStreaming)
            cam.StopStreaming();
        cameraStreaming = tryStartCamera(idx);
        if (!cameraStreaming)
        {
            std::fprintf(stderr, "[SandboxCameraFull] Switch camera failed.\n");
            cameraStreaming = tryStartCamera(oldIdx);
            if (!cameraStreaming)
                std::fprintf(stderr, "[SandboxCameraFull] Restore previous camera failed.\n");
        }

        if (cameraStreaming && cam.GetCurrentDeviceIndex() < devices.size())
        {
            currentDevice = cam.GetCurrentDeviceIndex();
            cam.SetVirtualCameraTarget(&vDemo.virtualCam);
            cam.SetVirtualCameraMapping(true);
            warnedNoImu = false;
        }
        else
        {
            currentDevice = oldIdx;
        }

        hasFrame = false;
    };

    auto switchCameraNext = [&]()
    {
        if (devices.size() <= 1)
            return;
        const NkU32 next = (currentDevice + 1u) % static_cast<NkU32>(devices.size());
        switchCameraToIndex(next);
    };

    auto capturePhoto = [&]()
    {
        if (!cameraStreaming)
            return;

        std::string path = cam.CapturePhotoToFile(""); // nom auto horodaté
        if (!path.empty())
        {
            std::fprintf(
                stderr,
                "[SandboxCameraFull] Photo saved: %s\n",
                path.c_str()
            );
            NkCameraFrame snap;
            bool gotSnap = false;
            if (hasFrame && displayFrame.IsValid())
            {
                snap = displayFrame;
                gotSnap = true;
            }
            else if (cam.GetLastFrame(snap))
            {
                gotSnap = NkCameraSystem::ConvertToRGBA8(snap);
            }

            if (gotSnap && snap.IsValid() && snap.format == NkPixelFormat::NK_PIXEL_RGBA8)
            {
                capturePreviewFrame = std::move(snap);
                hasCapturePreview   = true;
                capturePreviewTicks = 180; // ~3 secondes
            }
        }
        else
        {
            NkCameraFrame dbg;
            bool got = cam.GetLastFrame(dbg);
            std::fprintf(
                stderr,
                "[SandboxCameraFull] CapturePhotoToFile failed. hasLastFrame=%d format=%s size=%ux%u backendError='%s'\n",
                got ? 1 : 0,
                got ? NkPixelFormatToString(dbg.format) : "N/A",
                got ? dbg.width : 0u,
                got ? dbg.height : 0u,
                cam.GetLastError().c_str()
            );
        }
    };

    auto toggleRecord = [&]()
    {
        if (!cameraStreaming)
            return;
        if (!isRecording)
        {
            NkVideoRecordConfig vrCfg;
            vrCfg.outputPath = ""; // nom auto
            vrCfg.bitrateBps = 4000000;
            vrCfg.videoCodec = "h264";
            vrCfg.container  = "mp4";
            vrCfg.mode       = recordMode;
            if (recordMode == NkVideoRecordConfig::Mode::IMAGE_SEQUENCE_ONLY)
                vrCfg.videoCodec = "images";
            isRecording = cam.StartVideoRecord(vrCfg);
            if (isRecording)
            {
                std::fprintf(
                    stderr,
                    "[SandboxCameraFull] Recording started (mode=%s, auto output path).\n",
                    recordModeToString(recordMode)
                );
            }
            else
            {
                std::fprintf(
                    stderr,
                    "[SandboxCameraFull] Recording start failed: %s\n",
                    cam.GetLastError().c_str()
                );
            }
        }
        else
        {
            cam.StopVideoRecord();
            isRecording = false;
            std::fprintf(stderr, "[SandboxCameraFull] Recording stopped.\n");
        }
    };

    auto cycleRecordMode = [&]()
    {
        if (isRecording)
            return;
        switch (recordMode)
        {
        case NkVideoRecordConfig::Mode::AUTO:
            recordMode = NkVideoRecordConfig::Mode::VIDEO_ONLY;
            break;
        case NkVideoRecordConfig::Mode::VIDEO_ONLY:
            recordMode = NkVideoRecordConfig::Mode::IMAGE_SEQUENCE_ONLY;
            break;
        case NkVideoRecordConfig::Mode::IMAGE_SEQUENCE_ONLY:
        default:
            recordMode = NkVideoRecordConfig::Mode::AUTO;
            break;
        }
        std::fprintf(
            stderr,
            "[SandboxCameraFull] Record mode switched to %s.\n",
            recordModeToString(recordMode)
        );
    };

    auto setFocusFromScreenPoint = [&](float px, float py)
    {
        if (contentW == 0 || contentH == 0)
            return;
        float nx = (px - static_cast<float>(contentX)) / static_cast<float>(contentW);
        float ny = (py - static_cast<float>(contentY)) / static_cast<float>(contentH);
        nx = std::clamp(nx, 0.0f, 1.0f);
        ny = std::clamp(ny, 0.0f, 1.0f);
        focusNx = nx;
        focusNy = ny;
        if (cameraStreaming)
            cam.SetFocusPoint(nx, ny);
    };

    auto handleActionKey = [&](NkKey key)
    {
        switch (key)
        {
        case NkKey::NK_ESCAPE:
            window.Close();
            break;

        case NkKey::NK_NUM1:
        case NkKey::NK_NUM2:
        case NkKey::NK_NUM3:
        case NkKey::NK_NUM4:
        {
            NkU32 idx = static_cast<NkU32>(key) - static_cast<NkU32>(NkKey::NK_NUM1);
            switchCameraToIndex(idx);
            break;
        }

        case NkKey::NK_SPACE:
            capturePhoto();
            break;

        case NkKey::NK_R:
            toggleRecord();
            break;

        case NkKey::NK_M:
            cycleRecordMode();
            break;

        case NkKey::NK_V:
            showVirtualWorld = !showVirtualWorld;
            break;

        case NkKey::NK_Z:
            vDemo.virtualCam.SetPosition(vDemo.worldWidth / 2.f, vDemo.worldHeight / 2.f);
            vDemo.virtualCam.Reset();
            cam.SetVirtualCameraMapping(false);
            cam.SetVirtualCameraMapping(cameraStreaming); // re-capturer référence IMU
            break;

        case NkKey::NK_EQUALS:
            virtualZoom = std::min(virtualZoom + 0.25f, 4.f);
            vDemo.virtualCam.SetZoom(virtualZoom);
            break;

        case NkKey::NK_MINUS:
            virtualZoom = std::max(virtualZoom - 0.25f, 0.25f);
            vDemo.virtualCam.SetZoom(virtualZoom);
            break;

        case NkKey::NK_T:
        {
            static bool torchOn = false;
            torchOn = !torchOn;
            cam.SetTorch(torchOn);
            break;
        }

        case NkKey::NK_F:
            if (cameraStreaming)
                cam.SetAutoFocus(true);
            break;

        default:
            break;
        }
    };

    auto handlePointerPress = [&](NkI32 px, NkI32 py)
    {
        if (modeBtn.Contains(px, py))
        {
            handleActionKey(NkKey::NK_M);
            return;
        }
        if (switchBtn.Contains(px, py))
        {
            switchCameraNext();
            return;
        }
        if (toggleBtn.Contains(px, py))
        {
            handleActionKey(NkKey::NK_V);
            return;
        }
        if (photoBtn.Contains(px, py))
        {
            handleActionKey(NkKey::NK_SPACE);
            return;
        }
        if (recordBtn.Contains(px, py))
        {
            handleActionKey(NkKey::NK_R);
            return;
        }
        setFocusFromScreenPoint(static_cast<float>(px), static_cast<float>(py));
    };

    es.SetEventCallback<NkWindowCloseEvent>([&](auto*)
    {
        std::fprintf(stderr, "[SandboxCameraFull] Window close request received.\n");
        window.Close();
    });

    es.SetEventCallback<NkWindowResizeEvent>([&](NkWindowResizeEvent* ev)
    {
        renderer.Resize(ev->GetWidth(), ev->GetHeight());
        updateLayout();
    });

    es.SetEventCallback<NkKeyPressEvent>([&](NkKeyPressEvent* ev)
    {
        std::fprintf(
            stderr,
            "[SandboxCameraFull] KeyPress key=%s scancode=%s native=%u\n",
            NkKeyToString(ev->GetKey()),
            NkScancodeToString(ev->GetScancode()),
            ev->GetNativeKey()
        );
        handleActionKey(ev->GetKey());
    });

    // Molette → zoom caméra physique
    es.SetEventCallback<NkMouseWheelVerticalEvent>([&](NkMouseWheelVerticalEvent* ev) {
        static float pZoom = 1.f;
        pZoom = std::max(1.f, std::min(pZoom + static_cast<float>(ev->GetDelta()) * 0.1f, 5.f));
        if (cameraStreaming) cam.SetZoom(pZoom);
    });

    // Clic/touch: UI mobile ou point de focus.
    es.SetEventCallback<NkMouseButtonPressEvent>([&](NkMouseButtonPressEvent* ev) {
        if (ev->GetButton() == NkMouseButton::NK_MB_LEFT)
            handlePointerPress(ev->GetX(), ev->GetY());
    });

    es.SetEventCallback<NkTouchBeginEvent>([&](NkTouchBeginEvent* ev) {
        if (ev->GetNumTouches() > 0)
        {
            const auto& t = ev->GetTouch(0);
            handlePointerPress(static_cast<NkI32>(t.clientX), static_cast<NkI32>(t.clientY));
        }
    });

    // =========================================================================
    // Boucle principale
    // =========================================================================
    auto prevTime = std::chrono::steady_clock::now();

#if defined(NKENTSEU_PLATFORM_NOOP)
    int headlessFrames = 2;
#endif

    while (window.IsOpen())
    {
#if defined(NKENTSEU_PLATFORM_NOOP)
        if (--headlessFrames <= 0)
        {
            window.Close();
        }
#endif
        auto now = std::chrono::steady_clock::now();
        dt = std::chrono::duration<float>(now - prevTime).count();
        prevTime = now;

        if (capturePreviewTicks > 0)
            --capturePreviewTicks;
        ++fallbackTick;

        es.PollEvents();
        if (!window.IsOpen())
            break;
        updateLayout();

        // ----- Récupérer la frame caméra -----
        bool gotFrameThisTick = false;
        if (cameraStreaming) {
            NkCameraFrame raw;
            if (cam.DrainFrameQueue(raw)) {
                if (NkCameraSystem::ConvertToRGBA8(raw) && raw.IsValid())
                {
                    displayFrame = std::move(raw);
                    hasFrame = true;
                    gotFrameThisTick = true;
                    lastFrameTimestamp = now;
                }
            }
        }

        if (cameraStreaming && !gotFrameThisTick)
        {
            const auto silentMs = std::chrono::duration_cast<std::chrono::milliseconds>(
                now - lastFrameTimestamp).count();
            if (silentMs > 4000)
            {
                std::fprintf(
                    stderr,
                    "[SandboxCameraFull] No frame received for %.2fs on camera %u (backendError='%s').\n",
                    static_cast<double>(silentMs) / 1000.0,
                    currentDevice,
                    cam.GetLastError().c_str()
                );
                if (cam.GetLastError().empty() && !warnedNoFrameTransport)
                {
                    std::fprintf(
                        stderr,
                        "[SandboxCameraFull] Device opened but no frame payload is arriving. "
                        "In WSL2 this usually means USB camera transport is not delivering video packets.\n"
                    );
                    warnedNoFrameTransport = true;
                }

                const NkU32 previousCam = currentDevice;
                cam.StopStreaming();
                cameraStreaming = false;
                hasFrame = false;

                profileStartIndex = (profileStartIndex + 1u) % startProfileCount;
                std::fprintf(stderr, "[SandboxCameraFull] Restarting current camera with fallback profiles...\n");
                bool recovered = tryStartCamera(previousCam);

                if (!recovered && devices.size() > 1)
                {
                    std::fprintf(stderr, "[SandboxCameraFull] Trying another camera device...\n");
                    for (NkU32 step = 1; step <= devices.size(); ++step)
                    {
                        NkU32 idx = (previousCam + step) % static_cast<NkU32>(devices.size());
                        if (tryStartCamera(idx))
                        {
                            cameraStreaming = true;
                            currentDevice = cam.GetCurrentDeviceIndex();
                            cam.SetVirtualCameraTarget(&vDemo.virtualCam);
                            cam.SetVirtualCameraMapping(true);
                            warnedNoImu = false;
                            std::fprintf(
                                stderr,
                                "[SandboxCameraFull] Recovered stream on camera %u.\n",
                                currentDevice
                            );
                            break;
                        }
                    }

                    if (!cameraStreaming)
                    {
                        std::fprintf(
                            stderr,
                            "[SandboxCameraFull] Failed to recover stream on alternate devices.\n"
                        );
                    }
                }
                else if (recovered)
                {
                    cameraStreaming = true;
                    currentDevice = cam.GetCurrentDeviceIndex();
                }

                lastFrameTimestamp = now;
            }
        }
        else if (!cameraStreaming)
        {
            lastFrameTimestamp = now;
        }

        // ----- Mettre à jour la caméra virtuelle depuis l'IMU -----
        // Si l'IMU est disponible (mobile/tablette), bouge automatiquement
        // Sur desktop sans IMU → UpdateVirtualCamera est un no-op
        cam.UpdateVirtualCamera(dt);

        // Lire l'orientation courante pour l'affichage debug
        bool orientationAvailable = cam.GetCurrentOrientation(lastOrient);
        if (cam.IsVirtualCameraMappingEnabled() && !orientationAvailable && !warnedNoImu)
        {
            std::fprintf(
                stderr,
                "[SandboxCameraFull] Orientation/IMU unavailable on this device. "
                "Virtual tracking from physical motion is disabled.\n"
            );
            warnedNoImu = true;
        }

        // -----  Rendu -----
        renderer.BeginFrame();

        if (showVirtualWorld)
        {
            // === MODE MONDE VIRTUEL ===
            // Appliquer la transformation de la caméra virtuelle
            NkTransform2D worldTransform = vDemo.virtualCam.GetTransform();
            worldTransform.position.x += static_cast<float>(contentX);
            worldTransform.position.y += static_cast<float>(contentY);
            renderer.SetTransform(worldTransform);

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
                float sx=(float)contentW/fw, sy=(float)contentH/fh;
                // Rendu sous-échantillonné (software renderer)
                NkU32 step=2;
                for (NkU32 y=0;y<fh;y+=step) for (NkU32 x=0;x<fw;x+=step) {
                    NkU32 pix=displayFrame.GetPixelRGBA(x,y);
                    renderer.FillRect(contentX + (NkI32)(x*sx), contentY + (NkI32)(y*sy),
                                      (NkU32)(step*sx)+1,(NkU32)(step*sy)+1,pix);
                }
            }
            else
            {
                // Fallback visuel explicite quand aucune frame n'est dispo.
                const NkU32 pulse = (fallbackTick / 2u) % 255u;
                renderer.FillRect(
                    contentX,
                    contentY,
                    contentW,
                    contentH,
                    Renderer::PackColor(8, 12, static_cast<NkU8>(20 + pulse / 8u))
                );
                if (contentW > 60 && contentH > 120)
                {
                    renderer.DrawRect(
                        contentX + 30,
                        contentY + 30,
                        contentW - 60,
                        contentH - 120,
                        0x4466AAFF
                    );
                    renderer.DrawLine(
                        contentX + 30,
                        contentY + 30,
                        contentX + static_cast<NkI32>(contentW - 30),
                        contentY + static_cast<NkI32>(contentH - 90),
                        0x6688CCFF
                    );
                    renderer.DrawLine(
                        contentX + static_cast<NkI32>(contentW - 30),
                        contentY + 30,
                        contentX + 30,
                        contentY + static_cast<NkI32>(contentH - 90),
                        0x6688CCFF
                    );
                }
                renderer.FillCircle(
                    contentX + static_cast<NkI32>(contentW / 2u),
                    contentY + static_cast<NkI32>(contentH / 2u - 20),
                    24,
                    0xCC4444FF
                );
            }
        }

        // === HUD (toujours en espace écran) ===
        NkU32 W = contentW, H = contentH;
        NkI32 X = contentX, Y = contentY;

        // Barre inférieure
        renderer.FillRect(X, Y + static_cast<NkI32>(H) - 50, W, 50, 0x000000CC);

        // Indicateur enregistrement
        if (isRecording) {
            float dur=cam.GetRecordingDurationSeconds();
            bool blink=(NkI32)(dur*2)%2==0;
            if (blink) renderer.FillCircle(X + static_cast<NkI32>(W) - 25, Y + static_cast<NkI32>(H) - 25, 10, 0xFF2222FF);
        }

        // Indicateur mapping IMU actif
        if (cam.IsVirtualCameraMappingEnabled()) {
            // Cercle boussole montrant la rotation
            renderer.DrawCircle(X + static_cast<NkI32>(W) - 60, Y + 30, 20, orientationAvailable ? 0x44AAFFFF : 0xAA4444FF);
            if (orientationAvailable)
            {
                float yaw_r = lastOrient.yaw * 3.14159f / 180.f;
                renderer.DrawLine(
                    X + static_cast<NkI32>(W) - 60, Y + 30,
                    X + static_cast<NkI32>(W) - 60 + (NkI32)(sinf(yaw_r) * 18),
                    Y + 30 - (NkI32)(cosf(yaw_r) * 18),
                    0xFF4444FF);
            }
        }

        // Barre mode
        renderer.DrawLine(
            X + 10,
            Y + static_cast<NkI32>(H) - 25,
            X + static_cast<NkI32>(W / 4u),
            Y + static_cast<NkI32>(H) - 25,
            showVirtualWorld ? 0x44FF44FF : 0xFF8844FF
        );

        // Indicateur caméra courante
        // (barres = nombre de caméras disponibles)
        for (NkU32 i=0;i<(NkU32)devices.size()&&i<4;++i) {
            NkU32 col = (i==currentDevice) ? 0x44FF44FF : 0x334455FF;
            renderer.FillRect(X + 10 + i * 18, Y + static_cast<NkI32>(H) - 15, 14, 8, col);
        }

        // Zone de focus (dernier point touché/clic).
        NkI32 fx = X + static_cast<NkI32>(focusNx * static_cast<float>(W)) - 40;
        NkI32 fy = Y + static_cast<NkI32>(focusNy * static_cast<float>(H)) - 40;
        renderer.DrawRect(fx, fy, 80, 80, 0x44FF44FF);

        // Miniature de la dernière capture photo.
        if (hasCapturePreview && capturePreviewTicks > 0 && capturePreviewFrame.IsValid())
        {
            const NkU32 tw = 240;
            const NkU32 th = 135;
            const NkI32 tx = X + static_cast<NkI32>(W) - static_cast<NkI32>(tw) - 16;
            const NkI32 ty = Y + 60;
            renderer.DrawRect(tx - 2, ty - 2, tw + 4, th + 4, 0xFFFFFFFF);

            for (NkU32 py = 0; py < th; ++py)
            {
                NkU32 sy = (py * capturePreviewFrame.height) / th;
                for (NkU32 px = 0; px < tw; ++px)
                {
                    NkU32 sx = (px * capturePreviewFrame.width) / tw;
                    NkU32 pix = capturePreviewFrame.GetPixelRGBA(sx, sy);
                    renderer.SetPixel(tx + static_cast<NkI32>(px), ty + static_cast<NkI32>(py), pix);
                }
            }
        }

        const NkU32 modeColor =
            (recordMode == NkVideoRecordConfig::Mode::AUTO) ? 0x4477DDFF :
            (recordMode == NkVideoRecordConfig::Mode::VIDEO_ONLY) ? 0x44AA44FF :
                                                                    0xAA8844FF;
        renderer.FillRect(modeBtn.x, modeBtn.y, modeBtn.w, modeBtn.h, modeColor);
        renderer.DrawRect(modeBtn.x, modeBtn.y, modeBtn.w, modeBtn.h, 0xFFFFFFFF);

        renderer.FillRect(toggleBtn.x, toggleBtn.y, toggleBtn.w, toggleBtn.h, showVirtualWorld ? 0x337733FF : 0x773333FF);
        renderer.DrawRect(toggleBtn.x, toggleBtn.y, toggleBtn.w, toggleBtn.h, 0xFFFFFFFF);

        renderer.FillRect(photoBtn.x, photoBtn.y, photoBtn.w, photoBtn.h, 0xDDDDDDFF);
        renderer.DrawRect(photoBtn.x, photoBtn.y, photoBtn.w, photoBtn.h, 0xFFFFFFFF);

        renderer.FillRect(
            recordBtn.x,
            recordBtn.y,
            recordBtn.w,
            recordBtn.h,
            isRecording ? 0xFF3333FF : 0x772222FF
        );
        renderer.DrawRect(recordBtn.x, recordBtn.y, recordBtn.w, recordBtn.h, 0xFFFFFFFF);

        if (switchBtn.IsValid())
        {
            renderer.FillRect(switchBtn.x, switchBtn.y, switchBtn.w, switchBtn.h, 0x446644FF);
            renderer.DrawRect(switchBtn.x, switchBtn.y, switchBtn.w, switchBtn.h, 0xFFFFFFFF);
        }

        renderer.EndFrame();
        renderer.Present();

#if defined(NKENTSEU_PLATFORM_WASM) && defined(__EMSCRIPTEN__)
        // Cooperative yield so browser keeps presenting frames/input.
        emscripten_sleep(0);
#endif
    }

    // Nettoyage
    if (isRecording) cam.StopVideoRecord();
    if (cameraStreaming) cam.StopStreaming();
    NkClose();
    return 0;
}
