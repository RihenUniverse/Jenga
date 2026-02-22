# Guide Installation APK sur MEmu

## Problème
Les APKs générés par Jenga ne s'installent pas sur l'émulateur MEmu

## Diagnostic

### 1. Vérifier Version Android de MEmu

```bash
# Connecter à MEmu via adb
adb connect 127.0.0.1:21503

# Vérifier version Android
adb shell getprop ro.build.version.sdk
```

**Requis**: API level ≥ 24 (Android 7.0+)

Les APKs Jenga sont compilés avec `minSDK=24` par défaut.

### 2. Vérifier ABIs Supportés

```bash
# Lister ABIs supportés par MEmu
adb shell getprop ro.product.cpu.abilist
```

**Expected**: `x86,x86_64` ou `x86_64`

Les Fat APKs Jenga incluent:
- arm64-v8a
- x86_64
- x86 (Example 18)
- armeabi-v7a (Example 18)

**✓** MEmu devrait être compatible (x86/x86_64 inclus)

### 3. Installation Manuelle

#### Méthode 1: ADB Install

```bash
# Installer APK
adb install -r "E:\Projets\MacShared\Projets\Jenga\Jenga\Exemples\05_android_ndk\Build\Bin\Debug-Android\NativeApp\android-build-universal\NativeApp-Debug.apk"

# Si erreur INSTALL_FAILED_UPDATE_INCOMPATIBLE
adb uninstall com.jenga.nativeapp
adb install "path/to/NativeApp-Debug.apk"
```

#### Méthode 2: Drag & Drop

1. Démarrer MEmu
2. Glisser-déposer l'APK directement dans la fenêtre MEmu
3. Accepter l'installation

#### Méthode 3: Shared Folder

1. MEmu Settings → Paramètres → Partage de fichiers
2. Activer le partage et choisir un dossier Windows
3. Copier l'APK dans ce dossier
4. Ouvrir File Manager dans MEmu
5. Naviguer vers le dossier partagé
6. Cliquer sur l'APK pour installer

### 4. Vérifier Logs d'Installation

```bash
# Voir les erreurs d'installation en temps réel
adb logcat | grep -i "packageinstaller"

# Ou plus spécifique
adb logcat *:E | grep -i "install"
```

## Solutions aux Problèmes Courants

### Erreur: INSTALL_FAILED_NO_MATCHING_ABIS

**Cause**: MEmu n'a pas d'ABI compatible avec l'APK

**Solution**:
1. Vérifier que l'APK inclut x86 ou x86_64:
   ```bash
   unzip -l NativeApp-Debug.apk | grep "lib/"
   ```
2. Si manquant, reconfigurer `.jenga`:
   ```python
   androidabis(["x86", "x86_64", "arm64-v8a"])
   ```

### Erreur: INSTALL_FAILED_UPDATE_INCOMPATIBLE

**Cause**: Version précédente installée avec signature différente

**Solution**:
```bash
adb uninstall com.jenga.nativeapp
adb install NativeApp-Debug.apk
```

### Erreur: INSTALL_FAILED_INVALID_APK

**Cause**: APK corrompu ou API level incompatible

**Solution**:
1. Vérifier intégrité APK:
   ```bash
   unzip -t NativeApp-Debug.apk
   ```
2. Rebuilder APK:
   ```bash
   jenga clean
   jenga build --platform android --config Debug
   ```

### Erreur: INSTALL_FAILED_OLDER_SDK

**Cause**: MEmu version Android < minSDK (24)

**Solution**:
1. **Option A**: Mettre à jour MEmu vers Android 7.0+
2. **Option B**: Réduire minSDK dans `.jenga`:
   ```python
   androidminsdk(21)  # Android 5.0 (avec limitations)
   ```

## Procédure Recommandée

### 1. Vérification Initiale

```bash
# Connecter MEmu
adb connect 127.0.0.1:21503

# Vérifier configuration
adb shell getprop | grep -E "(version.sdk|cpu.abi)"
```

**Attendu**:
```
[ro.build.version.sdk]: [24]  # ou plus
[ro.product.cpu.abi]: [x86_64]
```

### 2. Installation Simple

```bash
# Désinstaller version précédente si existe
adb uninstall com.jenga.nativeapp

# Installer nouvelle version
adb install -r NativeApp-Debug.apk

# Vérifier installation
adb shell pm list packages | grep jenga
```

### 3. Lancement

```bash
# Lancer l'app
adb shell am start -n com.jenga.nativeapp/.android.app.NativeActivity

# Ou depuis MEmu: cliquer sur l'icône app
```

## Configuration MEmu Recommandée

### Paramètres MEmu

1. **Version Android**: 7.1 (API 25) minimum
2. **RAM**: 2GB minimum (4GB recommandé)
3. **CPU**: 2 cores minimum
4. **Rendu**: OpenGL (pas DirectX pour NDK apps)

### Activer ADB Debugging

1. MEmu → Paramètres → À propos
2. Cliquer 7 fois sur "Build number"
3. Retour → Options développeur
4. Activer "Débogage USB"

## Test Rapide

```bash
# Script complet de test
echo "=== Test Installation APK sur MEmu ==="

# 1. Connexion
adb connect 127.0.0.1:21503

# 2. Vérification
SDK=$(adb shell getprop ro.build.version.sdk)
ABI=$(adb shell getprop ro.product.cpu.abi)
echo "MEmu: Android API $SDK, ABI $ABI"

# 3. Installation
APK="E:\Projets\MacShared\Projets\Jenga\Jenga\Exemples\05_android_ndk\Build\Bin\Debug-Android\NativeApp\android-build-universal\NativeApp-Debug.apk"

if [ -f "$APK" ]; then
    echo "Installing $APK..."
    adb install -r "$APK"

    if [ $? -eq 0 ]; then
        echo "✓ Installation SUCCESS"
        adb shell pm list packages | grep jenga
    else
        echo "✗ Installation FAILED"
        adb logcat -d | grep -i "install" | tail -20
    fi
else
    echo "APK not found: $APK"
fi
```

## Alternatives à MEmu

Si MEmu continue à avoir des problèmes:

1. **Android Studio Emulator** (AVD)
   - Plus stable
   - Support complet NDK
   - Configuration API levels flexibles

2. **Genymotion**
   - Performances excellentes
   - x86/x86_64 natif
   - Gratuit pour usage perso

3. **Device Physique**
   - Toujours plus fiable
   - Activer USB debugging
   - `adb install` directement

## Support

Si problème persiste:
1. Sauvegarder logs: `adb logcat > memu_logs.txt`
2. Vérifier AndroidManifest.xml dans APK
3. Tester avec AVD (Android Studio)
4. Reporter issue sur GitHub Jenga avec logs
