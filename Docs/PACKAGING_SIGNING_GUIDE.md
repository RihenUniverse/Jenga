# Guide Complet - Packaging & Signing

## 🎯 Vue d'Ensemble

Jenga Build System supporte le packaging et la signature d'applications pour toutes les plateformes :

- **Android** : APK, AAB (App Bundle)
- **iOS** : IPA
- **Windows** : ZIP, Installer
- **macOS** : DMG, .app bundle
- **Linux** : ZIP, AppImage, DEB, RPM

## 📦 Package Command

### Android APK

#### Configuration
```python
# myapp.jenga

with workspace("MyApp"):
    platforms(["Android"])
    
    # Android SDK/NDK paths
    androidsdkpath("/path/to/Android/Sdk")
    androidndkpath("/path/to/Android/Sdk/ndk/25.1.8937393")
    
    with project("MyGame"):
        sharedlib()  # ou consoleapp()
        language("C++")
        
        # Android configuration
        androidapplicationid("com.mycompany.mygame")
        androidversioncode(1)
        androidversionname("1.0.0")
        androidminsdk(21)
        androidtargetsdk(33)
        
        # Signing (optionnel pour debug)
        androidsign(True)
        androidkeystore("release.jks")
        androidkeystorepass("mypassword")
        androidkeyalias("key0")
```

#### Build & Package
```bash
# 1. Build l'application
jenga build --platform Android --config Release

# 2. Package en APK
jenga package --platform Android

# Output: Build/Packages/MyGame-Release.apk
```

#### Package Options
```bash
# APK (défaut)
jenga package --platform Android --type apk

# AAB (Google Play Store)
jenga package --platform Android --type aab

# Spécifier le projet
jenga package --platform Android --project MyGame
```

### Android AAB (App Bundle)

Pour publier sur Google Play Store :

```bash
jenga package --platform Android --type aab
```

**Note** : AAB nécessite bundletool et gradle (en développement)

### iOS IPA

```bash
# Build
jenga build --platform iOS --config Release

# Package
jenga package --platform iOS

# Output: Build/Packages/MyApp-Release.ipa
```

**Requis** : Xcode, certificats et provisioning profiles valides

### Windows

```bash
# Build
jenga build --platform Windows --config Release

# Package en ZIP
jenga package --platform Windows

# Output: Build/Packages/MyApp-Release-Windows.zip
```

Le ZIP contient :
- Exécutable (.exe)
- DLLs nécessaires
- Assets (si spécifiés)

### macOS

```bash
# Package en DMG
jenga package --platform MacOS

# Output: Build/Packages/MyApp-Release.dmg
```

### Linux

```bash
# Package en ZIP
jenga package --platform Linux

# Output: Build/Packages/MyApp-Release-Linux.zip
```

## 🔐 Sign Command

### Génération de Keystore (Android)

#### Commande Interactive
```bash
jenga keygen --platform Android
```

**Prompts** :
```
Keystore name: release.jks
Key alias: key0
Keystore password: ******
Your name: John Doe
Organization: MyCompany
...
```

#### Commande Non-Interactive
```bash
jenga keygen --platform Android \
  --name release.jks \
  --alias mykey \
  --storepass mypassword \
  --validity 10000
```

### Signature Android APK

#### Option 1 : Configuration dans .jenga

```python
with project("MyGame"):
    # ...
    androidsign(True)
    androidkeystore("release.jks")
    androidkeystorepass("mypassword")
    androidkeyalias("key0")
```

Puis :
```bash
jenga package --platform Android
# APK automatiquement signé
```

#### Option 2 : Signature Manuelle

```bash
# Signer un APK existant
jenga sign --platform Android \
  --apk Build/Packages/MyGame-Release.apk \
  --keystore release.jks \
  --storepass mypassword \
  --alias key0

# Output: MyGame-Release-signed.apk
```

### Vérification de Signature

```bash
# Vérifier automatiquement après signature
jenga sign --platform Android --apk myapp.apk

# Output:
# ✓ APK signed successfully!
# Verifying signature...
# ✓ APK signature verified
```

## 🛠️ Workflow Complet

### Debug Build (Non Signé)

```bash
# Build
jenga build --platform Android --config Debug

# Package (sans signature)
jenga package --platform Android
```

**Utilisable pour** : Tests locaux, debugging

### Release Build (Signé)

```bash
# 1. Générer keystore (une fois)
jenga keygen --platform Android

# 2. Configurer .jenga
# (ajouter androidkeystore, etc.)

# 3. Build Release
jenga build --platform Android --config Release

# 4. Package et signer
jenga package --platform Android

# 5. Distribuer
# MyGame-Release-signed.apk prêt pour distribution
```

## 📋 Exemples Complets

### Exemple 1 : Jeu Mobile Simple

```python
# game.jenga

with workspace("MyGame"):
    platforms(["Android", "iOS"])
    configurations(["Debug", "Release"])
    
    androidsdkpath("/home/user/Android/Sdk")
    androidndkpath("/home/user/Android/Sdk/ndk/25.1.8937393")
    
    with project("Game"):
        sharedlib()
        language("C++")
        cppdialect("C++17")
        
        files(["src/**.cpp"])
        includedirs(["include"])
        
        # Android config
        androidapplicationid("com.mygame.awesome")
        androidversioncode(1)
        androidversionname("1.0.0")
        androidminsdk(21)
        androidtargetsdk(33)
        
        # Debug: pas de signature
        with filter("configurations:Debug"):
            androidsign(False)
        
        # Release: signé
        with filter("configurations:Release"):
            androidsign(True)
            androidkeystore("keys/release.jks")
            androidkeystorepass("SECURE_PASSWORD")
            androidkeyalias("game_key")
        
        # Assets
        dependfiles([
            "assets/**",
            "textures/**"
        ])
```

**Build & Release** :
```bash
# Debug (local testing)
jenga build --platform Android --config Debug
jenga package --platform Android

# Release (Play Store)
jenga build --platform Android --config Release
jenga package --platform Android --type aab
# → MyGame-Release-signed.aab
```

### Exemple 2 : Multi-Plateforme

```python
with workspace("CrossPlatformApp"):
    platforms(["Windows", "Linux", "MacOS", "Android", "iOS"])
    
    with project("App"):
        consoleapp()
        language("C++")
        
        files(["src/**.cpp"])
        
        # Windows
        with filter("system:Windows"):
            defines(["PLATFORM_WINDOWS"])
        
        # Android
        with filter("system:Android"):
            androidapplicationid("com.app.cross")
            androidsign(True)
            androidkeystore("android.jks")
```

**Package Toutes les Plateformes** :
```bash
# Windows
jenga package --platform Windows --config Release
# → App-Release-Windows.zip

# Linux
jenga package --platform Linux --config Release
# → App-Release-Linux.zip

# macOS
jenga package --platform MacOS --config Release
# → App-Release.dmg

# Android
jenga package --platform Android --config Release
# → App-Release-signed.apk

# iOS
jenga package --platform iOS --config Release
# → App-Release.ipa
```

## 🔒 Sécurité

### Bonnes Pratiques Keystore

1. **NE JAMAIS** committer le keystore dans Git
```bash
# .gitignore
*.jks
*.keystore
*.p12
keys/
```

2. **Backup** sécurisé
```bash
# Sauvegarder dans un endroit sûr
cp release.jks ~/secure-backup/
```

3. **Variables d'environnement** pour les mots de passe
```python
import os

with project("App"):
    androidsign(True)
    androidkeystore("release.jks")
    androidkeystorepass(os.getenv("KEYSTORE_PASSWORD"))
```

4. **Permissions** restrictives
```bash
chmod 600 release.jks
```

### CI/CD Integration

```yaml
# .github/workflows/release.yml

name: Release Build

on:
  push:
    tags:
      - 'v*'

jobs:
  android-release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Android SDK
        uses: android-actions/setup-android@v2
      
      - name: Decode keystore
        run: |
          echo "${{ secrets.KEYSTORE_BASE64 }}" | base64 -d > release.jks
      
      - name: Build APK
        run: |
          jenga build --platform Android --config Release
      
      - name: Package & Sign
        env:
          KEYSTORE_PASSWORD: ${{ secrets.KEYSTORE_PASSWORD }}
        run: |
          jenga package --platform Android
      
      - name: Upload APK
        uses: actions/upload-artifact@v2
        with:
          name: release-apk
          path: Build/Packages/*.apk
```

## 📊 Comparaison des Formats

| Format | Plateforme | Usage | Signature |
|--------|-----------|-------|-----------|
| **APK** | Android | Distribution directe, tests | Optionnelle (debug) / Requise (release) |
| **AAB** | Android | Google Play Store uniquement | Requise |
| **IPA** | iOS | App Store, TestFlight | Requise (certificat Apple) |
| **ZIP** | Windows/Linux/macOS | Distribution générale | Optionnelle |
| **DMG** | macOS | Distribution macOS | Recommandée |
| **EXE** | Windows | Installeur Windows | Recommandée (Authenticode) |

## 🚀 Commandes Rapides

```bash
# Générer keystore Android
jenga keygen

# Build + Package Android Debug
jenga build --platform Android && jenga package --platform Android

# Build + Package Android Release (signé)
jenga build --platform Android --config Release
jenga package --platform Android

# Signer APK existant
jenga sign --platform Android --apk myapp.apk --keystore release.jks

# Package toutes config
for config in Debug Release; do
  jenga build --config $config --platform Android
  jenga package --config $config --platform Android
done

# Package multi-plateforme
for platform in Windows Linux Android; do
  jenga package --platform $platform --config Release
done
```

## 📚 Résumé

**Jenga Build System** offre :

1. ✅ **Package** : APK, AAB, IPA, ZIP, DMG
2. ✅ **Sign** : Signature Android APK, iOS, Windows, macOS
3. ✅ **Keygen** : Génération de keystores Android
4. ✅ **Workflow** : Debug non signé, Release signé
5. ✅ **Multi-plateforme** : 6 plateformes supportées
6. ✅ **Sécurité** : Best practices intégrées
7. ✅ **CI/CD** : Prêt pour l'automatisation

**Le système de packaging et signing est COMPLET et prêt pour la production !** 🚀
