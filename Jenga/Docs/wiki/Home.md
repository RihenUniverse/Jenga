# Jenga Wiki

**Langues / Languages :** [Français](#français) · [English](#english)

---

## Français

**Jenga** est un système de build **cross-plateforme** écrit en Python pour les
projets natifs **C, C++, Objective-C, Assembly, Rust et Zig**. Il remplace
CMake / Makefile par un **DSL Python** lisible décrit dans des fichiers `.jenga`,
et **compile directement** via les toolchains natives — sans génération de
fichiers projet intermédiaires.

### Pourquoi Jenga ?

- **Un seul fichier décrit tout** : la même description `.jenga` cible toutes
  les plateformes.
- **Zéro génération intermédiaire** : compilation directe (contrairement à CMake).
- **DSL Python** : toute la puissance de Python dans vos fichiers de build.
- **Rapide** : cache incrémental 3 niveaux (mtime → `.d` → SHA256) + daemon
  pour des commandes quasi-instantanées.
- **Packaging & déploiement intégrés** : MSI, EXE, ZIP, DEB, PKG, DMG, APK, AAB,
  IPA, HAP — sans gradle / electron-builder / pkgbuild externes.
- **Réseau auto-configuré** : pare-feu et permissions réseau gérés à
  l'installation, sur toutes les plateformes.

### Plateformes supportées

| Plateforme | Statut | Compilateurs |
|-----------|--------|--------------|
| Windows x64 | ✅ Production | MSVC, clang-cl, clang-mingw, MinGW (gcc) |
| Linux x64 | ✅ Production | GCC, Clang (natif + cross) |
| Android | ✅ Production | NDK r27c (arm64-v8a, armeabi-v7a, x86, x86_64) |
| Web / WASM | ✅ Production | Emscripten (emsdk 4.x) |
| macOS | ✅ Prêt (macOS requis) | Apple Clang |
| iOS / tvOS / watchOS / visionOS | ✅ Prêt (macOS + Xcode) | Apple Clang (direct ou xcodebuild) |
| HarmonyOS | ✅ Prêt | LLVM du NDK OpenHarmony |
| Xbox One / Series X\|S | 🟡 Partiel | MSVC + Microsoft GDK |
| Nintendo Switch / PS4 / PS5 | 🔒 Licence requise | SDK propriétaires |

### Navigation

| Page | Contenu |
|------|---------|
| [Installation](Installation.md) | Installer Jenga via pip ou depuis les sources |
| [Premier Workspace](Premier-Workspace.md) | Créer son premier projet pas à pas |
| [Commandes CLI](Commandes-CLI.md) | Référence des 24 commandes `jenga` |
| [DSL Reference](DSL-Reference.md) | Toutes les fonctions DSL `.jenga` |
| [Toolchains et Sysroots](Toolchains-et-Sysroots.md) | Détection, cross-compilation, toolchains custom |
| [Tests Unitest](Tests-Unitest.md) | Framework de tests C++ intégré |
| [Documentation Automatique](Documentation-Automatique.md) | `jenga docs` (Doxygen → MD/HTML/PDF) |
| [Packaging, Déploiement, Publication](Packaging-Deploiement-Publication.md) | Créer et distribuer des packages |
| [Réseau et Pare-feu](Reseau-et-Pare-feu.md) | Permissions réseau multi-plateforme |
| [HarmonyOS / OpenHarmony](HarmonyOS.md) | Build et packaging HAP |
| [Exemples](Exemples.md) | 27 exemples prêts à compiler |
| [FAQ / Dépannage](FAQ-Depannage.md) | Problèmes courants et solutions |

### Démarrage en 30 secondes

```bash
pip install jenga
jenga workspace MonProjet --interactive
cd MonProjet
jenga build
jenga run
```

---

## English

**Jenga** is a **cross-platform** build system written in Python for native
**C, C++, Objective-C, Assembly, Rust and Zig** projects. It replaces
CMake / Makefile with a readable **Python DSL** described in `.jenga` files and
**compiles directly** through native toolchains — with no intermediate project
files.

### Why Jenga?

- **One file describes everything**: the same `.jenga` targets every platform.
- **No intermediate generation**: direct compilation (unlike CMake).
- **Python DSL**: the full power of Python inside your build files.
- **Fast**: 3-level incremental cache (mtime → `.d` → SHA256) plus a daemon for
  near-instant commands.
- **Built-in packaging & deployment**: MSI, EXE, ZIP, DEB, PKG, DMG, APK, AAB,
  IPA, HAP — no external gradle / electron-builder / pkgbuild.
- **Auto-configured networking**: firewall rules and network permissions are
  handled at install time, on every platform.

### Supported platforms

| Platform | Status | Compilers |
|----------|--------|-----------|
| Windows x64 | ✅ Production | MSVC, clang-cl, clang-mingw, MinGW (gcc) |
| Linux x64 | ✅ Production | GCC, Clang (native + cross) |
| Android | ✅ Production | NDK r27c (arm64-v8a, armeabi-v7a, x86, x86_64) |
| Web / WASM | ✅ Production | Emscripten (emsdk 4.x) |
| macOS | ✅ Ready (macOS host) | Apple Clang |
| iOS / tvOS / watchOS / visionOS | ✅ Ready (macOS + Xcode) | Apple Clang (direct or xcodebuild) |
| HarmonyOS | ✅ Ready | OpenHarmony NDK LLVM |
| Xbox One / Series X\|S | 🟡 Partial | MSVC + Microsoft GDK |
| Nintendo Switch / PS4 / PS5 | 🔒 License required | Proprietary SDKs |

### Navigation

| Page | Content |
|------|---------|
| [Installation](Installation.md) | Install Jenga via pip or from source |
| [First Workspace](Premier-Workspace.md) | Create your first project step by step |
| [CLI Commands](Commandes-CLI.md) | Reference for the 24 `jenga` commands |
| [DSL Reference](DSL-Reference.md) | All `.jenga` DSL functions |
| [Toolchains & Sysroots](Toolchains-et-Sysroots.md) | Detection, cross-compilation, custom toolchains |
| [Unitest Tests](Tests-Unitest.md) | Built-in C++ testing framework |
| [Automatic Documentation](Documentation-Automatique.md) | `jenga docs` (Doxygen → MD/HTML/PDF) |
| [Packaging, Deployment, Publishing](Packaging-Deploiement-Publication.md) | Build and distribute packages |
| [Networking & Firewall](Reseau-et-Pare-feu.md) | Cross-platform network permissions |
| [HarmonyOS / OpenHarmony](HarmonyOS.md) | HAP build and packaging |
| [Examples](Exemples.md) | 27 ready-to-build examples |
| [FAQ / Troubleshooting](FAQ-Depannage.md) | Common issues and fixes |

### 30-second quick start

```bash
pip install jenga
jenga workspace MyProject --interactive
cd MyProject
jenga build
jenga run
```
