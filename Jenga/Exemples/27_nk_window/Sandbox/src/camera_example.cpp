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

#include <NKWindow/NkWindow.h>
#include <NKWindow/Core/NkMain.h>
#include <cstdio>
#include <vector>
#include <algorithm>
#include <chrono>
#include <cstdlib>

#if defined(NKENTSEU_PLATFORM_WASM) && defined(__EMSCRIPTEN__)
#   include <emscripten.h>
#endif

using namespace nkentseu;

int nkmain(const NkEntryState& state)
{
    // =========================================================================
    // 1. Initialiser le framework (initialise aussi NkCameraSystem)
    // =========================================================================
    NkAppData app;
    app.appName           = "NkWindow Camera Example";
    app.preferredRenderer = NkRendererApi::NK_SOFTWARE;
    if (!NkInitialise(app))
    {
        std::fprintf(stderr, "[SandboxCamera] NkInitialise failed.\n");
        return -1;
    }

    // =========================================================================
    // 2. Fenêtre
    // =========================================================================
    NkWindowConfig wCfg;
    wCfg.title  = "Camera Preview — NkWindow";
    wCfg.width  = 1280;
    wCfg.height = 720;
    nkentseu::Window window(wCfg);
    if (!window.IsOpen())
    {
        std::fprintf(stderr, "[SandboxCamera] Window creation failed: %s\n", window.GetLastError().ToString().c_str());
        NkClose();
        return -2;
    }

#if defined(NKENTSEU_PLATFORM_NOOP)
    std::fprintf(
        stderr,
        "[SandboxCamera] Built with NOOP headless backend. Rebuild without --headless to use camera/window.\n"
    );
    window.Close();
    NkClose();
    return -3;
#endif

    Renderer renderer(window);
    renderer.SetBackgroundColor(0x111111FF);

    // =========================================================================
    // 3. Énumérer les caméras
    // =========================================================================
    auto& cam     = NkCamera();          // NkCameraSystem::Instance()
    auto  devices = cam.EnumerateDevices();
    bool  cameraStreaming = false;

    // Afficher les caméras en console
    for (const auto& d : devices)
    {
        const char* facing =
            d.facing == NkCameraFacing::NK_CAMERA_FACING_FRONT ? "Front" :
            d.facing == NkCameraFacing::NK_CAMERA_FACING_BACK  ? "Back"  : "External";
        // Log : d.index, d.name, facing, d.modes.size()
        (void)facing;
    }

    // =========================================================================
    // 4. Ouvrir la caméra 0 en HD 30fps (si disponible)
    // =========================================================================
    NkCameraConfig camCfg;
    camCfg.deviceIndex     = 0;
    camCfg.preset          = NkCameraResolution::NK_CAM_RES_HD;   // 1280×720
    camCfg.fps             = 30;
    camCfg.outputFormat    = NkPixelFormat::NK_PIXEL_RGBA8;
    camCfg.flipHorizontal  = true;    // miroir (utile caméra frontale)
    camCfg.autoFocus       = true;
    camCfg.autoExposure    = true;

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

    NkU32 selectedCam = 0;
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

            if (cam.StartStreaming(tryCfg))
            {
                camCfg = tryCfg;
                selectedCam = deviceIndex;
                profileStartIndex = profileIndex;
                cam.EnableFrameQueue(4);
                std::fprintf(
                    stderr,
                    "[SandboxCamera] Camera %u streaming started (%s).\n",
                    deviceIndex,
                    p.label
                );
                return true;
            }

            std::fprintf(
                stderr,
                "[SandboxCamera] StartStreaming failed on device %u (%s): %s\n",
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
            "[SandboxCamera] No camera device found. Fallback mode enabled.\n"
            "[SandboxCamera] Linux checks: /dev/video* exists, user in group 'video'.\n"
        );
    }
    else
    {
        cameraStreaming = tryStartCamera(0);
        if (!cameraStreaming)
        {
            std::fprintf(
                stderr,
                "[SandboxCamera] Running without camera until a device becomes available.\n"
            );
        }
    }

    std::fprintf(
        stderr,
        "[SandboxCamera] Controls: SPACE=photo, R=record, M=mode(AUTO/VIDEO/MANUAL), F=autofocus, T=torch, ESC=quit.\n"
        "[SandboxCamera] Ensure window focus before pressing keys.\n"
    );

    // Hot-plug : re-énumérer si une caméra est branchée/débranchée
    cam.SetHotPlugCallback([&](const std::vector<NkCameraDevice>& newDevices)
    {
        devices = newDevices;
        if (!cameraStreaming && !devices.empty())
        {
            NkU32 idx = (selectedCam < devices.size()) ? selectedCam : 0;
            cameraStreaming = tryStartCamera(idx);
        }
    });

    // =========================================================================
    // 5. États de l'application
    // =========================================================================
    bool       isRecording  = false;
    float      zoomLevel    = 1.f;
    bool       torchOn      = false;
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

    // Texture logicielle pour afficher la frame caméra
    NkCameraFrame displayFrame;
    bool          hasDisplayFrame = false;
    NkCameraFrame capturePreviewFrame;
    bool          hasCapturePreview = false;
    NkU32         capturePreviewTicks = 0;
    bool          warnedNoFrameTransport = false;
    auto          lastFrameTimestamp = std::chrono::steady_clock::now();
    float         focusNx = 0.5f;
    float         focusNy = 0.5f;

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

        const NkU32 btnSize = std::max<NkU32>(54u, std::min(contentW, contentH) / 9u);
        const NkI32 padding = static_cast<NkI32>(std::max<NkU32>(12u, btnSize / 4u));
        const NkI32 bottomY = contentY + static_cast<NkI32>(contentH)
                            - static_cast<NkI32>(btnSize) - padding;

        modeBtn = UiRect{ contentX + padding, bottomY, btnSize, btnSize };
        photoBtn = UiRect{
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

    // =========================================================================
    // 6. Événements
    // =========================================================================
    auto& es = EventSystem::Instance();

    auto switchCameraToIndex = [&](NkU32 newIdx)
    {
        if (newIdx < devices.size() && newIdx != selectedCam)
        {
            if (cameraStreaming)
                cam.StopStreaming();
            cameraStreaming = tryStartCamera(newIdx);
            hasDisplayFrame = false;
            if (cameraStreaming)
                zoomLevel = 1.f;
        }
    };

    auto switchCameraNext = [&]()
    {
        if (devices.size() <= 1)
            return;
        const NkU32 next = (selectedCam + 1u) % static_cast<NkU32>(devices.size());
        switchCameraToIndex(next);
    };

    auto capturePhoto = [&]()
    {
        if (!cameraStreaming)
            return;

        std::string path = cam.CapturePhotoToFile(""); // nom auto = photo_YYYYMMDD_HHMMSS.png
        if (!path.empty())
        {
            std::fprintf(
                stderr,
                "[SandboxCamera] Photo saved: %s\n",
                path.c_str()
            );

            NkCameraFrame snap;
            bool gotSnap = false;
            if (hasDisplayFrame && displayFrame.IsValid())
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
                capturePreviewFrame  = std::move(snap);
                hasCapturePreview    = true;
                capturePreviewTicks  = 180; // ~3 secondes à 60 FPS
            }
        }
        else
        {
            NkCameraFrame dbg;
            bool hasFrame = cam.GetLastFrame(dbg);
            std::fprintf(
                stderr,
                "[SandboxCamera] CapturePhotoToFile failed. hasLastFrame=%d format=%s size=%ux%u backendError='%s'\n",
                hasFrame ? 1 : 0,
                hasFrame ? NkPixelFormatToString(dbg.format) : "N/A",
                hasFrame ? dbg.width : 0u,
                hasFrame ? dbg.height : 0u,
                cam.GetLastError().c_str()
            );
        }
    };

    auto toggleRecord = [&]()
    {
        if (!isRecording)
        {
            if (!cameraStreaming)
                return;
            NkVideoRecordConfig vrCfg;
            vrCfg.outputPath  = "";       // nom auto = video_YYYYMMDD_HHMMSS.mp4
            vrCfg.bitrateBps  = 4000000;  // 4 Mbps
            vrCfg.videoCodec  = "h264";
            vrCfg.container   = "mp4";
            vrCfg.mode        = recordMode;
            if (recordMode == NkVideoRecordConfig::Mode::IMAGE_SEQUENCE_ONLY)
                vrCfg.videoCodec = "images";
            isRecording = cam.StartVideoRecord(vrCfg);
            if (isRecording)
            {
                std::fprintf(
                    stderr,
                    "[SandboxCamera] Recording started (mode=%s, auto output path).\n",
                    recordModeToString(recordMode)
                );
            }
            else
            {
                std::fprintf(
                    stderr,
                    "[SandboxCamera] Recording start failed: %s\n",
                    cam.GetLastError().c_str()
                );
            }
        }
        else
        {
            cam.StopVideoRecord();
            isRecording = false;
            std::fprintf(stderr, "[SandboxCamera] Recording stopped.\n");
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
            "[SandboxCamera] Record mode switched to %s.\n",
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

        case NkKey::NK_SPACE:
            capturePhoto();
            break;

        case NkKey::NK_R:
            toggleRecord();
            break;

        case NkKey::NK_M:
            cycleRecordMode();
            break;

        case NkKey::NK_EQUALS:
            zoomLevel = std::min(zoomLevel + 0.25f, 5.f);
            if (cameraStreaming)
                cam.SetZoom(zoomLevel);
            break;

        case NkKey::NK_MINUS:
            zoomLevel = std::max(zoomLevel - 0.25f, 1.f);
            if (cameraStreaming)
                cam.SetZoom(zoomLevel);
            break;

        case NkKey::NK_T:
            torchOn = !torchOn;
            if (cameraStreaming)
                cam.SetTorch(torchOn);
            break;

        case NkKey::NK_F:
            if (cameraStreaming)
                cam.SetAutoFocus(true);
            break;

        case NkKey::NK_NUM1:
        case NkKey::NK_NUM2:
        case NkKey::NK_NUM3:
        {
            NkU32 newIdx = static_cast<NkU32>(key) - static_cast<NkU32>(NkKey::NK_NUM1);
            switchCameraToIndex(newIdx);
            break;
        }

        default:
            break;
        }
    };

    auto handlePointerPress = [&](NkI32 px, NkI32 py)
    {
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
        setFocusFromScreenPoint(static_cast<float>(px), static_cast<float>(py));
    };

    es.SetEventCallback<NkWindowCloseEvent>([&](auto*)
    {
        std::fprintf(stderr, "[SandboxCamera] Window close request received.\n");
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
            "[SandboxCamera] KeyPress key=%s scancode=%s native=%u\n",
            NkKeyToString(ev->GetKey()),
            NkScancodeToString(ev->GetScancode()),
            ev->GetNativeKey()
        );
        handleActionKey(ev->GetKey());
    });

    // Clic/touch: UI mobile ou point de focus.
    es.SetEventCallback<NkMouseButtonPressEvent>([&](NkMouseButtonPressEvent* ev)
    {
        if (ev->GetButton() == NkMouseButton::NK_MB_LEFT)
            handlePointerPress(ev->GetX(), ev->GetY());
    });

    es.SetEventCallback<NkTouchBeginEvent>([&](NkTouchBeginEvent* ev)
    {
        if (ev->GetNumTouches() > 0)
        {
            const auto& t = ev->GetTouch(0);
            handlePointerPress(static_cast<NkI32>(t.clientX), static_cast<NkI32>(t.clientY));
        }
    });

    // =========================================================================
    // 7. Boucle principale
    // =========================================================================
#if defined(NKENTSEU_PLATFORM_NOOP)
    int headlessFrames = 2;
#endif
    NkU32 fallbackTick = 0;
    while (window.IsOpen())
    {
#if defined(NKENTSEU_PLATFORM_NOOP)
        if (--headlessFrames <= 0)
        {
            window.Close();
        }
#endif
        es.PollEvents();
        if (!window.IsOpen())
            break;
        updateLayout();

        if (capturePreviewTicks > 0)
            --capturePreviewTicks;

        ++fallbackTick;

        if (!cameraStreaming && !devices.empty())
        {
            if ((fallbackTick % 120u) == 0u)
            {
                NkU32 idx = (selectedCam < devices.size()) ? selectedCam : 0;
                cameraStreaming = tryStartCamera(idx);
            }
        }

        // --- Récupérer la frame la plus récente ---
        NkCameraFrame rawFrame;
        bool gotFrameThisTick = false;
        if (cameraStreaming && cam.DrainFrameQueue(rawFrame))
        {
            // Convertir en RGBA8 si nécessaire (NV12/YUV420/BGRA → RGBA8)
            if (NkCameraSystem::ConvertToRGBA8(rawFrame) && rawFrame.IsValid())
            {
                displayFrame    = std::move(rawFrame);
                hasDisplayFrame = true;
                gotFrameThisTick = true;
                lastFrameTimestamp = std::chrono::steady_clock::now();
            }
        }

        if (cameraStreaming && !gotFrameThisTick)
        {
            const auto now = std::chrono::steady_clock::now();
            const auto silentMs = std::chrono::duration_cast<std::chrono::milliseconds>(
                now - lastFrameTimestamp).count();

            if (silentMs > 4000)
            {
                std::fprintf(
                    stderr,
                    "[SandboxCamera] No frame received for %.2fs on camera %u (backendError='%s').\n",
                    static_cast<double>(silentMs) / 1000.0,
                    selectedCam,
                    cam.GetLastError().c_str()
                );
                if (cam.GetLastError().empty() && !warnedNoFrameTransport)
                {
                    std::fprintf(
                        stderr,
                        "[SandboxCamera] Device opened but no frame payload is arriving. "
                        "In WSL2 this usually means USB camera transport is not delivering video packets.\n"
                    );
                    warnedNoFrameTransport = true;
                }

                const NkU32 previousCam = selectedCam;
                cam.StopStreaming();
                cameraStreaming = false;
                hasDisplayFrame = false;

                profileStartIndex = (profileStartIndex + 1u) % startProfileCount;
                std::fprintf(stderr, "[SandboxCamera] Restarting current camera with fallback profiles...\n");
                bool recovered = tryStartCamera(previousCam);

                if (!recovered && devices.size() > 1)
                {
                    std::fprintf(stderr, "[SandboxCamera] Trying another camera device...\n");
                    for (NkU32 step = 1; step <= devices.size(); ++step)
                    {
                        NkU32 idx = (previousCam + step) % static_cast<NkU32>(devices.size());
                        if (tryStartCamera(idx))
                        {
                            cameraStreaming = true;
                            recovered = true;
                            break;
                        }
                    }

                    if (!recovered)
                    {
                        std::fprintf(
                            stderr,
                            "[SandboxCamera] Failed to recover stream on alternate devices.\n"
                        );
                    }
                }
                else if (recovered)
                {
                    cameraStreaming = true;
                }

                lastFrameTimestamp = now;
            }
        }
        else if (!cameraStreaming)
        {
            lastFrameTimestamp = std::chrono::steady_clock::now();
        }

        // --- Rendu ---
        renderer.BeginFrame();

        if (hasDisplayFrame && displayFrame.IsValid())
        {
            // Afficher la frame caméra pixel par pixel dans le renderer software
            // (En production : uploader dans une texture GPU via OpenGL/Vulkan/D3D11)
            NkU32 fw = displayFrame.width;
            NkU32 fh = displayFrame.height;

            // Scale pour remplir la zone de contenu (safe area).
            float scaleX = static_cast<float>(contentW) / static_cast<float>(fw);
            float scaleY = static_cast<float>(contentH) / static_cast<float>(fh);

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
                    NkI32 sx = contentX + static_cast<NkI32>(x * scaleX);
                    NkI32 sy = contentY + static_cast<NkI32>(y * scaleY);

                    // Remplir le carré step×step (approx)
                    NkU32 sw = static_cast<NkU32>(step * scaleX) + 1;
                    NkU32 sh = static_cast<NkU32>(step * scaleY) + 1;
                    renderer.FillRect(sx, sy, sw, sh, pix);
                }
            }
        }
        else
        {
            // Fallback visuel sans caméra: garder une fenêtre active et informative.
            NkU32 W = contentW, H = contentH;
            NkU32 pulse = (fallbackTick / 2u) % 255u;
            renderer.FillRect(contentX, contentY, W, H, Renderer::PackColor(8, 12, static_cast<NkU8>(20 + pulse / 8u)));
            renderer.DrawRect(contentX + 30, contentY + 30, W - 60, H - 120, 0x4466AAFF);
            renderer.DrawLine(contentX + 30, contentY + 30, contentX + static_cast<NkI32>(W - 30), contentY + static_cast<NkI32>(H - 90), 0x6688CCFF);
            renderer.DrawLine(contentX + static_cast<NkI32>(W - 30), contentY + 30, contentX + 30, contentY + static_cast<NkI32>(H - 90), 0x6688CCFF);
            renderer.FillCircle(contentX + static_cast<NkI32>(W / 2), contentY + static_cast<NkI32>(H / 2 - 20), 24, 0xCC4444FF);
        }

        // --- Overlay HUD ---
        NkU32 W = contentW;
        NkU32 H = contentH;
        NkI32 X = contentX;
        NkI32 Y = contentY;

        // Indicateur d'enregistrement (rouge clignotant)
        if (isRecording)
        {
            float dur = cam.GetRecordingDurationSeconds();
            bool  blink = static_cast<int>(dur * 2) % 2 == 0;
            if (blink)
                renderer.FillCircle(X + static_cast<NkI32>(W - 30), Y + 30, 12, 0xFF2222FF);
        }

        // Barre d'infos en bas (fond semi-transparent)
        renderer.FillRect(X, Y + static_cast<NkI32>(H) - 40, W, 40, 0x000000AA);

        // Durée d'enregistrement (barres horizontales = secondes)
        if (isRecording)
        {
            float dur = cam.GetRecordingDurationSeconds();
            NkU32 barW = static_cast<NkU32>(dur * 10.f); // 10 px par seconde
            renderer.FillRect(X + 10, Y + static_cast<NkI32>(H) - 30, std::min(barW, W - 20), 6, 0xFF4444FF);
        }

        // Zone de focus (dernier point touché/clic, ou centre par défaut)
        NkI32 fx = X + static_cast<NkI32>(focusNx * static_cast<float>(W)) - 50;
        NkI32 fy = Y + static_cast<NkI32>(focusNy * static_cast<float>(H)) - 50;
        renderer.DrawRect(fx, fy, 100, 100, 0x44FF44FF);
        renderer.DrawLine(fx + 50, fy, fx + 50, fy + 10, 0x44FF44FF);
        renderer.DrawLine(fx + 50, fy + 90, fx + 50, fy + 100, 0x44FF44FF);

        // Miniature de la dernière capture photo.
        if (hasCapturePreview && capturePreviewTicks > 0 && capturePreviewFrame.IsValid())
        {
            const NkU32 tw = 240;
            const NkU32 th = 135;
            const NkI32 tx = X + static_cast<NkI32>(W) - static_cast<NkI32>(tw) - 16;
            const NkI32 ty = Y + 16;
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

    // =========================================================================
    // 8. Nettoyage
    // =========================================================================
    if (isRecording) cam.StopVideoRecord();
    if (cameraStreaming) cam.StopStreaming();
    // NkClose() appelle aussi NkCameraSystem::Shutdown()
    NkClose();
    return 0;
}
