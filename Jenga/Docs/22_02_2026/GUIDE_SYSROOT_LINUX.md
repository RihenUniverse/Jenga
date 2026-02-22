# Guide : Sysroot Linux pour Cross-Compilation depuis Windows

**Date** : 2026-02-22
**Jenga** : v2.0.0
**Objectif** : Compiler du code Linux avec dépendances système (X11, OpenGL) depuis Windows

---

## 📌 Problématique

Lors de la cross-compilation Linux depuis Windows avec Zig, certains exemples échouent car ils nécessitent des **headers et bibliothèques système Linux** :

- **Exemple 16** : Window X11 Linux → `fatal error: 'X11/Xlib.h' file not found`
- **Exemple 25** : OpenGL Triangle Linux → Nécessite `X11/Xlib.h` et `GL/gl.h`

**Cause** : Zig permet de cross-compiler le code C/C++ standard, mais ne fournit pas les bibliothèques tierces comme X11 ou OpenGL.

---

## 🎯 Solutions Disponibles

### Option 1 : Compilation Native sur Linux/WSL2 ✅ **[Recommandé pour tests rapides]**

**Avantage** : Simplicité, pas besoin de sysroot
**Inconvénient** : Nécessite WSL2 ou machine Linux

#### Sur WSL2 (Ubuntu)

```bash
# 1. Installer les dépendances nécessaires
sudo apt update
sudo apt install build-essential libx11-dev mesa-common-dev libgl1-mesa-dev

# 2. Naviguer vers l'exemple
cd /mnt/e/Projets/MacShared/Projets/Jenga/Jenga/Exemples/16_window_x11_linux

# 3. Compiler avec un toolchain Linux natif
jenga build --platform linux-x64
```

#### Modification du .jenga pour WSL2

Si vous utilisez GCC/Clang natif au lieu de Zig :

```python
with filter("system:Linux"):
    # Option A: Utiliser GCC natif (si disponible)
    ccompiler("gcc")
    cppcompiler("g++")
    linker("g++")
    links(["X11"])

    # Option B: Utiliser Clang natif
    # ccompiler("clang")
    # cppcompiler("clang++")
    # linker("clang++")
    # links(["X11"])
```

---

### Option 2 : Créer un Sysroot Linux Complet ✅ **[Recommandé pour CI/CD]**

**Avantage** : Cross-compilation depuis Windows sans WSL2
**Inconvénient** : Nécessite accès temporaire à une machine Linux

#### Étape 1 : Créer le sysroot sur une machine Linux

Sur une vraie machine Linux (ou WSL2 temporaire) :

```bash
# 1. Créer la structure du sysroot
mkdir -p ~/sysroot-linux-x64/{include,lib,usr}

# 2. Installer les packages de développement
sudo apt update
sudo apt install -y \
    libx11-dev \
    libgl1-mesa-dev \
    mesa-common-dev \
    libglu1-mesa-dev \
    libxrandr-dev \
    libxinerama-dev \
    libxcursor-dev \
    libxi-dev

# 3. Copier les headers
cp -r /usr/include/* ~/sysroot-linux-x64/include/

# 4. Copier les bibliothèques (architecture x86_64)
cp -r /usr/lib/x86_64-linux-gnu/* ~/sysroot-linux-x64/lib/

# 5. Copier les bibliothèques additionnelles
if [ -d /lib/x86_64-linux-gnu ]; then
    cp -r /lib/x86_64-linux-gnu/* ~/sysroot-linux-x64/lib/
fi

# 6. Créer une archive pour transférer vers Windows
cd ~
tar czf sysroot-linux-x64.tar.gz sysroot-linux-x64/
```

#### Étape 2 : Transférer le sysroot vers Windows

```bash
# Depuis WSL2, copier vers Windows
cp ~/sysroot-linux-x64.tar.gz /mnt/e/Projets/sysroots/

# Depuis Windows, extraire l'archive
# (utiliser 7-Zip ou WinRAR pour extraire .tar.gz)
```

Ou directement depuis WSL2 :

```bash
# Déplacer le sysroot vers un emplacement Windows
mv ~/sysroot-linux-x64 /mnt/e/Projets/sysroots/
```

#### Étape 3 : Configurer Jenga pour utiliser le sysroot

**Méthode A : Modifier GlobalToolchains.py** (global)

Éditer [Jenga/GlobalToolchains.py](e:\Projets\MacShared\Projets\Jenga\Jenga\GlobalToolchains.py) :

```python
def ToolchainZigLinuxX64():
    # ... (configuration existante)

    with toolchain("zig-linux-x64", "clang"):
        settarget("Linux", "x86_64", "gnu")
        targettriple("x86_64-linux-gnu")
        ccompiler(cc_wrapper)
        cppcompiler(cpp_wrapper)
        linker(cpp_wrapper)
        archiver(str(ar_wrapper))

        # Ajouter le sysroot
        sysroot(r"E:/Projets/sysroots/sysroot-linux-x64")
        includedirs([r"E:/Projets/sysroots/sysroot-linux-x64/include"])
        libdirs([r"E:/Projets/sysroots/sysroot-linux-x64/lib"])

        cflags(["-target", "x86_64-linux-gnu"])
        cxxflags(["-target", "x86_64-linux-gnu", "-std=c++17"])
        ldflags(["-target", "x86_64-linux-gnu"])
        arflags([])
```

**Méthode B : Modifier localement chaque exemple** (pour exemples spécifiques)

Éditer [16_window_x11_linux.jenga](e:\Projets\MacShared\Projets\Jenga\Jenga\Exemples\16_window_x11_linux\16_window_x11_linux.jenga) :

```python
with filter("system:Linux"):
    usetoolchain("zig-linux-x64")
    sysroot(r"E:/Projets/sysroots/sysroot-linux-x64")
    includedirs([r"E:/Projets/sysroots/sysroot-linux-x64/include"])
    libdirs([r"E:/Projets/sysroots/sysroot-linux-x64/lib"])
    links(["X11"])
```

#### Étape 4 : Réinstaller Jenga et compiler

```bash
# Si vous avez modifié GlobalToolchains.py, réinstaller Jenga
cd e:\Projets\MacShared\Projets\Jenga
python -m pip install -e .

# Compiler l'exemple
cd Jenga\Exemples\16_window_x11_linux
jenga build --platform linux-x64
```

---

### Option 3 : Utiliser Docker Linux ✅ **[Recommandé pour CI/CD cloud]**

**Avantage** : Environnement Linux reproductible
**Inconvénient** : Nécessite Docker Desktop

#### Dockerfile pour compilation Jenga

Créer `Dockerfile-linux-build` :

```dockerfile
FROM ubuntu:22.04

# Installer les dépendances
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    build-essential \
    libx11-dev \
    libgl1-mesa-dev \
    mesa-common-dev \
    git

# Installer Jenga
WORKDIR /jenga
COPY . .
RUN pip3 install -e .

# Volume pour les builds
VOLUME /builds
WORKDIR /builds

CMD ["bash"]
```

#### Utilisation

```bash
# Build l'image Docker
docker build -t jenga-linux-builder -f Dockerfile-linux-build .

# Compiler un exemple
docker run --rm \
    -v e:/Projets/MacShared/Projets/Jenga/Jenga/Exemples:/builds \
    jenga-linux-builder \
    bash -c "cd /builds/16_window_x11_linux && jenga build --platform linux-x64"
```

---

## 📦 Packages Linux Recommandés pour Sysroot

### Minimum (Console Apps)

```bash
build-essential
```

### Pour Windowing (X11)

```bash
libx11-dev
libxrandr-dev
libxinerama-dev
libxcursor-dev
libxi-dev
```

### Pour OpenGL

```bash
libgl1-mesa-dev
mesa-common-dev
libglu1-mesa-dev
```

### Pour Audio (ALSA/PulseAudio)

```bash
libasound2-dev
libpulse-dev
```

---

## 🔧 Dépannage

### Erreur : `cannot find -lX11`

**Cause** : Bibliothèque X11 manquante dans le sysroot

**Solution** :

```bash
# Sur Linux, copier les .so manquants
find /usr/lib -name "libX11.so*" -exec cp {} ~/sysroot-linux-x64/lib/ \;
```

### Erreur : `X11/Xlib.h: No such file or directory`

**Cause** : Headers X11 manquants

**Solution** :

```bash
# Sur Linux, réinstaller libx11-dev et recopier
sudo apt install --reinstall libx11-dev
cp -r /usr/include/X11 ~/sysroot-linux-x64/include/
```

### Erreur : `cannot find crt*.o`

**Cause** : Fichiers de runtime C manquants

**Solution** :

```bash
# Copier les fichiers CRT (C Runtime)
cp /usr/lib/x86_64-linux-gnu/crt*.o ~/sysroot-linux-x64/lib/
```

---

## 📊 Comparaison des Options

| Critère | Option 1 (WSL2) | Option 2 (Sysroot) | Option 3 (Docker) |
|---------|-----------------|---------------------|-------------------|
| **Simplicité** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Performance** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Portabilité** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **CI/CD** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Setup Initial** | Facile | Moyen | Moyen |

---

## ✅ Recommandations

1. **Pour développement local rapide** : Utilisez **Option 1 (WSL2)**
2. **Pour pipeline CI/CD** : Utilisez **Option 2 (Sysroot)** ou **Option 3 (Docker)**
3. **Pour tests multi-plateforme** : Utilisez **Option 2** avec sysroots pour Linux, Android, etc.

---

## 📝 Notes Importantes

- **Zig seul ne suffit pas** : Zig cross-compile le code standard, mais pas les bibliothèques système
- **Sysroot ≠ Émulation** : Un sysroot contient uniquement les headers et bibliothèques, pas un OS complet
- **Architecture** : Assurez-vous que le sysroot correspond à l'architecture cible (x86_64, arm64, etc.)
- **Licences** : Vérifiez les licences des bibliothèques incluses dans le sysroot

---

## 🔗 Exemples Concernés

- **16_window_x11_linux** : Nécessite X11
- **25_opengl_triangle** (Linux) : Nécessite X11 + OpenGL
- Tout exemple Linux utilisant des bibliothèques système tierces

---

**Généré par** : Claude Code
**Build System** : Jenga v2.0.0
