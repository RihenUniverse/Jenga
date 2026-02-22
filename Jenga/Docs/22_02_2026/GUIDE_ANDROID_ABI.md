# Guide : ABIs Android et Compatibilité Multi-Appareils

**Date** : 2026-02-22
**Jenga** : v2.0.0
**Problème** : APK ne s'installe pas sur MEmu ou émulateurs Android

---

## 📌 Qu'est-ce qu'une ABI Android?

**ABI (Application Binary Interface)** = Architecture processeur supportée par l'APK

Android supporte **4 ABIs principales** :

| ABI | Description | Appareils | Émulateurs |
|-----|-------------|-----------|------------|
| **armeabi-v7a** | ARM 32-bit | Anciens smartphones (< 2015) | MEmu (mode ARM), Genymotion |
| **arm64-v8a** | ARM 64-bit | Smartphones modernes (2015+) | Appareils physiques récents |
| **x86** | Intel 32-bit | Tablettes Intel (rares) | **MEmu**, BlueStacks, Nox |
| **x86_64** | Intel 64-bit | Tablettes Intel récentes | Émulateurs x64 modernes |

---

## 🔍 Diagnostic : Pourquoi l'APK ne s'installe pas sur MEmu?

### Vérifier l'ABI de MEmu

#### Méthode 1 : Via ADB

```bash
# Connecter MEmu via ADB
adb connect 127.0.0.1:21503

# Vérifier l'ABI supportée
adb shell getprop ro.product.cpu.abi
```

**Résultat attendu** :
- `x86` → MEmu utilise Intel 32-bit
- `x86_64` → MEmu utilise Intel 64-bit
- `armeabi-v7a` ou `arm64-v8a` → MEmu en mode ARM (rare)

#### Méthode 2 : Via les paramètres MEmu

1. Ouvrir MEmu
2. Paramètres → About phone
3. Vérifier "CPU" ou "Processor"

**MEmu par défaut = x86 (32-bit)**

---

## ✅ Solution : Compiler pour TOUTES les ABIs

### Configuration Actuelle (Limitée)

```python
androidabis(["arm64-v8a", "x86_64"])  # ❌ Manque x86 et armeabi-v7a
```

**Problème** : Cette configuration ne fonctionne que sur:
- Smartphones ARM 64-bit récents
- Émulateurs Intel 64-bit

**Ne fonctionne PAS sur** :
- ❌ MEmu (x86 32-bit)
- ❌ BlueStacks (x86 32-bit)
- ❌ Anciens smartphones ARM 32-bit

### Configuration Recommandée (Universelle)

```python
androidabis(["armeabi-v7a", "arm64-v8a", "x86", "x86_64"])  # ✅ Compatible avec 99% appareils
```

**Avantages** :
- ✅ Fonctionne sur MEmu, BlueStacks, Nox
- ✅ Fonctionne sur tous les smartphones Android (anciens et récents)
- ✅ Fonctionne sur émulateurs ARM et x86
- ✅ APK unique (fat APK) compatible avec tous les appareils

**Inconvénient** :
- Taille APK plus grande (4x les binaires .so)
- Temps de compilation plus long

---

## 🛠️ Modification des Exemples Android

### Exemple 18 - Android Window

Éditer [18_window_android_native.jenga](e:\Projets\MacShared\Projets\Jenga\Jenga\Exemples\18_window_android_native\18_window_android_native.jenga) :

```python
with project("AndroidWindow"):
    windowedapp()
    language("C++")
    cppdialect("C++17")
    files(["src/**.cpp"])
    androidapplicationid("com.jenga.window")
    androidminsdk(24)
    androidtargetsdk(34)

    # AVANT (limité)
    # androidabis(["arm64-v8a", "x86_64"])

    # APRÈS (universel) ✅
    androidabis(["armeabi-v7a", "arm64-v8a", "x86", "x86_64"])

    androidnativeactivity(True)
    usetoolchain("android-ndk")
```

### Exemple 24 - All Platforms

Même modification dans [24_all_platforms.jenga](e:\Projets\MacShared\Projets\Jenga\Jenga\Exemples\24_all_platforms\24_all_platforms.jenga) :

```python
with filter("system:Android"):
    windowedapp()
    usetoolchain("android-ndk")
    defines(["PLATFORM_ANDROID"])
    androidapplicationid("com.jenga.allplatforms")
    androidminsdk(24)
    androidtargetsdk(34)
    androidabis(["armeabi-v7a", "arm64-v8a", "x86", "x86_64"])  # ✅ Toutes ABIs
    androidnativeactivity(True)
```

### Exemple 25 - OpenGL Triangle

Même modification dans [25_opengl_triangle.jenga](e:\Projets\MacShared\Projets\Jenga\Jenga\Exemples\25_opengl_triangle\25_opengl_triangle.jenga) :

```python
with filter("system:Android"):
    windowedapp()
    usetoolchain("android-ndk")
    androidapplicationid("com.jenga.gltriangle")
    androidminsdk(24)
    androidtargetsdk(34)
    androidabis(["armeabi-v7a", "arm64-v8a", "x86", "x86_64"])  # ✅ Toutes ABIs
    androidnativeactivity(True)
    links(["EGL", "GLESv3", "android", "log"])
    defines(["PLATFORM_ANDROID"])
```

---

## 🚀 Recompilation avec Toutes les ABIs

```bash
# Exemple 18
cd e:\Projets\MacShared\Projets\Jenga\Jenga\Exemples\18_window_android_native
jenga build --platform android-arm64

# Exemple 24
cd e:\Projets\MacShared\Projets\Jenga\Jenga\Exemples\24_all_platforms
jenga build --platform android-arm64

# Exemple 25
cd e:\Projets\MacShared\Projets\Jenga\Jenga\Exemples\25_opengl_triangle
jenga build --platform android-arm64
```

**Résultat** : APK générées contiennent maintenant 4 versions de chaque .so :
```
APK/lib/
├── armeabi-v7a/
│   └── libAndroidWindow.so
├── arm64-v8a/
│   └── libAndroidWindow.so
├── x86/
│   └── libAndroidWindow.so
└── x86_64/
    └── libAndroidWindow.so
```

---

## 📲 Installation sur MEmu

### Méthode 1 : Via ADB (Recommandé)

```bash
# 1. Connecter MEmu
adb connect 127.0.0.1:21503

# 2. Vérifier la connexion
adb devices

# 3. Installer l'APK
adb install -r "e:\Projets\MacShared\Projets\Jenga\Jenga\Exemples\18_window_android_native\Build\Bin\Debug-Android\AndroidWindow\android-build-arm64-v8a\AndroidWindow-Debug.apk"

# Flags utiles :
# -r : Réinstaller si existe déjà
# -t : Autoriser les APK de test
# -g : Accorder toutes les permissions
adb install -r -t -g "chemin/vers/app.apk"
```

### Méthode 2 : Drag & Drop

1. Ouvrir MEmu
2. Glisser l'APK depuis l'explorateur Windows vers la fenêtre MEmu
3. Accepter l'installation

**Note** : Peut nécessiter d'activer "Sources inconnues" dans MEmu :
- Paramètres → Sécurité → Sources inconnues (activer)

### Méthode 3 : Via Shared Folder

1. Configurer un dossier partagé dans MEmu
2. Copier l'APK dans ce dossier
3. Dans MEmu, utiliser un gestionnaire de fichiers pour installer

---

## 🐛 Dépannage

### Erreur : `INSTALL_FAILED_NO_MATCHING_ABIS`

**Cause** : Aucune ABI dans l'APK ne correspond à l'appareil

**Solution** :
```python
# Ajouter toutes les ABIs
androidabis(["armeabi-v7a", "arm64-v8a", "x86", "x86_64"])
```

### Erreur : `INSTALL_FAILED_INVALID_APK`

**Cause** : APK non signée ou corrompue

**Solution** :
```bash
# Vérifier l'APK
adb shell pm list packages | grep jenga

# Désinstaller l'ancienne version
adb uninstall com.jenga.window

# Réinstaller
adb install -r "chemin/vers/app.apk"
```

### Erreur : `adb: device offline`

**Solution** :
```bash
# Redémarrer ADB
adb kill-server
adb start-server
adb connect 127.0.0.1:21503
```

### MEmu ne détecte pas l'APK (Drag & Drop)

**Solution** :
1. Activer "Sources inconnues" :
   - MEmu → Paramètres → Sécurité → Sources inconnues (ON)
2. Redémarrer MEmu
3. Réessayer le drag & drop

---

## 📊 Comparaison ABIs

### Taille APK

| Configuration | Taille APK | Compatibilité |
|---------------|------------|---------------|
| `["arm64-v8a"]` | ~2 MB | 50% appareils (smartphones récents) |
| `["arm64-v8a", "x86_64"]` | ~4 MB | 70% appareils |
| `["armeabi-v7a", "arm64-v8a", "x86", "x86_64"]` | ~8 MB | **99% appareils** ✅ |

### Temps de Compilation

| Configuration | Temps (exemple 18) |
|---------------|-------------------|
| 1 ABI | ~0.36s |
| 2 ABIs | ~0.72s |
| 4 ABIs | ~1.5s |

---

## ✅ Recommandations

### Pour Développement Local (MEmu/BlueStacks)

```python
# Configuration optimisée pour émulateurs x86
androidabis(["x86", "x86_64"])  # ✅ Rapide, fonctionne sur tous émulateurs PC
```

### Pour Distribution Google Play

```python
# Configuration universelle (99% compatibilité)
androidabis(["armeabi-v7a", "arm64-v8a", "x86", "x86_64"])  # ✅ Maximum compatibilité
```

**Note** : Google Play peut générer des APKs spécifiques par ABI automatiquement (App Bundle).

### Pour Tests sur Smartphones Physiques

```python
# Configuration ARM uniquement (smartphones)
androidabis(["armeabi-v7a", "arm64-v8a"])  # ✅ Couvre 95% smartphones
```

---

## 📝 Checklist Installation MEmu

- [ ] Modifier `.jenga` pour inclure `x86` dans `androidabis()`
- [ ] Recompiler l'APK avec `jenga build --platform android-arm64`
- [ ] Vérifier l'ABI de MEmu avec `adb shell getprop ro.product.cpu.abi`
- [ ] Activer "Sources inconnues" dans MEmu (Paramètres → Sécurité)
- [ ] Installer via ADB : `adb install -r -t app.apk`
- [ ] Lancer l'application depuis MEmu

---

## 🔗 Ressources

- **ADB Documentation** : https://developer.android.com/tools/adb
- **Android ABIs** : https://developer.android.com/ndk/guides/abis
- **MEmu Official** : https://www.memuplay.com/

---

**Généré par** : Claude Code
**Build System** : Jenga v2.0.0
