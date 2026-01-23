# Jenga Build System - Le Guide Complet

## 📘 Table des Matières

### Partie I - Introduction
1. [Présentation](#chapitre-1-présentation)
2. [Installation](#chapitre-2-installation)
3. [Premiers Pas](#chapitre-3-premiers-pas)

### Partie II - Concepts Fondamentaux
4. [Architecture du Système](#chapitre-4-architecture)
5. [Workspaces et Projets](#chapitre-5-workspaces-et-projets)
6. [Configurations et Plateformes](#chapitre-6-configurations-et-plateformes)

### Partie III - Fonctionnalités Avancées
7. [Toolchains](#chapitre-7-toolchains)
8. [Tests Unitaires](#chapitre-8-tests-unitaires)
9. [Groupes de Projets](#chapitre-9-groupes-de-projets)
10. [Inclusion de Projets Externes](#chapitre-10-inclusion-externe)

### Partie IV - Multi-Plateforme
11. [Compilation Cross-Platform](#chapitre-11-cross-platform)
12. [Android (APK/AAB)](#chapitre-12-android)
13. [iOS (IPA)](#chapitre-13-ios)
14. [Desktop (Windows/Linux/macOS)](#chapitre-14-desktop)

### Partie V - Packaging et Distribution
15. [Package Command](#chapitre-15-package)
16. [Sign Command](#chapitre-16-sign)
17. [Keygen Command](#chapitre-17-keygen)
18. [CI/CD Integration](#chapitre-18-cicd)

### Partie VI - Optimisation et Performance
19. [Cache de Compilation](#chapitre-19-cache)
20. [Compilation Parallèle](#chapitre-20-parallel)
21. [Precompiled Headers](#chapitre-21-pch)

### Partie VII - Références
22. [API Complète](#chapitre-22-api)
23. [Dépannage](#chapitre-23-troubleshooting)
24. [Exemples Pratiques](#chapitre-24-examples)

---

# PARTIE I - INTRODUCTION

## Chapitre 1: Présentation

### 1.1 Qu'est-ce que Jenga ?

**Jenga Build System** est un système de build moderne et puissant pour C/C++ qui unifie la compilation multi-plateforme dans un DSL (Domain-Specific Language) simple et élégant.

#### Pourquoi Jenga ?

**Problèmes traditionnels** :
- CMake : Syntaxe complexe, verbeux
- Make : Non portable, archaïque
- Premake : Limité, peu maintenu
- Meson : Python requis partout
- Bazel : Overhead massif

**Solution Jenga** :
```python
# Configuration simple et lisible
with workspace("MyApp"):
    configurations(["Debug", "Release"])
    
    with project("App"):
        consoleapp()
        files(["src/**.cpp"])
        
        with test("Unit"):
            testfiles(["tests/**.cpp"])
```

#### Caractéristiques Principales

✅ **DSL Pythonique** - Syntaxe claire et intuitive
✅ **Multi-plateforme** - 6 plateformes supportées
✅ **Cache Intelligent** - Build 20x plus rapide
✅ **Tests Intégrés** - Framework Unitest inclus
✅ **Packaging** - APK, AAB, IPA, ZIP, DMG
✅ **Signature** - Android, iOS, Windows, macOS
✅ **Toolchains** - Support complet GCC, Clang, MSVC
✅ **Zero Dépendances** - Python 3 uniquement

### 1.2 Philosophie

Jenga repose sur trois principes :

#### 1. Simplicité
```python
# Un projet en 5 lignes
with project("Hello"):
    consoleapp()
    files(["main.cpp"])
```

#### 2. Puissance
```python
# Multi-plateforme complet
with workspace("Game"):
    platforms(["Windows", "Linux", "Android", "iOS"])
    
    with project("Engine"):
        staticlib()
        
        with filter("system:Android"):
            androidminsdk(21)
            links(["log", "android"])
```

#### 3. Cohérence
- **Convention over Configuration**
- **Sane Defaults**
- **Progressive Disclosure**

### 1.3 Comparaison

| Feature | Jenga | CMake | Meson | Bazel |
|---------|-------|-------|-------|-------|
| Syntaxe Simple | ✅ | ❌ | ✅ | ❌ |
| Multi-plateforme | ✅ | ✅ | ✅ | ✅ |
| Cache Rapide | ✅ | ⚠️ | ✅ | ✅ |
| Tests Intégrés | ✅ | ❌ | ✅ | ✅ |
| Packaging Mobile | ✅ | ❌ | ❌ | ⚠️ |
| Courbe d'apprentissage | Faible | Élevée | Moyenne | Très élevée |

---

## Chapitre 2: Installation

### 2.1 Prérequis

**Système** :
- Python 3.7+
- GCC, Clang, ou MSVC

**Optionnel** :
- Android SDK/NDK (pour Android)
- Xcode (pour iOS/macOS)
- Java JDK (pour keytool)

### 2.2 Installation

#### Téléchargement
```bash
# Extraire l'archive
unzip Jenga_Build_System.zip
cd Jenga_Build_System
```

#### Configuration PATH
```bash
# Linux/macOS
export PATH="$PATH:$(pwd)"
chmod +x jenga.sh

# Windows
set PATH=%PATH%;%CD%
```

#### Vérification
```bash
jenga --help
```

**Output** :
```
╔══════════════════════════════════════════════════════════════════╗
║            ██╗███████╗███╗   ██╗ ██████╗  █████╗                    ║
║    Multi-platform C/C++ Build System v1.0.0                       ║
╚══════════════════════════════════════════════════════════════════╝
```

### 2.3 Configuration Initiale

#### Compiler
```bash
# Détecter automatiquement
jenga info
# Platform: Linux
# Compiler: g++ (detected)
```

#### Android SDK (optionnel)
```bash
export ANDROID_SDK_ROOT=/path/to/Android/Sdk
export ANDROID_NDK_ROOT=/path/to/Android/Sdk/ndk/25.1.8937393
```

---

## Chapitre 3: Premiers Pas

### 3.1 Hello World

#### Structure
```
hello/
├── hello.jenga
└── main.cpp
```

#### main.cpp
```cpp
#include <iostream>

int main() {
    std::cout << "Hello, Jenga!" << std::endl;
    return 0;
}
```

#### hello.jenga
```python
with workspace("Hello"):
    configurations(["Debug", "Release"])
    
    with project("Hello"):
        consoleapp()
        language("C++")
        
        files(["main.cpp"])
        
        targetdir("Build/Bin/%{cfg.buildcfg}")
```

#### Build
```bash
jenga build
```

**Output** :
```
✓ Build completed in 1.23s
✓ Build completed successfully
```

#### Run
```bash
jenga run

# Output:
# Hello, Jenga!
```

### 3.2 Bibliothèque Simple

#### Structure
```
mathlib/
├── mathlib.jenga
├── include/
│   └── math.h
└── src/
    └── math.cpp
```

#### math.h
```cpp
#pragma once

namespace math {
    int add(int a, int b);
    int multiply(int a, int b);
}
```

#### math.cpp
```cpp
#include "math.h"

namespace math {
    int add(int a, int b) {
        return a + b;
    }
    
    int multiply(int a, int b) {
        return a * b;
    }
}
```

#### mathlib.jenga
```python
with workspace("MathLib"):
    
    with project("Math"):
        staticlib()
        language("C++")
        
        location(".")
        
        files([
            "src/**.cpp",
            "include/**.h"
        ])
        
        includedirs(["include"])
        
        targetdir("Build/Lib/%{cfg.buildcfg}")
```

#### Build
```bash
jenga build
# ✓ Built: Build/Lib/Debug/libMath.a
```

### 3.3 Projet avec Dépendances

#### Structure
```
app/
├── app.jenga
├── MathLib/
│   ├── include/math.h
│   └── src/math.cpp
└── App/
    └── main.cpp
```

#### main.cpp
```cpp
#include <iostream>
#include "math.h"

int main() {
    std::cout << "2 + 3 = " << math::add(2, 3) << std::endl;
    std::cout << "4 * 5 = " << math::multiply(4, 5) << std::endl;
    return 0;
}
```

#### app.jenga
```python
with workspace("App"):
    
    # Bibliothèque Math
    with project("Math"):
        staticlib()
        location("MathLib")
        
        files(["src/**.cpp"])
        includedirs(["include"])
    
    # Application
    with project("App"):
        consoleapp()
        location("App")
        
        files(["main.cpp"])
        
        # Dépendance
        dependson(["Math"])
        includedirs(["MathLib/include"])
```

#### Build & Run
```bash
jenga build
jenga run --project App

# Output:
# 2 + 3 = 5
# 4 * 5 = 20
```

### 3.4 Premier Test

#### Structure
```
calculator/
├── calculator.jenga
├── src/
│   ├── calculator.h
│   ├── calculator.cpp
│   └── main.cpp
└── tests/
    └── calculator_tests.cpp
```

#### calculator.h
```cpp
#pragma once

class Calculator {
public:
    int add(int a, int b);
    int subtract(int a, int b);
};
```

#### calculator.cpp
```cpp
#include "calculator.h"

int Calculator::add(int a, int b) {
    return a + b;
}

int Calculator::subtract(int a, int b) {
    return a - b;
}
```

#### calculator_tests.cpp
```cpp
#include "calculator.h"
#include <cassert>
#include <iostream>

void test_add() {
    Calculator calc;
    assert(calc.add(2, 3) == 5);
    assert(calc.add(-1, 1) == 0);
    std::cout << "✓ test_add passed" << std::endl;
}

void test_subtract() {
    Calculator calc;
    assert(calc.subtract(5, 3) == 2);
    assert(calc.subtract(0, 5) == -5);
    std::cout << "✓ test_subtract passed" << std::endl;
}

int main() {
    test_add();
    test_subtract();
    std::cout << "\n✅ All tests passed!" << std::endl;
    return 0;
}
```

#### calculator.jenga
```python
with workspace("Calculator"):
    
    with project("Calculator"):
        consoleapp()
        location(".")
        
        files([
            "src/calculator.cpp",
            "src/main.cpp"
        ])
        
        includedirs(["src"])
        
        # Tests imbriqués
        with test("Unit"):
            testfiles(["tests/calculator_tests.cpp"])
            testmainfile("src/main.cpp")
```

#### Build & Test
```bash
# Build
jenga build

# Run tests
jenga run --project Calculator_Unit_Tests

# Output:
# ✓ test_add passed
# ✓ test_subtract passed
# 
# ✅ All tests passed!
```

---

## Chapitre 4: Architecture

### 4.1 Vue d'Ensemble

```
Jenga Build System
├── Tools/
│   ├── jenga.py              # Entry point
│   ├── core/
│   │   ├── api.py            # DSL API
│   │   ├── loader.py         # .jenga loader
│   │   ├── buildsystem.py    # Compilation engine
│   │   ├── androidsystem.py  # Android builder
│   │   └── emscripten.py     # WebAssembly builder
│   ├── Commands/
│   │   ├── build.py          # Build command
│   │   ├── clean.py          # Clean command
│   │   ├── package.py        # Package command
│   │   ├── sign.py           # Sign command
│   │   └── keygen.py         # Keygen command
│   └── utils/
│       ├── display.py        # Console output
│       └── reporter.py       # Build reporter
└── Workspace/
    ├── myproject.jenga       # Configuration
    ├── .cjenga/              # Build cache
    │   └── cbuild.json
    └── Build/                # Artifacts
        ├── Bin/
        ├── Lib/
        └── Obj/
```

### 4.2 Flux d'Exécution

```
1. jenga build
   ↓
2. Parse arguments
   ↓
3. Load .jenga file
   ↓
4. Execute DSL
   ↓
5. Build dependency graph
   ↓
6. Compile in order
   ↓
7. Link binaries
   ↓
8. Copy dependencies
   ↓
9. Success!
```

### 4.3 Cache System

```
.cjenga/
└── cbuild.json
    {
      "files": {
        "src/main.cpp": {
          "hash": "abc123...",
          "mtime": 1674567890,
          "size": 1234,
          "object": "Build/Obj/main.o"
        }
      }
    }
```

**Algorithme** :
1. Check mtime + size
2. Si changé → recompile
3. Sinon → use cached .o
4. **Résultat : 20x plus rapide**

---

Fin de la Partie I - Introduction et Bases

[Suite dans BOOK_PART_2.md]
