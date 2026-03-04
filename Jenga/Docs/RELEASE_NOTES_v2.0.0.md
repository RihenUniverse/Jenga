# Jenga Build System — Release v2.0.1

**Date de release : 23 Février 2026**

> **Jenga** est un système de build cross-plateforme Python pour projets C/C++.
> Il remplace les Makefiles et CMakeLists.txt par une syntaxe Python claire et
> un support natif de Windows, Linux, Android, Web/WASM, macOS, iOS, Xbox et HarmonyOS.

---

## 🚀 Installation rapide

```bash
pip install jenga-build
```

Ou depuis les artefacts de cette release :

```bash
pip install jenga-2.0.1-py3-none-any.whl
```

**Prérequis :** Python 3.8 ou supérieur — aucune autre dépendance obligatoire.

---

## ✅ Plateformes supportées

| Plateforme | Statut | Compilateurs testés |
|-----------|--------|---------------------|
| **Windows x64** | ✅ Production Ready | clang 21 (MSYS64/UCRT64), g++ 15, MSVC 14.44 |
| **Linux x64** | ✅ Production Ready | clang 14, g++ 11 (Ubuntu 22.04 / WSL2) |
| **Android** | ✅ Production Ready | NDK r27c (arm64-v8a, armeabi-v7a, x86, x86_64) |
| **Web / WASM** | ✅ Production Ready | emsdk 4.0.22 |
| **macOS** | ✅ Prêt (nécessite macOS) | Apple Clang (xcrun) |
| **iOS / tvOS / watchOS / visionOS** | ✅ Prêt (nécessite macOS + Xcode) | Apple Clang via xcrun |
| **Xbox One / Series X\|S** | ✅ Prêt (nécessite Windows + GDK) | MSVC + Microsoft GDK |
| **HarmonyOS** | ✅ Prêt (nécessite SDK HarmonyOS) | LLVM du NDK OpenHarmony |

---

## 🆕 Nouveautés de cette version

### Génération automatique de scripts runners WebAssembly

Après chaque build WASM réussi, Jenga génère maintenant automatiquement :
- `run_<Project>.bat` (Windows)
- `run_<Project>.sh` (Linux/macOS)

Ces scripts lancent un serveur HTTP Python local pour contourner les restrictions
CORS des navigateurs. Double-cliquez simplement sur `run_<Project>.bat` et ouvrez
`http://localhost:8080/<Project>.html`.

```
Build/Bin/Release-Web/WasmApp/
├── WasmApp.html
├── WasmApp.js
├── WasmApp.wasm
├── run_WasmApp.bat   ← nouveau
└── run_WasmApp.sh    ← nouveau
```

### Nouvelles fonctions DSL HarmonyOS

```python
with project("MyApp"):
    harmonysdk("/opt/harmonyos/sdk")    # nouveau
    harmonyminsdk(9)                     # nouveau (API level minimum)
```

### Support visionOS complet

`TargetOS.VISIONOS` est maintenant correctement géré dans la détection de toolchain,
la validation de plateforme hôte et la factory de builders.

```python
with filter("system:visionOS"):
    visionosminsdk("1.0")
```

---

## 🤖 Android NDK — Guide de démarrage

### Prérequis

| Outil | Version testée | Installation |
|-------|---------------|--------------|
| Android NDK | r27c (27.0.12077973) | Android Studio SDK Manager |
| Android SDK | API 34 | Android Studio SDK Manager |
| Java JDK | 17+ | `winget install Microsoft.OpenJDK.17` |
| `aapt2` | inclus SDK Build-Tools | via SDK Manager |

Définir les variables d'environnement :

```bash
# Windows
set ANDROID_SDK_ROOT=C:\Users\%USERNAME%\AppData\Local\Android\Sdk
set ANDROID_NDK_ROOT=%ANDROID_SDK_ROOT%\ndk\27.0.12077973

# Linux / macOS
export ANDROID_SDK_ROOT=$HOME/Android/Sdk
export ANDROID_NDK_ROOT=$ANDROID_SDK_ROOT/ndk/27.0.12077973
```

### Exemple minimal

```python
# android_app.jenga
import os
from Jenga import *
from Jenga.GlobalToolchains import RegisterJengaGlobalToolchains

with workspace("AndroidDemo"):
    RegisterJengaGlobalToolchains()
    configurations(["Debug", "Release"])
    targetoses([TargetOS.ANDROID])
    targetarchs([TargetArch.ARM64])

    androidsdkpath(os.getenv("ANDROID_SDK_ROOT", ""))
    androidndkpath(os.getenv("ANDROID_NDK_ROOT", ""))

    with project("MyApp"):
        windowedapp()                              # NativeActivity
        language("C++")
        cppdialect("C++17")
        files(["src/**.cpp"])
        androidapplicationid("com.monentreprise.myapp")
        androidminsdk(24)                          # Android 7.0+
        androidtargetsdk(34)
        androidabis(["arm64-v8a", "x86_64"])       # device + émulateur
        androidnativeactivity(True)
```

```bash
jenga build android_app.jenga --platform Android-arm64
```

### Ce que génère Jenga automatiquement

```
Build/Bin/Debug-Android/MyApp/
├── MyApp.apk              ← APK universel signé (debug keystore)
├── lib/
│   ├── arm64-v8a/
│   │   └── libMyApp.so
│   └── x86_64/
│       └── libMyApp.so
└── AndroidManifest.xml
```

### APK multi-ABI (Universal APK)

Un seul `jenga build` génère un APK contenant **toutes les architectures** déclarées :

```python
androidabis(["armeabi-v7a", "arm64-v8a", "x86", "x86_64"])
# → APK unique compatible smartphones, tablettes et émulateurs
```

### Fonctionnalités Android supportées

| Fonctionnalité | Fonction DSL |
|---------------|-------------|
| ID d'application | `androidapplicationid("com.exemple.app")` |
| Version code / name | `androidversioncode(5)` / `androidversionname("1.5")` |
| SDK minimum / cible | `androidminsdk(24)` / `androidtargetsdk(34)` |
| ABIs | `androidabis(["arm64-v8a", "x86_64"])` |
| NativeActivity | `androidnativeactivity(True)` |
| Permissions | `androidpermissions(["android.permission.CAMERA"])` |
| Assets | `androidassets(["assets/**"])` |
| Icône | `androidassets(["res/mipmap-*"])` |
| Signature release | `androidkeystore("my.jks")` + `androidkeystorepass("pass")` |
| Fichiers Java | `androidjavafiles(["java/**.java"])` |
| ProGuard / R8 | `androidproguard(True)` |
| App Bundle (AAB) | `jenga build ... --aab` |
| OpenGL ES | `links(["GLESv3", "EGL"])` |
| Camera2 NDK | `links(["camera2ndk", "mediandk"])` |
| Orientation | `androidscreenorientation("landscape")` |

---

## 🌐 Emscripten / WebAssembly — Guide de démarrage

### Prérequis

| Outil | Version testée | Installation |
|-------|---------------|--------------|
| emsdk | 4.0.22 | [emscripten.org/docs/getting_started](https://emscripten.org/docs/getting_started/downloads.html) |
| Python | 3.8+ | inclus dans emsdk |
| Node.js | 18+ | inclus dans emsdk |

```bash
# Installation emsdk
git clone https://github.com/emscripten-core/emsdk.git
cd emsdk
./emsdk install latest
./emsdk activate latest
source ./emsdk_env.sh   # Linux/macOS
emsdk_env.bat           # Windows
```

Définir la variable d'environnement :

```bash
# Windows
set EMSDK=C:\emsdk

# Linux / macOS
export EMSDK=$HOME/emsdk
```

### Exemple minimal

```python
# wasm_app.jenga
from Jenga import *
from Jenga.GlobalToolchains import RegisterJengaGlobalToolchains

with workspace("WasmDemo"):
    RegisterJengaGlobalToolchains()
    configurations(["Release"])
    targetoses([TargetOS.WEB])
    targetarchs([TargetArch.WASM32])

    with project("WasmApp"):
        consoleapp()
        language("C++")
        cppdialect("C++17")
        files(["src/**.cpp"])
        usetoolchain("emscripten")
        emscripteninitialmemory(32)      # 32 MB heap initial
        emscriptenstacksize(5)            # 5 MB stack
```

```bash
jenga build wasm_app.jenga --platform Web-wasm32 --config Release
```

### Lancer l'application

Après le build, les scripts runners sont générés automatiquement :

```
# Windows — double-cliquez ou :
Build\Bin\Release-Web\WasmApp\run_WasmApp.bat

# Linux / macOS
./Build/Bin/Release-Web/WasmApp/run_WasmApp.sh

# Ouvrir dans le navigateur :
http://localhost:8080/WasmApp.html
```

Le script démarre un serveur HTTP Python local (port 8080 par défaut,
personnalisable : `run_WasmApp.bat 9000`).

### Fonctionnalités Emscripten supportées

| Fonctionnalité | Fonction DSL |
|---------------|-------------|
| Mémoire initiale (MB) | `emscripteninitialmemory(32)` |
| Taille du stack (MB) | `emscriptenstacksize(5)` |
| Nom du module JS | `emscriptenexportname("MyModule")` |
| Shell HTML personnalisé | `emscriptenshellfile("shell.html")` |
| Canvas ID | `emscriptencanvasid("mycanvas")` |
| Shell fullscreen | `emscriptenfullscreenshell(True)` |
| Flags supplémentaires | `emscriptenextraflags(["-s", "ASYNCIFY"])` |
| Embed fichiers | `embedresources(["assets/**"])` → `--preload-file` |
| Debug WASM | config Debug → `-g -gsource-map` auto |

### Exemple avec OpenGL ES / WebGL

```python
with project("OpenGLApp"):
    windowedapp()
    language("C++")
    files(["src/**.cpp"])
    usetoolchain("emscripten")
    emscripteninitialmemory(64)
    emscriptenfullscreenshell(True)
    emscriptenextraflags([
        "-s", "USE_WEBGL2=1",
        "-s", "FULL_ES3=1",
        "-s", "USE_GLFW=3",
    ])
    links(["GL"])
```

### Interopérabilité JavaScript

```cpp
// C++ → JS via EM_ASM
#include <emscripten.h>

int main() {
    EM_ASM({ console.log("Hello from WASM!"); });
    return 0;
}
```

```js
// JS → C++ : appeler une fonction exportée
Module.ccall('myFunction', 'number', ['number'], [42]);
```

---

## 🐛 Bugs corrigés

| # | Fichier | Description | Impact |
|---|---------|-------------|--------|
| 1 | `GlobalToolchains.py` | `NameError: c_compiler` dans `ToolchainClangCl` — variables `cpp_compiler`/`linker_path` indéfinies | 🔴 Crash au démarrage |
| 2 | `GlobalToolchains.py` | `NameError: linker_path` dans `ToolchainClangNative` et `ToolchainClangCrossLinux` | 🔴 Crash au démarrage |
| 3 | `Ios.py` | Alias `IOSBuilder` manquant — la factory retournait `None` pour toutes les plateformes Apple | 🔴 Build iOS/tvOS/watchOS/visionOS impossible |
| 4 | `MacosXcodeBuilder.py` | Alias `IOSBuilder`/`MacOSBuilder` manquants + `return plist_path` hors de la méthode (IndentationError) | 🔴 Mode Xcode inutilisable |
| 5 | `AppleMobileBuilder.py` | Fichier déplacé dans `unused/` cassant l'import de `MacosXcodeBuilder` | 🔴 Mode Xcode inutilisable |
| 6 | `HarmonyOs.py` | `flags += [...]` utilisé avant définition de `flags` sur cible ARM | 🔴 `NameError` sur ARM/armeabi-v7a |
| 7 | `Builder.py` | visionOS absent de `_ValidateHostTarget` et `_ResolveToolchain` | 🟡 Toolchain non résolue |
| 8 | `07_web_wasm.jenga` | Chemins Windows hardcodés dans l'exemple | 🟡 Exemple non portable |
| 9 | `05_android_ndk.jenga` | `usetoolchain()` appelé avant enregistrement du toolchain | 🟡 NameError au chargement |
| 10 | `09_multi_projects.jenga` | `windowedapp()` manquant dans les filtres Android (NativeActivity) | 🟡 APK non fonctionnel |

---

## 📦 Ce qui est inclus dans cette release

```
jenga-2.0.1-py3-none-any.whl    ← Installation Python (pip)
jenga-2.0.1.tar.gz              ← Sources (sdist)
```

### Structure du package

```
Jenga/
├── Core/
│   ├── Api.py               ← DSL complet (200+ fonctions)
│   ├── Builder.py           ← Builder de base + cache incrémental
│   ├── DependencyResolver.py← Tri topologique (algorithme de Kahn)
│   ├── Variables.py         ← Expansion %{wks.location}, %{prj.name}...
│   └── Builders/
│       ├── Windows.py       ← MSVC / clang-cl / MinGW
│       ├── Linux.py         ← GCC / Clang natif et cross
│       ├── Android.py       ← NDK + packaging APK / AAB
│       ├── Emscripten.py    ← WebAssembly + scripts runners
│       ├── Macos.py         ← Apple Clang / Mach-O
│       ├── Ios.py           ← iOS / tvOS / watchOS / visionOS direct
│       ├── MacosXcodeBuilder.py ← iOS via xcodebuild
│       ├── Xbox.py          ← GDK (GameCore) + UWP Dev Mode
│       ├── HarmonyOs.py     ← OpenHarmony NDK (LLVM)
│       ├── Zig.py           ← Cross-compilation via Zig
│       └── Switch.py        ← Nintendo Switch (NintendoSDK)
├── GlobalToolchains.py      ← Détection auto des toolchains
├── Unitest/                 ← Framework de test C++ intégré
└── Exemples/                ← 27 exemples prêts à l'emploi
```

---

## 📖 Exemples inclus

| Exemple | Description |
|---------|-------------|
| `01_hello_console` | Application console C++ basique |
| `02_static_library` | Bibliothèque statique |
| `03_shared_library` | Bibliothèque partagée (.dll/.so/.dylib) |
| `04_unit_tests` | Tests unitaires avec le framework Jenga Unitest |
| `05_android_ndk` | Application Android NDK (NativeActivity) |
| `06_ios_app` | Application iOS (Objective-C++) |
| `07_web_wasm` | Application WebAssembly (Emscripten) |
| `08_custom_toolchain` | Intégration d'un compilateur personnalisé |
| `09_multi_projects` | Workspace multi-projets avec dépendances |
| `10_modules_cpp20` | C++20 Modules (Clang / MSVC / GCC) |
| `14_cross_compile` | Cross-compilation Linux via Zig |
| `17_window_macos_cocoa` | Fenêtre macOS avec Cocoa (Objective-C++) |
| `24_all_platforms` | Build unique pour toutes les plateformes |
| `25_opengl_triangle` | OpenGL triangle (Windows + Linux + Android + Web) |
| `26_xbox_project_kinds` | Projets Xbox (GDK GameCore) |
| `27_nk_window` | Interface Nuklear multi-plateforme |

---

## ⚡ Performance du cache incrémental

| Plateforme | Build initial | Build incrémental | Gain |
|-----------|---------------|-------------------|------|
| Windows (clang-mingw) | ~0.9s | ~0.1s | **7.5x** |
| Linux (clang 14) | ~1.0s | ~0.5s | **2x** |
| Web (emscripten) | ~2.4s | ~0.3s | **8.7x** |
| Android NDK (arm64) | ~0.4s | ~0.1s | **5x** |

Le cache utilise 3 niveaux : timestamp (mtime) → fichiers de dépendances (`.d`) → signature SHA256 (`.jenga_sig`).

---

## 🔧 Démarrage rapide

### 1. Installer

```bash
pip install jenga-2.0.1-py3-none-any.whl
```

### 2. Créer un projet

```python
# monprojet.jenga
from Jenga import *
from Jenga.GlobalToolchains import RegisterJengaGlobalToolchains

with workspace("MonProjet"):
    RegisterJengaGlobalToolchains()
    configurations(["Debug", "Release"])
    targetoses([TargetOS.WINDOWS, TargetOS.LINUX])
    targetarchs([TargetArch.X86_64])

    with project("App"):
        consoleapp()
        language("C++")
        cppdialect("C++17")
        files(["src/**.cpp"])
```

### 3. Compiler

```bash
jenga build monprojet.jenga
jenga build monprojet.jenga --config Release
jenga build monprojet.jenga --platform Linux-x86_64   # cross-compile
jenga build monprojet.jenga -j8                        # 8 jobs parallèles
```

### 4. Toolchains auto-détectés

`RegisterJengaGlobalToolchains()` détecte automatiquement via variables d'environnement :

| Variable | Toolchain |
|----------|-----------|
| `ANDROID_NDK_ROOT` | `android-ndk` |
| `EMSDK` | `emscripten` |
| `CLANG_BASE` | `clang-native`, `clang-cross-linux` |
| `MINGW_ROOT` | `clang-mingw`, `mingw` |
| `ZIG_ROOT` | `zig-linux-x64` |
| `OHOS_SDK` / `HARMONY_OS_SDK` | Détection auto HarmonyOS |

---

## ⚠️ Limitations connues

| Limitation | Détail |
|-----------|--------|
| **Xbox** | Nécessite Microsoft GDK (`winget install Microsoft.Gaming.GDK`). Le packaging `.xvc` nécessite GDKX (licence EA). |
| **iOS/macOS/tvOS/watchOS/visionOS** | Nécessite macOS avec Xcode installé. Non compilable depuis Windows/Linux. |
| **HarmonyOS** | Nécessite le SDK OpenHarmony. Testable sur Windows, Linux et macOS. |
| **Nintendo Switch** | Nécessite NintendoSDK (licence développeur Nintendo). |
| **PS4 / PS5** | Nécessite SDK Sony (licence développeur PlayStation). |
| **Cache SQLite** | Volontairement désactivé en v2 — le système mtime+.d+.jenga_sig est le mécanisme actif. |

---

## 🧪 Suite de tests

```bash
python -m pytest tests/ -v
```

**95 tests automatisés** couvrant :
- Résolution de dépendances (algorithme de Kahn)
- Système de filtres (system:, config:, arch:, &&, \|\|, !)
- Expansion de variables (%{wks.location}, %{prj.name}...)
- Détection et enregistrement de toolchains
- Génération de scripts runners Emscripten
- Intégration Apple (macOS/iOS/tvOS/watchOS/visionOS)
- Intégration HarmonyOS
- Intégration Xbox (GDK/UWP)
- Parsing syntaxique des 27 exemples

---

## 📚 Documentation

- [Guide complet utilisateur](Jenga/Docs/GUIDE_COMPLET_JENGA.md) — 2500+ lignes, 20 chapitres
- [Rapport d'analyse technique](Jenga/Docs/RAPPORT_ACTIVITE_ANALYSE_COMPLETE.md)
- [Exemples](Jenga/Exemples/) — 27 projets prêts à compiler

---

## 📋 Changelog depuis v1.x

- **+** Génération automatique de scripts runners WASM (`.bat` / `.sh`)
- **+** `harmonyminsdk()` et `harmonysdk()` dans le DSL
- **+** Support complet visionOS (validation, toolchain, factory)
- **+** `AppleMobileBuilder.py` restauré pour le mode Xcode
- **fix** 3 `NameError` critiques dans `GlobalToolchains.py`
- **fix** Alias `IOSBuilder` dans `Ios.py` et `MacosXcodeBuilder.py`
- **fix** `NameError: flags` dans `HarmonyOs.py` sur cible ARM
- **fix** `IndentationError` dans `MacosXcodeBuilder.py`
- **fix** Exemples 05, 07, 09 corrigés et portables
- **+** 28 nouveaux tests (total : 95)
- **+** `pytest.ini` pour éviter la collecte des fonctions DSL
- **+** Compilation parallèle (`-j` flag, `ThreadPoolExecutor`)

---

*Jenga Build System — Construit avec Python, pour les développeurs C/C++.*
