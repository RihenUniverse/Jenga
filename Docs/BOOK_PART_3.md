# Jenga Build System - Le Guide Complet
# PARTIE III - FONCTIONNALITÉS AVANCÉES

## Chapitre 9: Groupes de Projets

### 9.1 Qu'est-ce qu'un Groupe ?

Les **groupes** organisent les projets logiquement.

#### Syntaxe

```python
with workspace("GameEngine"):
    
    with group("Core"):
        with project("Math"):
            staticlib()
        
        with project("Physics"):
            staticlib()
    
    with group("Rendering"):
        with project("OpenGL"):
            staticlib()
        
        with project("Vulkan"):
            staticlib()
    
    with group("Game"):
        with project("Engine"):
            staticlib()
        
        with project("Editor"):
            consoleapp()
```

### 9.2 Hiérarchie

```
GameEngine/
├── Core/
│   ├── Math
│   └── Physics
├── Rendering/
│   ├── OpenGL
│   └── Vulkan
└── Game/
    ├── Engine
    └── Editor
```

### 9.3 Utilisation

**IDE** : Les groupes deviennent des dossiers virtuels dans Visual Studio, Xcode, etc.

**Build** : Pas d'impact sur la compilation (organisation visuelle uniquement)

---

## Chapitre 10: Inclusion de Projets Externes

### 10.1 Pourquoi Inclure des Projets Externes ?

**Problème** : Réutiliser des bibliothèques sans dupliquer le code

**Solution** : `include()` charge des projets depuis d'autres fichiers `.jenga`

### 10.2 Deux Approches de Définition

#### Approche 1: Projets dans un Workspace Externe

```python
# external/MathLib/mathlib.jenga
with workspace("MathLib"):
    
    with project("Vector"):
        staticlib()
        files(["src/**.cpp"])
    
    with project("Matrix"):
        staticlib()
        files(["src/**.cpp"])
        dependson(["Vector"])
```

#### Approche 2: Projets Standalone (Sans Workspace)

```python
# libs/Logger/logger.jenga
# Pas de workspace - projets définis directement

with project("Logger"):
    staticlib()
    files(["src/**.cpp"])

with project("FileLogger"):
    staticlib()
    files(["src/**.cpp"])
    dependson(["Logger"])
```

**Différence** : Sans workspace, les projets sont ajoutés directement au workspace appelant.

### 10.3 Syntaxe d'Inclusion

```python
include(jenga_file: str, projects: list = None)
```

**Arguments** :
- `jenga_file` : Chemin vers .jenga
- `projects` : Liste projets à inclure (optionnel)
  - `None` : Tous les projets
  - `["ProjectA", "ProjectB"]` : Seulement ces projets

### 10.4 Inclusion Complète

Tous les projets du fichier externe :

```python
with workspace("MyApp"):
    
    # Inclure TOUS les projets
    include("external/MathLib/mathlib.jenga")
    
    with project("App"):
        consoleapp()
        # Vector et Matrix sont disponibles
        dependson(["Vector", "Matrix"])
```

### 10.5 Inclusion Sélective

Seulement certains projets :

```python
with workspace("MyApp"):
    
    # Inclure SEULEMENT Logger (pas FileLogger)
    include("libs/Logger/logger.jenga", ["Logger"])
    
    with project("App"):
        consoleapp()
        dependson(["Logger"])
```

### 10.6 Exemples Pratiques

#### Exemple 1: Bibliothèque Graphics

```python
# external/Graphics/graphics.jenga
with workspace("Graphics"):
    
    with project("GraphicsCore"):
        staticlib()
        files(["Core/**.cpp"])
    
    with project("OpenGLRenderer"):
        staticlib()
        files(["OpenGL/**.cpp"])
        dependson(["GraphicsCore"])
    
    with project("VulkanRenderer"):
        staticlib()
        files(["Vulkan/**.cpp"])
        dependson(["GraphicsCore"])
```

**Utilisation - OpenGL seulement** :
```python
with workspace("MyGame"):
    
    include("external/Graphics/graphics.jenga", 
            ["GraphicsCore", "OpenGLRenderer"])
    
    with project("Game"):
        consoleapp()
        dependson(["OpenGLRenderer"])
```

**Utilisation - Les deux renderers** :
```python
with workspace("GraphicsDemo"):
    
    # Inclure tout
    include("external/Graphics/graphics.jenga")
    
    with project("Demo"):
        consoleapp()
        
        with filter("configurations:Debug"):
            dependson(["OpenGLRenderer"])
        
        with filter("configurations:Release"):
            dependson(["VulkanRenderer"])
```

#### Exemple 2: Utilitaires Modulaires

```python
# libs/Utils/utils.jenga
with project("StringUtils"):
    staticlib()
    files(["String/**.cpp"])

with project("FileUtils"):
    staticlib()
    files(["File/**.cpp"])

with project("TimeUtils"):
    staticlib()
    files(["Time/**.cpp"])
```

**Utilisation sélective** :
```python
with workspace("MyApp"):
    
    # Seulement String et File
    include("libs/Utils/utils.jenga", ["StringUtils", "FileUtils"])
    
    with project("App"):
        consoleapp()
        dependson(["StringUtils", "FileUtils"])
```

### 10.7 Dépendances entre Projets Externes

**Important** : Les dépendances sont résolues automatiquement !

```python
# external/Math/math.jenga
with workspace("Math"):
    
    with project("Vector"):
        staticlib()
    
    with project("Matrix"):
        staticlib()
        dependson(["Vector"])  # Matrix → Vector
    
    with project("Advanced"):
        staticlib()
        dependson(["Matrix"])  # Advanced → Matrix → Vector
```

**Inclusion** :

```python
# ❌ ERREUR : Dépendances manquantes
include("external/Math/math.jenga", ["Advanced"])
# Advanced a besoin de Matrix et Vector !

# ✅ CORRECT : Inclure les dépendances
include("external/Math/math.jenga", ["Advanced", "Matrix", "Vector"])

# ✅ MIEUX : Inclure tout
include("external/Math/math.jenga")
```

### 10.8 Multiples Inclusions

Inclure plusieurs bibliothèques :

```python
with workspace("GameEngine"):
    
    # Math library
    include("external/Math/math.jenga")
    
    # Graphics library
    include("external/Graphics/graphics.jenga", 
            ["GraphicsCore", "OpenGLRenderer"])
    
    # Physics library
    include("external/Physics/physics.jenga")
    
    # Logger
    include("libs/Logger/logger.jenga", ["Logger"])
    
    # Votre engine
    with project("Engine"):
        staticlib()
        files(["src/**.cpp"])
        
        dependson([
            "Vector",         # De Math
            "Matrix",         # De Math
            "GraphicsCore",   # De Graphics
            "PhysicsCore",    # De Physics
            "Logger"          # De Logger
        ])
```

### 10.9 Organisation Recommandée

```
MyProject/
├── myproject.jenga          # Workspace principal
├── external/                # Libs externes (avec workspace)
│   ├── MathLib/
│   │   ├── mathlib.jenga
│   │   └── (sources)
│   └── Graphics/
│       ├── graphics.jenga
│       └── (sources)
├── libs/                    # Libs standalone (sans workspace)
│   ├── Logger/
│   │   ├── logger.jenga
│   │   └── (sources)
│   └── Utils/
│       ├── utils.jenga
│       └── (sources)
└── src/
    └── main.cpp
```

### 10.10 Best Practices

#### Documentation des Dépendances

```python
# external/Graphics/graphics.jenga
"""
Graphics Library v2.0

Projets:
- GraphicsCore : Système de base (requis)
- OpenGLRenderer : Renderer OpenGL (dépend de Core)
- VulkanRenderer : Renderer Vulkan (dépend de Core)

Recommandations:
- OpenGL : include(..., ["GraphicsCore", "OpenGLRenderer"])
- Vulkan : include(..., ["GraphicsCore", "VulkanRenderer"])
"""
```

#### Chemins Relatifs

```python
# ✅ Bon
include("external/Math/math.jenga")

# ❌ Éviter
include("C:/Users/John/Projects/Math/math.jenga")
```

#### Versionning

```python
# mylib.jenga
LIB_VERSION = "2.1.0"

with project("MyLib"):
    defines([f"MYLIB_VERSION={LIB_VERSION}"])
```

---

## Chapitre 11: Compilation Cross-Platform

### 11.1 Architecture Multi-Plateforme

#### Stratégie

1. **Code commun** dans `src/core/`
2. **Code spécifique** dans `src/platform/{windows,linux,android}/`
3. **Filters** pour sélectionner les fichiers

### 11.2 Exemple Complet

#### Structure

```
Game/
├── game.jenga
├── src/
│   ├── core/
│   │   ├── game.h
│   │   └── game.cpp
│   └── platform/
│       ├── windows/
│       │   └── window_win32.cpp
│       ├── linux/
│       │   └── window_x11.cpp
│       └── android/
│           └── window_android.cpp
```

#### game.jenga

```python
with workspace("Game"):
    platforms(["Windows", "Linux", "Android"])
    configurations(["Debug", "Release"])
    
    with project("Game"):
        consoleapp()
        language("C++")
        
        location(".")
        
        # Code commun (toutes plateformes)
        files([
            "src/core/**.cpp",
            "src/core/**.h"
        ])
        
        includedirs(["src"])
        
        # Windows
        with filter("system:Windows"):
            files(["src/platform/windows/**.cpp"])
            defines(["PLATFORM_WINDOWS", "_WIN32"])
            links(["kernel32", "user32", "gdi32"])
        
        # Linux
        with filter("system:Linux"):
            files(["src/platform/linux/**.cpp"])
            defines(["PLATFORM_LINUX", "__linux__"])
            links(["X11", "pthread", "dl"])
        
        # Android
        with filter("system:Android"):
            files(["src/platform/android/**.cpp"])
            defines(["PLATFORM_ANDROID"])
            sharedlib()  # .so pour Android
            links(["log", "android"])
            
            androidapplicationid("com.example.game")
            androidminsdk(21)
            androidtargetsdk(33)
```

### 11.3 Headers Conditionnels

#### platform.h

```cpp
#pragma once

#if defined(_WIN32)
    #define PLATFORM_WINDOWS
    #include <windows.h>
#elif defined(__linux__) && !defined(__ANDROID__)
    #define PLATFORM_LINUX
    #include <X11/Xlib.h>
#elif defined(__ANDROID__)
    #define PLATFORM_ANDROID
    #include <android/log.h>
#elif defined(__APPLE__)
    #define PLATFORM_MACOS
    #include <Cocoa/Cocoa.h>
#endif

// API unifiée
class Window {
public:
    Window(int width, int height);
    void show();
    void update();
    
private:
#ifdef PLATFORM_WINDOWS
    HWND hwnd;
#elif defined(PLATFORM_LINUX)
    Display* display;
    ::Window window;
#elif defined(PLATFORM_ANDROID)
    ANativeWindow* native_window;
#endif
};
```

### 11.4 Build Multi-Plateforme

```bash
# Windows
jenga build --platform Windows --config Release
# → Game-Release-Windows.exe

# Linux
jenga build --platform Linux --config Release
# → Game-Release-Linux

# Android
jenga build --platform Android --config Release
jenga package --platform Android
# → Game-Release.apk
```

---

## Chapitre 12: Android (APK/AAB)

### 12.1 Configuration Android

```python
with workspace("AndroidGame"):
    platforms(["Android"])
    
    # SDK/NDK paths
    androidsdkpath("/home/user/Android/Sdk")
    androidndkpath("/home/user/Android/Sdk/ndk/25.1.8937393")
    
    with project("Game"):
        sharedlib()  # Bibliothèque native
        language("C++")
        cppdialect("C++17")
        
        files(["src/**.cpp"])
        
        # Configuration Android
        androidapplicationid("com.mygame.awesome")
        androidversioncode(1)
        androidversionname("1.0.0")
        androidminsdk(21)   # Android 5.0
        androidtargetsdk(33) # Android 13
        
        # Bibliothèques Android
        links([
            "android",
            "log",
            "EGL",
            "GLESv3"
        ])
        
        # Assets
        dependfiles([
            "assets/**",
            "textures/**"
        ])
```

### 12.2 Signature

#### Génération Keystore

```bash
jenga keygen --platform Android

# Interactive:
# Keystore name: release.jks
# Key alias: key0
# Password: ******
```

#### Configuration

```python
with project("Game"):
    # ...
    
    with filter("configurations:Release"):
        androidsign(True)
        androidkeystore("release.jks")
        androidkeystorepass("mypassword")
        androidkeyalias("key0")
```

### 12.3 Build APK

```bash
# Build
jenga build --platform Android --config Release

# Package
jenga package --platform Android

# Output:
# ✓ APK created: Build/Packages/Game-Release-signed.apk
#   Size: 5.23 MB
```

### 12.4 AAB (Play Store)

```bash
jenga package --platform Android --type aab

# Output: Game-Release.aab
```

---

## Chapitre 13: iOS (IPA)

### 13.1 Configuration iOS

```python
with workspace("iOSApp"):
    platforms(["iOS"])
    
    with project("App"):
        consoleapp()
        language("C++")
        cppdialect("C++17")
        
        files(["src/**.cpp", "src/**.mm"])  # Objective-C++
        
        # iOS configuration
        # TODO: iOS-specific settings
```

### 13.2 Build IPA

```bash
# Build
jenga build --platform iOS --config Release

# Package
jenga package --platform iOS

# Output: App-Release.ipa
```

**Note** : Nécessite Xcode et certificats Apple

---

## Chapitre 14: Desktop (Windows/Linux/macOS)

### 14.1 Windows

```python
with workspace("WindowsApp"):
    platforms(["Windows"])
    
    with toolchain("msvc", "cl"):
        cppcompiler("cl")
    
    with project("App"):
        windowedapp()
        language("C++")
        
        files(["src/**.cpp"])
        
        with filter("system:Windows"):
            defines(["_WIN32", "WIN32_LEAN_AND_MEAN"])
            links(["kernel32", "user32", "gdi32", "opengl32"])
```

**Build** :
```bash
jenga build --platform Windows --config Release
jenga package --platform Windows
# → App-Release-Windows.zip
```

### 14.2 Linux

```python
with workspace("LinuxApp"):
    platforms(["Linux"])
    
    with toolchain("gcc", "g++"):
        cppcompiler("g++")
    
    with project("App"):
        consoleapp()
        language("C++")
        
        files(["src/**.cpp"])
        
        with filter("system:Linux"):
            defines(["_LINUX", "__linux__"])
            links(["X11", "GL", "pthread", "dl"])
```

**Build** :
```bash
jenga build --platform Linux --config Release
jenga package --platform Linux
# → App-Release-Linux.zip
```

### 14.3 macOS

```python
with workspace("macOSApp"):
    platforms(["MacOS"])
    
    with toolchain("clang", "clang++"):
        cppcompiler("clang++")
        framework("Cocoa")
        framework("OpenGL")
    
    with project("App"):
        windowedapp()
        language("C++")
        
        files(["src/**.cpp", "src/**.mm"])
        
        with filter("system:MacOS"):
            defines(["__APPLE__"])
```

**Build** :
```bash
jenga build --platform MacOS --config Release
jenga package --platform MacOS
# → App-Release.dmg
```

---

## Chapitre 15: Package Command

### 15.1 Syntaxe

```bash
jenga package [options]
```

**Options** :
- `--platform <n>` : Plateforme cible
- `--config <n>` : Configuration
- `--project <n>` : Projet à packager
- `--type <n>` : Type (apk, aab, zip, dmg, ipa)

### 15.2 Types de Packages

| Plateforme | Format | Description |
|------------|--------|-------------|
| Android | APK | Application package |
| Android | AAB | App Bundle (Play Store) |
| iOS | IPA | iOS App Store package |
| Windows | ZIP | Archive with .exe + DLLs |
| macOS | DMG | Disk image |
| Linux | ZIP | Archive with binary + .so |

### 15.3 Workflow

```bash
# 1. Build
jenga build --platform Android --config Release

# 2. Package
jenga package --platform Android

# 3. Distribuer
# Build/Packages/MyApp-Release-signed.apk
```

---

Fin de la Partie III - Fonctionnalités Avancées

[Suite dans BOOK_PART_4.md]
