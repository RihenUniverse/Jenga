# Guide - Icônes et Ressources Mobile (Android/iOS)

**Jenga v2.0.1** - Documentation complète pour intégrer icônes, logos et ressources dans vos applications Android et iOS.

---

## 📱 Android

### 1. Icônes d'Application (Launcher Icons)

Android utilise un système de ressources multi-densités pour les icônes. Les icônes doivent être placées dans des dossiers `mipmap` ou `drawable` selon leur densité.

#### Structure Standard

```
MonProjet/
├── android-res/
│   ├── mipmap-mdpi/          # ~48x48px (1x)
│   │   └── ic_launcher.png
│   ├── mipmap-hdpi/          # ~72x72px (1.5x)
│   │   └── ic_launcher.png
│   ├── mipmap-xhdpi/         # ~96x96px (2x)
│   │   └── ic_launcher.png
│   ├── mipmap-xxhdpi/        # ~144x144px (3x)
│   │   └── ic_launcher.png
│   └── mipmap-xxxhdpi/       # ~192x192px (4x)
│       └── ic_launcher.png
```

#### Configuration dans .jenga

```python
with project("MyApp"):
    windowedapp()
    language("C++")
    files(["src/**.cpp"])

    with filter("system:Android"):
        usetoolchain("android-ndk")
        androidapplicationid("com.example.myapp")
        androidminsdk(24)
        androidtargetsdk(34)
        androidabis(["arm64-v8a", "x86_64"])
        androidnativeactivity(True)

        # Ressources Android (icônes, assets, etc.)
        # Option 1: Si vous avez une structure res/ complète
        # (Actuellement nécessite modification du builder)

        # Option 2: Assets simples (images, sons, etc.)
        androidassets(["assets/**/*.png", "assets/**/*.jpg"])
```

#### Utilisation avec AndroidManifest.xml personnalisé

Pour définir l'icône de l'application, le builder Android génère automatiquement `AndroidManifest.xml`. Pour personnaliser :

**1. Créer un AndroidManifest.xml personnalisé** :

```xml
<!-- android-custom/AndroidManifest.xml -->
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.example.myapp">

    <application
        android:label="My App"
        android:icon="@mipmap/ic_launcher"
        android:theme="@android:style/Theme.NoTitleBar.Fullscreen">

        <meta-data android:name="android.app.lib_name" android:value="MyApp" />

        <activity android:name="android.app.NativeActivity"
            android:exported="true"
            android:configChanges="orientation|keyboardHidden|screenSize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

**2. Référencer dans .jenga** :

```python
# TODO: Feature à implémenter dans le builder Android
# androidmanifest("android-custom/AndroidManifest.xml")
# androidresources(["android-res/**"])
```

**Note** : Actuellement, les icônes personnalisées nécessitent une extension du builder Android pour copier les ressources `mipmap-*` dans l'APK.

---

### 2. Assets (Fichiers de données)

Les assets sont des fichiers (images, sons, JSON, etc.) accessibles depuis le code C++.

#### Structure

```
MonProjet/
├── assets/
│   ├── textures/
│   │   ├── background.png
│   │   └── sprite.png
│   ├── sounds/
│   │   └── click.wav
│   └── data/
│       └── config.json
```

#### Configuration dans .jenga

```python
with filter("system:Android"):
    # Copier tous les assets dans l'APK
    androidassets([
        "assets/**/*.png",
        "assets/**/*.jpg",
        "assets/**/*.wav",
        "assets/**/*.json"
    ])
```

#### Accès depuis le code C++

```cpp
#include <android/asset_manager.h>
#include <android_native_app_glue.h>

void LoadAsset(AAssetManager* assetManager, const char* filename) {
    AAsset* asset = AAssetManager_open(assetManager, filename, AASSET_MODE_BUFFER);
    if (asset) {
        size_t size = AAsset_getLength(asset);
        const void* data = AAsset_getBuffer(asset);

        // Utiliser les données...

        AAsset_close(asset);
    }
}

extern "C" void android_main(android_app* app) {
    AAssetManager* assetMgr = app->activity->assetManager;
    LoadAsset(assetMgr, "textures/background.png");
}
```

---

### 3. Permissions Android

Pour accéder à certaines ressources (stockage, caméra, etc.), déclarez les permissions :

```python
with filter("system:Android"):
    androidpermissions([
        "android.permission.CAMERA",
        "android.permission.WRITE_EXTERNAL_STORAGE",
        "android.permission.READ_EXTERNAL_STORAGE",
        "android.permission.INTERNET"
    ])
```

---

## 🍎 iOS

### 1. Icône d'Application (App Icon)

iOS utilise un catalogue d'icônes (`Assets.xcassets/AppIcon.appiconset`) avec plusieurs tailles.

#### Option 1: Fichier ICNS (recommandé pour simplicité)

```python
with filter("system:iOS"):
    usetoolchain("ios-direct")
    iosbundleid("com.example.myapp")
    iosversion("1.0")
    iosminsdk(13.0)

    # Icône au format .icns (contient toutes les tailles)
    iosappicon("assets/AppIcon.icns")
```

**Générer un .icns depuis PNG** (macOS) :

```bash
# Créer un iconset
mkdir AppIcon.iconset

# Copier vos PNG (tailles requises)
cp icon_16x16.png     AppIcon.iconset/icon_16x16.png
cp icon_32x32.png     AppIcon.iconset/icon_16x16@2x.png
cp icon_32x32.png     AppIcon.iconset/icon_32x32.png
cp icon_64x64.png     AppIcon.iconset/icon_32x32@2x.png
cp icon_128x128.png   AppIcon.iconset/icon_128x128.png
cp icon_256x256.png   AppIcon.iconset/icon_128x128@2x.png
cp icon_256x256.png   AppIcon.iconset/icon_256x256.png
cp icon_512x512.png   AppIcon.iconset/icon_256x256@2x.png
cp icon_512x512.png   AppIcon.iconset/icon_512x512.png
cp icon_1024x1024.png AppIcon.iconset/icon_512x512@2x.png

# Générer le .icns
iconutil -c icns AppIcon.iconset
```

#### Option 2: Catalogue Xcode (Assets.xcassets)

**Structure** :

```
MonProjet/
├── ios-assets/
│   └── Assets.xcassets/
│       └── AppIcon.appiconset/
│           ├── Contents.json
│           ├── icon-20@2x.png      # 40x40
│           ├── icon-20@3x.png      # 60x60
│           ├── icon-29@2x.png      # 58x58
│           ├── icon-29@3x.png      # 87x87
│           ├── icon-40@2x.png      # 80x80
│           ├── icon-40@3x.png      # 120x120
│           ├── icon-60@2x.png      # 120x120
│           ├── icon-60@3x.png      # 180x180
│           └── icon-1024.png       # 1024x1024 (App Store)
```

**Contents.json** :

```json
{
  "images": [
    { "size": "20x20", "idiom": "iphone", "filename": "icon-20@2x.png", "scale": "2x" },
    { "size": "20x20", "idiom": "iphone", "filename": "icon-20@3x.png", "scale": "3x" },
    { "size": "29x29", "idiom": "iphone", "filename": "icon-29@2x.png", "scale": "2x" },
    { "size": "29x29", "idiom": "iphone", "filename": "icon-29@3x.png", "scale": "3x" },
    { "size": "40x40", "idiom": "iphone", "filename": "icon-40@2x.png", "scale": "2x" },
    { "size": "40x40", "idiom": "iphone", "filename": "icon-40@3x.png", "scale": "3x" },
    { "size": "60x60", "idiom": "iphone", "filename": "icon-60@2x.png", "scale": "2x" },
    { "size": "60x60", "idiom": "iphone", "filename": "icon-60@3x.png", "scale": "3x" },
    { "size": "1024x1024", "idiom": "ios-marketing", "filename": "icon-1024.png", "scale": "1x" }
  ],
  "info": { "version": 1, "author": "xcode" }
}
```

**Configuration** :

```python
# TODO: Feature à implémenter
# iosresources(["ios-assets/Assets.xcassets/**"])
```

---

### 2. Ressources iOS (Fichiers Bundle)

Les ressources sont copiées dans le bundle `.app`.

```python
with filter("system:iOS"):
    # Ressources à copier dans le bundle
    iosresources([
        "assets/textures/**/*.png",
        "assets/sounds/**/*.wav",
        "assets/data/**/*.json"
    ])
```

**Accès depuis le code C++** :

```cpp
#include <CoreFoundation/CoreFoundation.h>

std::string GetBundleResourcePath(const char* filename, const char* ext) {
    CFBundleRef mainBundle = CFBundleGetMainBundle();
    CFStringRef fileStr = CFStringCreateWithCString(NULL, filename, kCFStringEncodingUTF8);
    CFStringRef extStr = CFStringCreateWithCString(NULL, ext, kCFStringEncodingUTF8);

    CFURLRef resourceURL = CFBundleCopyResourceURL(mainBundle, fileStr, extStr, NULL);

    char path[PATH_MAX];
    if (resourceURL && CFURLGetFileSystemRepresentation(resourceURL, true, (UInt8*)path, PATH_MAX)) {
        CFRelease(resourceURL);
        CFRelease(fileStr);
        CFRelease(extStr);
        return std::string(path);
    }

    return "";
}

// Usage
std::string texturePath = GetBundleResourcePath("background", "png");
```

---

## 🎨 Génération d'Icônes Multi-Tailles

### Outil: ImageMagick

**Installation** :

```bash
# macOS
brew install imagemagick

# Ubuntu/Debian
sudo apt install imagemagick

# Windows (Scoop)
scoop install imagemagick
```

**Script de génération** :

```bash
#!/bin/bash
# generate_icons.sh - Génère toutes les tailles d'icônes depuis une source 1024x1024

SOURCE="icon-source.png"  # Votre icône haute résolution (1024x1024 recommandé)

# Android mipmap
mkdir -p android-res/mipmap-mdpi android-res/mipmap-hdpi android-res/mipmap-xhdpi \
         android-res/mipmap-xxhdpi android-res/mipmap-xxxhdpi

convert "$SOURCE" -resize 48x48   android-res/mipmap-mdpi/ic_launcher.png
convert "$SOURCE" -resize 72x72   android-res/mipmap-hdpi/ic_launcher.png
convert "$SOURCE" -resize 96x96   android-res/mipmap-xhdpi/ic_launcher.png
convert "$SOURCE" -resize 144x144 android-res/mipmap-xxhdpi/ic_launcher.png
convert "$SOURCE" -resize 192x192 android-res/mipmap-xxxhdpi/ic_launcher.png

# iOS (iconset pour .icns)
mkdir -p ios-assets/AppIcon.iconset

convert "$SOURCE" -resize 16x16     ios-assets/AppIcon.iconset/icon_16x16.png
convert "$SOURCE" -resize 32x32     ios-assets/AppIcon.iconset/icon_16x16@2x.png
convert "$SOURCE" -resize 32x32     ios-assets/AppIcon.iconset/icon_32x32.png
convert "$SOURCE" -resize 64x64     ios-assets/AppIcon.iconset/icon_32x32@2x.png
convert "$SOURCE" -resize 128x128   ios-assets/AppIcon.iconset/icon_128x128.png
convert "$SOURCE" -resize 256x256   ios-assets/AppIcon.iconset/icon_128x128@2x.png
convert "$SOURCE" -resize 256x256   ios-assets/AppIcon.iconset/icon_256x256.png
convert "$SOURCE" -resize 512x512   ios-assets/AppIcon.iconset/icon_256x256@2x.png
convert "$SOURCE" -resize 512x512   ios-assets/AppIcon.iconset/icon_512x512.png
convert "$SOURCE" -resize 1024x1024 ios-assets/AppIcon.iconset/icon_512x512@2x.png

# Générer .icns (macOS uniquement)
if [[ "$OSTYPE" == "darwin"* ]]; then
    iconutil -c icns ios-assets/AppIcon.iconset -o ios-assets/AppIcon.icns
fi

echo "✓ Icônes générées!"
```

**Usage** :

```bash
chmod +x generate_icons.sh
./generate_icons.sh
```

---

## 📋 Exemple Complet

### Structure du Projet

```
MyMobileApp/
├── src/
│   └── main.cpp
├── assets/
│   ├── textures/
│   │   └── logo.png
│   └── sounds/
│       └── beep.wav
├── android-res/
│   ├── mipmap-mdpi/
│   │   └── ic_launcher.png
│   ├── mipmap-hdpi/
│   │   └── ic_launcher.png
│   └── ... (autres densités)
├── ios-assets/
│   └── AppIcon.icns
└── MyMobileApp.jenga
```

### MyMobileApp.jenga

```python
import os
from Jenga import *
from Jenga.GlobalToolchains import RegisterJengaGlobalToolchains

with workspace("MyMobileApp"):
    RegisterJengaGlobalToolchains()
    configurations(["Debug", "Release"])
    targetoses([TargetOS.ANDROID, TargetOS.IOS])
    targetarchs([TargetArch.ARM64, TargetArch.X86_64])

    androidsdkpath(os.getenv("ANDROID_SDK_ROOT", ""))
    androidndkpath(os.getenv("ANDROID_NDK_ROOT", ""))

    with project("MyMobileApp"):
        windowedapp()
        language("C++")
        cppdialect("C++17")
        files(["src/**.cpp"])

        # ── Android ──────────────────────────────────────────
        with filter("system:Android"):
            usetoolchain("android-ndk")
            androidapplicationid("com.example.mymobileapp")
            androidminsdk(24)
            androidtargetsdk(34)
            androidabis(["arm64-v8a", "x86_64"])
            androidnativeactivity(True)

            # Assets
            androidassets([
                "assets/textures/**/*.png",
                "assets/sounds/**/*.wav"
            ])

            # Permissions
            androidpermissions([
                "android.permission.VIBRATE"
            ])

            # TODO: Icônes (feature à implémenter)
            # androidresources(["android-res/**"])

        # ── iOS ──────────────────────────────────────────────
        with filter("system:iOS"):
            usetoolchain("ios-direct")
            iosbundleid("com.example.mymobileapp")
            iosversion("1.0")
            iosminsdk(13.0)

            # Icône
            iosappicon("ios-assets/AppIcon.icns")

            # Ressources
            iosresources([
                "assets/textures/**/*.png",
                "assets/sounds/**/*.wav"
            ])

        # ── Configuration Build ──────────────────────────────
        with filter("config:Debug"):
            defines(["_DEBUG"])
            optimize("Off")
            symbols(True)

        with filter("config:Release"):
            defines(["NDEBUG"])
            optimize("Speed")
            symbols(False)
```

---

## 🚀 Compilation

```bash
# Android
jenga build --platform android-arm64-ndk --config Release

# iOS (sur macOS)
jenga build --platform ios-arm64-xcode --config Release
```

---

## ⚠️ Fonctionnalités à Implémenter

### Android

- [ ] `androidicon(path)` - Définir l'icône principale
- [ ] `androidresources(patterns)` - Copier res/ dans l'APK
- [ ] `androidmanifest(path)` - Utiliser un AndroidManifest.xml personnalisé
- [ ] Support automatique mipmap-* dans le builder

### iOS

- [ ] Support automatique Assets.xcassets dans le builder
- [ ] `ioslaunchscreen(path)` - Écran de lancement personnalisé

---

## 📚 Références

### Android
- [Android App Resources](https://developer.android.com/guide/topics/resources/providing-resources)
- [Icon Design Guidelines](https://developer.android.com/guide/practices/ui_guidelines/icon_design_launcher)
- [Asset Manager API](https://developer.android.com/ndk/reference/group/asset)

### iOS
- [App Icons (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/app-icons)
- [Bundle Resources](https://developer.apple.com/documentation/foundation/bundle)
- [Asset Catalogs](https://developer.apple.com/library/archive/documentation/Xcode/Reference/xcode_ref-Asset_Catalog_Format/)

---

**Auteur** : Claude Sonnet 4.5
**Date** : 22 février 2026
**Version Jenga** : 2.0.1
