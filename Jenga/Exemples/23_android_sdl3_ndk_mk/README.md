# 23_android_sdl3_ndk_mk

Exemple Android NativeActivity qui montre:
- un DSL Jenga avec `newoption(...)`
- des `filter("options:...")` et `filter("action:...")`
- un build Android via `ndk-build` avec un `Android.mk` manuel

## Prerequis

- `ANDROID_SDK_ROOT`
- `ANDROID_NDK_ROOT` (ou `ANDROID_NDK_HOME`)
- SDL3 Android prebuilt (`lib/<abi>/libSDL3.so` + `include/SDL3/...`)

## Structure attendue pour SDL3

```text
<SDL3_ROOT>/
  include/SDL3/SDL.h
  lib/arm64-v8a/libSDL3.so
  lib/x86_64/libSDL3.so
```

## Build Jenga natif (sans ndk-build)

```bash
python -m Jenga.Jenga build \
  --no-daemon \
  --platform Android-arm64 \
  --target SDL3NativeDemo \
  --jenga-file 23_android_sdl3_ndk_mk.jenga
```

## Build via Android.mk (ndk-build)

```bash
export SDL3_ROOT=/absolute/path/to/SDL3-android

python -m Jenga.Jenga build \
  --no-daemon \
  --platform Android-arm64 \
  --target SDL3NativeDemo \
  --android-build-system ndk-mk \
  --with-sdl3 \
  --sdl3-root "$SDL3_ROOT" \
  --jenga-file 23_android_sdl3_ndk_mk.jenga
```

Notes:
- `--android-build-system ndk-mk` active le mode Android.mk.
- `--with-sdl3` et `--sdl3-root` alimentent les filtres `options:` dans le DSL.
- Le fichier `Android.mk` lit `SDL3_ROOT` via la variable d'environnement.
