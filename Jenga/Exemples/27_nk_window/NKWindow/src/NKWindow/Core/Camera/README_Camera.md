# NkCameraSystem — Système de Capture Caméra Physique + Caméra Virtuelle

## État de fonctionnement par plateforme

| Plateforme | Backend | Streaming | Photo | Vidéo | IMU/Orientation |
|---|---|---|---|---|---|
| **Windows** | Media Foundation | ✅ | ✅ PNG/PPM | ✅ MP4/H.264 | ❌ (pas d'IMU standard) |
| **Linux** | V4L2 mmap | ✅ | ✅ PPM | ✅ MP4 (ffmpeg requis) | ✅ IIO sysfs (laptop/tablette) |
| **macOS** | AVFoundation | ✅ | ✅ PNG | ✅ MP4/H.264 | ❌ (pas d'IMU) |
| **iOS** | AVFoundation | ✅ | ✅ JPEG natif | ✅ MP4/H.264 | ✅ CMMotionManager (yaw/pitch/roll réels) |
| **Android** | Camera2 NDK | ✅ | ✅ PPM | ✅ via MediaCodec | ✅ ASensorManager (accel+gyro) |
| **WebAssembly** | getUserMedia | ✅ | ✅ PNG (download) | ✅ WebM/MP4 | ✅ DeviceOrientationEvent |

---

## 1. Accéder à une caméra parmi plusieurs

```cpp
// Énumérer TOUTES les caméras du système
auto devices = NkCamera().EnumerateDevices();
// devices[0] = webcam principale (ou caméra arrière sur mobile)
// devices[1] = deuxième webcam (ou caméra frontale sur mobile)
// devices[N].name    = "Logitech HD Pro Webcam C920"
// devices[N].facing  = NK_CAMERA_FACING_BACK / FRONT / EXTERNAL
// devices[N].modes[] = résolutions + fps supportés

// Ouvrir la caméra N
NkCameraConfig cfg;
cfg.deviceIndex = 1;              // ← index de la caméra souhaitée
cfg.preset      = NK_CAM_RES_HD; // 1280×720
cfg.fps         = 30;
NkCamera().StartStreaming(cfg);

// Changer de caméra à la volée
NkCamera().StopStreaming();
cfg.deviceIndex = 2;
NkCamera().StartStreaming(cfg);
```

## 2. Gérer plusieurs caméras simultanément

```cpp
NkMultiCamera multi;

// Ouvrir 2 caméras en même temps (backends indépendants)
NkCameraConfig cfg0; cfg0.deviceIndex = 0; cfg0.preset = NK_CAM_RES_HD;
NkCameraConfig cfg1; cfg1.deviceIndex = 1; cfg1.preset = NK_CAM_RES_VGA;

auto& cam0 = multi.Open(0, cfg0);  // caméra 0
auto& cam1 = multi.Open(1, cfg1);  // caméra 1

cam0.EnableQueue(4);
cam1.EnableQueue(4);

// Dans la boucle principale:
NkCameraFrame f0, f1;
if (cam0.DrainFrame(f0)) { NkCameraSystem::ConvertToRGBA8(f0); /* afficher f0 */ }
if (cam1.DrainFrame(f1)) { NkCameraSystem::ConvertToRGBA8(f1); /* afficher f1 */ }

// Capturer photo depuis la caméra 1
cam1.CapturePhotoToFile("photo_cam1.ppm");

// Fermer une caméra
multi.Close(1);
multi.CloseAll();
```

## 3. Caméra virtuelle mappée sur la caméra réelle

La caméra physique fournit des données d'orientation via son IMU (gyroscope + accéléromètre).  
Ces données pilotent automatiquement une **NkCamera2D** (la caméra virtuelle du monde 2D).

```
Mouvement physique (téléphone/tablette)
         ↓
    IMU → yaw / pitch / roll
         ↓
  NkCameraSystem::UpdateVirtualCamera(dt)
         ↓
    NkCamera2D::SetPosition(panX, panY)  ← mode translation
    ou NkCamera2D::SetRotation(angle)    ← mode rotation
         ↓
  renderer.SetTransform(virtualCam.GetTransform())
         ↓
  Monde 2D qui "se déplace" selon l'orientation de l'appareil
```

### Code

```cpp
NkCamera2D virtualCam;
virtualCam.SetViewport(1280.f, 720.f);
virtualCam.SetPosition(1000.f, 750.f); // départ au centre du monde

// 1. Lier la caméra virtuelle
NkCamera().SetVirtualCameraTarget(&virtualCam);

// 2. Configurer la sensibilité
NkCameraSystem::VirtualCameraMapConfig cfg;
cfg.yawSensitivity   = 5.f;   // 1° de rotation physique → 5px de déplacement
cfg.pitchSensitivity = 5.f;
cfg.translationScale = 10.f;  // > 0 → mode translation (déplacement)
                               // = 0 → mode rotation seulement
cfg.smoothing        = true;
cfg.smoothFactor     = 0.12f; // 0.05 = très lisse, 1.0 = instantané
cfg.invertY          = true;  // inversion Y naturelle
NkCamera().SetVirtualCameraMapConfig(cfg);

// 3. Activer le mapping
NkCamera().SetVirtualCameraMapping(true);

// 4. Appeler CHAQUE FRAME dans la boucle principale
NkCamera().UpdateVirtualCamera(dt);

// 5. Utiliser la caméra virtuelle pour le rendu
renderer.SetTransform(virtualCam.GetTransform());
// ... dessiner le monde 2D ...
renderer.SetTransform(NkTransform2D{}); // reset pour l'UI

// Désactiver
NkCamera().SetVirtualCameraMapping(false);

// Lire l'orientation brute
NkCameraOrientation orient;
NkCamera().GetCurrentOrientation(orient);
// orient.yaw   = rotation gauche/droite [degrés]
// orient.pitch = inclinaison avant/arrière [degrés]
// orient.roll  = rotation sur l'axe Z [degrés]
```

### Disponibilité de l'IMU

| Plateforme | IMU disponible | Source | Données |
|---|---|---|---|
| iOS | ✅ Toujours | CMMotionManager | yaw + pitch + roll précis (fusion sensor) |
| Android | ✅ Toujours | ASensorManager | pitch/roll (accel) + yaw intégré (gyro) |
| WASM (mobile) | ✅ Si HTTPS | DeviceOrientationEvent | alpha/beta/gamma |
| WASM (desktop) | ❌ | — | — |
| Linux | ⚠️ Optionnel | IIO sysfs | pitch/roll (accel uniquement) |
| Windows | ❌ | — | — |
| macOS | ❌ | — | — |

Sur desktop sans IMU, `UpdateVirtualCamera()` est un **no-op** — la caméra virtuelle reste pilotable avec le clavier/souris via `NkCamera2DController`.

---

## 4. Streaming et frames

```cpp
NkCamera().StartStreaming(cfg);
NkCamera().EnableFrameQueue(4); // file thread-safe recommandée

// Dans la boucle:
NkCameraFrame frame;
if (NkCamera().DrainFrameQueue(frame)) {
    NkCameraSystem::ConvertToRGBA8(frame); // NV12/YUYV/BGRA → RGBA8
    // frame.data = pixels RGBA8
    // frame.width, frame.height, frame.stride
    NkU32 pixel = frame.GetPixelRGBA(x, y); // accès pixel direct
}
```

## 5. Photo et vidéo

```cpp
// Photo → fichier (nom auto si path="")
std::string path = NkCamera().CapturePhotoToFile("photo.ppm");

// Photo → mémoire
NkPhotoCaptureResult res;
NkCamera().CapturePhoto(res);
if (res) NkCameraSystem::SaveFrameToFile(res.frame, "photo.png");

// Vidéo
NkVideoRecordConfig vrCfg;
vrCfg.outputPath = "video.mp4"; // ou "" pour nom auto
vrCfg.bitrateBps = 4000000;
NkCamera().StartVideoRecord(vrCfg);
float dur = NkCamera().GetRecordingDurationSeconds();
NkCamera().StopVideoRecord();
```

## 6. Contrôles physiques

```cpp
NkCamera().SetZoom(2.f);             // ×2 zoom (optique/numérique)
NkCamera().SetTorch(true);           // lampe LED (iOS/Android)
NkCamera().SetAutoFocus(true);       // AF continu
NkCamera().SetFocusPoint(0.5f,0.5f);// focus au centre
NkCamera().SetAutoExposure(true);
NkCamera().SetAutoWhiteBalance(true);
// Retourne false si non supporté sur la plateforme/device courant
```

## 7. Notes d'intégration

### iOS
```xml
<!-- Info.plist obligatoire -->
<key>NSCameraUsageDescription</key>
<string>Accès caméra pour preview et capture</string>
```

### Android  
```xml
<!-- AndroidManifest.xml -->
<uses-permission android:name="android.permission.CAMERA"/>
<uses-feature android:name="android.hardware.camera2" android:required="true"/>
```
```cmake
# CMakeLists.txt
target_link_libraries(MyApp camera2ndk mediandk android log)
```

### Linux
- Format capture: YUYV (natif) → converti en RGBA8 par `ConvertToRGBA8()`
- Vidéo: `ffmpeg` doit être installé (`apt install ffmpeg`)
- Photo: format PPM (pas de dépendance externe)
- IMU: `/sys/bus/iio/devices/iio:device*/in_accel_*` (accéléromètre IIO)

### WebAssembly
- Requiert **HTTPS** ou **localhost**
- `getUserMedia()` requiert un geste utilisateur (bouton)
- Orientation: `DeviceOrientationEvent` (navigateur mobile uniquement)

### Windows
- Format natif: NV12 (converti par `ConvertToRGBA8()`)
- Libs: `mf.lib mfplat.lib mfreadwrite.lib mfuuid.lib ole32.lib`
- H.264 encode via Media Foundation Transform (intégré Windows 7+)
