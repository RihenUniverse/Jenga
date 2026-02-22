# 01_hello_console

## Description

Premier exemple Jenga démontrant la création d'une application console simple multi-plateformes. Ce projet illustre les concepts de base du système de build Jenga :

- Création d'un workspace minimal
- Configuration de plusieurs configurations de build (Debug/Release)
- Support multi-plateformes (Windows, Linux, macOS)
- Déclaration d'un projet de type console
- Compilation de fichiers C++

C'est l'exemple parfait pour démarrer avec Jenga et vérifier que votre environnement de développement est correctement configuré.

## Plateformes supportées

- **Windows** (x86_64) - MSVC / MinGW / Clang
- **Linux** (x86_64) - GCC / Clang
- **macOS** (x86_64) - Clang

## Architecture

```
01_hello_console/
├── 01_hello_console.jenga    # Fichier de configuration Jenga
└── main.cpp                   # Code source principal
```

## Fichiers

### main.cpp
Programme C++ minimal qui affiche "Hello from Jenga!" sur la sortie standard.

### 01_hello_console.jenga
Configuration Jenga définissant :
- Workspace "HelloConsole"
- Configurations Debug et Release
- Plateformes cibles : Windows, Linux, macOS
- Architecture : x86_64
- Projet "Hello" de type console app

## Compilation

### Build pour la plateforme native
```bash
jenga build
```

### Build avec configuration spécifique
```bash
jenga build --config Debug
jenga build --config Release
```

### Build pour une plateforme spécifique
```bash
# Windows
jenga build --platform windows-x64-msvc

# Linux
jenga build --platform linux-x64-gcc

# macOS
jenga build --platform macos-x64-clang
```

## Exécution

```bash
jenga run
```

Ou directement :
```bash
# Windows
./Build/Bin/Debug-Windows/Hello/Hello.exe

# Linux/macOS
./Build/Bin/Debug-Linux/Hello/Hello
./Build/Bin/Debug-macOS/Hello/Hello
```

## Sortie attendue

```
Hello from Jenga!
```

## Points clés

- **Simplicité** : Exemple minimal pour comprendre la structure de base d'un projet Jenga
- **Multi-plateformes** : Le même code source compile sur 3 systèmes d'exploitation majeurs
- **Type de projet** : `consoleapp()` génère un exécutable console sans interface graphique
- **Détection de fichiers** : `files(["**.cpp"])` détecte automatiquement tous les fichiers .cpp
- **Architecture unique** : Cible uniquement x86_64 pour simplifier
- **Pas de dépendances** : Utilise uniquement la bibliothèque standard C++ (iostream)

## Concepts Jenga démontrés

1. **Workspace** : Conteneur de configuration global
2. **Configurations** : Debug et Release avec optimisations différentes
3. **Target OS/Arch** : Spécification des plateformes et architectures cibles
4. **Project** : Unité de compilation (ici un seul projet)
5. **Project Kind** : `consoleapp()` pour une application console
6. **Language** : Spécification du langage C++
7. **Files** : Pattern globbing pour inclure les fichiers sources

## Étapes suivantes

Après avoir maîtrisé cet exemple, vous pouvez explorer :
- **02_static_library** : Compilation et liaison de bibliothèques statiques
- **03_shared_library** : Bibliothèques dynamiques (DLL/SO)
- **04_unit_tests** : Intégration de tests unitaires
- **15_window_win32** : Application graphique avec fenêtre native

## Dépannage

**Erreur "toolchain not found"** :
- Vérifiez que vous avez un compilateur C++ installé (MSVC, GCC, ou Clang)
- Sur Windows : Installez Visual Studio ou MinGW
- Sur Linux : `sudo apt install build-essential`
- Sur macOS : `xcode-select --install`

**Erreur de compilation** :
- Vérifiez la version de votre compilateur (C++11 minimum recommandé)
- Essayez avec `--verbose` pour voir les commandes de compilation détaillées

**Binary not found** :
- Vérifiez que la compilation s'est terminée sans erreur
- Le binaire est dans `Build/Bin/<Config>-<OS>/Hello/`
