# Android with NKWindow (safe area, rotation, touch, camera)

This guide documents how to build and program the Android side of example 27 with NKWindow.

Scope:
- Safe area handling (notch/system bars)
- Screen rotation policy (auto vs lock)
- Runtime orientation control from C++
- Touch-first input model
- Camera behavior notes for emulator vs real device

## 1) Build and run

From Windows PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\Projets\MacShared\Projets\Jenga\scripts\jenga27_android_only.ps1"
```

After Android success, build Windows + Web:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\Projets\MacShared\Projets\Jenga\scripts\jenga27_windows_web_only.ps1" -Clean
```

## 2) Android config in Jenga DSL

In `27_nk_window.jenga`, for Android projects:

```python
androidapplicationid("com.nkentseu.sandbox.camera")
androidminsdk(24)
androidtargetsdk(34)
androidcompilesdk(34)
androidabis(["armeabi-v7a", "arm64-v8a", "x86", "x86_64"])
androidnativeactivity(True)
androidallowrotation(True)  # Auto-rotate allowed
androidpermissions(["android.permission.CAMERA"])  # only for camera apps
```

Notes:
- `androidallowrotation(True)` => generated manifest uses free rotation mode.
- `androidallowrotation(False)` => portrait lock at manifest level.
- `androidscreenorientation("...")` can force a specific Android orientation constant.

## 3) Safe area programming model (C++)

Use window size + safe insets every frame (or on resize), then render in content rect:

```cpp
NkVec2u s = window.GetSize();
NkSafeAreaInsets insets = window.GetSafeAreaInsets();

NkU32 insetL = static_cast<NkU32>(std::max(0.0f, insets.left));
NkU32 insetR = static_cast<NkU32>(std::max(0.0f, insets.right));
NkU32 insetT = static_cast<NkU32>(std::max(0.0f, insets.top));
NkU32 insetB = static_cast<NkU32>(std::max(0.0f, insets.bottom));

NkI32 contentX = static_cast<NkI32>(insetL);
NkI32 contentY = static_cast<NkI32>(insetT);
NkU32 contentW = s.x - insetL - insetR;
NkU32 contentH = s.y - insetT - insetB;
```

Then:
- place buttons/HUD inside `(contentX, contentY, contentW, contentH)`
- scale camera preview to `contentW/contentH`
- avoid drawing critical UI in cutout/system bar areas

## 4) Runtime orientation control from C++

NKWindow exposes runtime APIs:

```cpp
if (window.SupportsOrientationControl()) {
    window.SetAutoRotateEnabled(true); // allow auto-rotate
    // window.SetAutoRotateEnabled(false); // lock current orientation
    // window.SetScreenOrientation(NkScreenOrientation::NK_SCREEN_ORIENTATION_PORTRAIT);
    // window.SetScreenOrientation(NkScreenOrientation::NK_SCREEN_ORIENTATION_LANDSCAPE);
}
```

Recommended split:
- Product default policy in DSL (`androidallowrotation` / `androidscreenorientation`)
- Runtime temporary override in C++ when needed (video, minigame, capture mode)

## 5) Touch-first event loop

On Android emulator/device, keyboard events are often limited. Keep touch actions for core controls:
- photo
- record
- mode switch
- camera switch
- focus point tap

Pattern:

```cpp
es.SetEventCallback<NkTouchBeginEvent>([&](NkTouchBeginEvent* ev) {
    if (ev->GetNumTouches() > 0) {
        auto t = ev->GetTouch(0);
        handlePointerPress(static_cast<NkI32>(t.clientX), static_cast<NkI32>(t.clientY));
    }
});
```

## 6) Camera on emulator vs real device

What is expected:
- Many emulators have partial/no Camera2 NDK support.
- Real Android device is the reference target for camera validation.

If camera fails:
1. Confirm app has `android.permission.CAMERA` in manifest.
2. Allow permission in Android settings/app prompt.
3. Check logs for backend message (permission denied / no Camera2 YUV device).
4. Validate on a physical device for final camera test.

## 7) Practical checklist before release

- [ ] Safe area respected for all overlays/buttons
- [ ] Resize/orientation updates call `renderer.Resize(...)`
- [ ] Touch-only controls can drive all camera features
- [ ] Rotation policy tested in both modes:
  - auto rotate allowed
  - locked orientation
- [ ] Camera tested on at least one physical Android device
- [ ] Build scripts pass:
  - `jenga27_android_only.ps1`
  - `jenga27_windows_web_only.ps1`

