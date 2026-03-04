# 23_android_sdl3_ndk_mk

Exemple SDL3 qui montre:
- une vraie fenetre SDL3 avec rendu 2D (soleil + planete + lune en orbite)
- une entree SDL3 callbacks unique (`SDL_AppInit/Event/Iterate/Quit`) pour desktop + Android
- un rendu 3D logiciel CPU from-scratch (pas d'OpenGL, pas de pipeline GPU custom)
- un DSL Jenga avec `newoption(...)`
- des `filter("options:...")` et `filter("action:...")`
- un build desktop (Windows/Linux) + un build Android via `ndk-build` et `Android.mk`

## Architecture des fichiers source

- `AndroidManifest.xml`: entree Android via `org.libsdl.app.SDLActivity`
- `src/app_entry.h`: `NkErrorHandler` centralise (gestion d'erreurs)
- `src/application.h` + `src/application.cpp`: classe `Application` et rendu 3D logiciel from-scratch (CPU)
- `src/main_android.cpp`: point d'entree SDL3 callbacks (`SDL_AppInit`, `SDL_AppEvent`, `SDL_AppIterate`, `SDL_AppQuit`) utilise sur desktop et Android

## Controles (PC + Android)

- Rotation camera:
  - PC: glisser avec clic gauche souris
  - Android: glisser avec 1 doigt
- Zoom:
  - PC: molette souris
  - Android: pinch 2 doigts
- Suivre une planete:
  - PC: clic droit sur un astre (ou touches `1`/`2`/`3`/`4`)
  - Android: tap sur un astre
- Reset vue:
  - PC: touche `R`
  - Android: double-tap sur une zone vide

## Prerequis

- Jenga installe et disponible via `jenga`
- SDL3 present dans `externals/SDL3` (deja fourni dans cet exemple) ou via `SDL3_ROOT`
- Pour Android:
  - `ANDROID_SDK_ROOT`
  - `ANDROID_NDK_ROOT` (ou `ANDROID_NDK_HOME`)

## Layouts SDL3 supportes (Android.mk)

Le `Android.mk` gere automatiquement:

1. Layout classique:
```text
<SDL3_ROOT>/include/SDL3/SDL.h
<SDL3_ROOT>/lib/<abi>/libSDL3.so
```

2. Layout Prefab d'un `.aar` SDL3:
```text
<SDL3_ROOT>/prefab/modules/SDL3-Headers/include/SDL3/SDL.h
<SDL3_ROOT>/prefab/modules/SDL3-shared/libs/android.<abi>/libSDL3.so
```

Si vous avez uniquement le fichier `.aar`, extrayez les `.so` une fois vers `lib/<abi>`:

```powershell
tar -xf externals\SDL3\lib\SDL3-3.4.0.aar -C externals\SDL3\_aar_extract
mkdir externals\SDL3\lib\arm64-v8a
mkdir externals\SDL3\lib\x86_64
copy externals\SDL3\_aar_extract\prefab\modules\SDL3-shared\libs\android.arm64-v8a\libSDL3.so externals\SDL3\lib\arm64-v8a\
copy externals\SDL3\_aar_extract\prefab\modules\SDL3-shared\libs\android.x86_64\libSDL3.so externals\SDL3\lib\x86_64\
```

Note:
- L'exemple utilise `SDLActivity`, qui charge `libmain.so`.
- Le projet Android est donc compile avec `targetname("main")`.
- Le `classes.jar` Java de SDL3 est extrait automatiquement depuis `SDL3-3.4.0.aar` par Jenga.

## Build + run desktop (Windows)

Depuis le dossier de l'exemple:

```powershell
jenga build --no-daemon `
  --platform Windows-x86_64 `
  --target SDL3NativeDemo `
  --jenga-file 23_android_sdl3_ndk_mk.jenga
```

Pour l'execution, SDL3.dll doit etre trouvable:

```powershell
$env:PATH = "$PWD\\externals\\SDL3\\bin;$env:PATH"
jenga run SDL3NativeDemo --no-daemon `
  --platform Windows-x86_64 `
  --jenga-file 23_android_sdl3_ndk_mk.jenga
```

Test automatique (fermeture apres N secondes):

```powershell
$env:JENGA_SDL3_TEST_SECONDS = "5"
jenga run SDL3NativeDemo --no-daemon `
  --platform Windows-x86_64 `
  --jenga-file 23_android_sdl3_ndk_mk.jenga
```

## Build desktop (WSL2 / Linux)

Prerequis: `libsdl3` installe dans le systeme Linux (paquet distro).

```bash
jenga build \
  --no-daemon \
  --platform Linux-x86_64 \
  --target SDL3NativeDemo \
  --jenga-file 23_android_sdl3_ndk_mk.jenga
```

## Build Android natif (sans ndk-build)

```bash
jenga build \
  --no-daemon \
  --platform Android-arm64 \
  --target SDL3NativeDemo \
  --jenga-file 23_android_sdl3_ndk_mk.jenga
```

## Build Android via Android.mk (ndk-build)

```bash
export SDL3_ROOT=/absolute/path/to/SDL3

jenga build \
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
- `--android-ndk-mk-mode split|universal|both` pilote la sortie APK en mode ndk-mk.
- `--android-abis armeabi-v7a,arm64-v8a,x86,x86_64` permet de choisir les ABIs a compiler.
- `--with-sdl3` et `--sdl3-root` alimentent les filtres `options:` dans le DSL.
- Le fichier `Android.mk` lit `SDL3_ROOT` via la variable d'environnement.
- Pour tests CLI desktop, `JENGA_SDL3_TEST_SECONDS` permet de quitter automatiquement.

## Modes APK ndk-mk (split / universal / both)

Exemples:

```bash
# APK par ABI seulement
jenga build --no-daemon --platform Android-arm64 --target SDL3NativeDemo \
  --android-build-system ndk-mk \
  --android-ndk-mk-mode split \
  --android-abis arm64-v8a,x86_64 \
  --jenga-file 23_android_sdl3_ndk_mk.jenga

# APK universel seulement
jenga build --no-daemon --platform Android-arm64 --target SDL3NativeDemo \
  --android-build-system ndk-mk \
  --android-ndk-mk-mode universal \
  --android-abis armeabi-v7a,arm64-v8a,x86,x86_64 \
  --jenga-file 23_android_sdl3_ndk_mk.jenga

# split + universel (comportement par defaut quand plusieurs ABIs sont cibles)
jenga build --no-daemon --platform Android-arm64 --target SDL3NativeDemo \
  --android-build-system ndk-mk \
  --android-ndk-mk-mode both \
  --android-abis armeabi-v7a,arm64-v8a,x86,x86_64 \
  --jenga-file 23_android_sdl3_ndk_mk.jenga
```
