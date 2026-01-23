# Jenga Build System - Le Guide Complet
# PARTIE II - CONCEPTS FONDAMENTAUX

## Chapitre 5: Workspaces et Projets

### 5.1 Workspace

Le **workspace** est le conteneur racine.

#### Syntaxe
```python
with workspace("MonWorkspace"):
    # Configuration globale
    configurations(["Debug", "Release", "Dist"])
    platforms(["Windows", "Linux", "MacOS"])
    startproject("App")
    
    # SDK paths (Android)
    androidsdkpath("/path/to/sdk")
    androidndkpath("/path/to/ndk")
    
    # Projets
    with project("Lib"):
        # ...
    
    with project("App"):
        # ...
```

#### Attributs

| Attribut | Description | Exemple |
|----------|-------------|---------|
| `name` | Nom du workspace | `"MyApp"` |
| `location` | Racine du workspace | `"."` |
| `configurations` | Configs disponibles | `["Debug", "Release"]` |
| `platforms` | Plateformes ciblées | `["Windows", "Android"]` |
| `startproject` | Projet par défaut | `"MainApp"` |

### 5.2 Project

Les **projets** sont les unités de build.

#### Types de Projets

```python
# Application console
with project("App"):
    consoleapp()

# Application fenêtrée (GUI)
with project("GUI"):
    windowedapp()

# Bibliothèque statique (.a, .lib)
with project("Core"):
    staticlib()

# Bibliothèque partagée (.so, .dll, .dylib)
with project("Plugin"):
    sharedlib()
```

#### Configuration de Base

```python
with project("Engine"):
    staticlib()
    language("C++")
    cppdialect("C++20")
    
    location("Engine")  # Dossier du projet
    
    files([
        "src/**.cpp",
        "src/**.h",
        "include/**.h"
    ])
    
    includedirs([
        "include",
        "third_party/glm"
    ])
    
    targetdir("Build/Lib/%{cfg.buildcfg}")
    objdir("Build/Obj/%{cfg.buildcfg}/%{prj.name}")
```

#### Variables Spéciales

| Variable | Description | Exemple |
|----------|-------------|---------|
| `%{wks.location}` | Racine workspace | `/home/user/project` |
| `%{prj.name}` | Nom projet | `Engine` |
| `%{cfg.buildcfg}` | Configuration | `Debug` ou `Release` |
| `%{cfg.platform}` | Plateforme | `Linux` |

### 5.3 Dépendances

#### dependson()

Dépendances entre projets :

```python
with workspace("Game"):
    
    with project("Math"):
        staticlib()
        files(["Math/**.cpp"])
    
    with project("Physics"):
        staticlib()
        files(["Physics/**.cpp"])
        dependson(["Math"])  # Physics → Math
    
    with project("Engine"):
        staticlib()
        files(["Engine/**.cpp"])
        dependson(["Math", "Physics"])  # Engine → Math, Physics
    
    with project("Game"):
        consoleapp()
        files(["Game/**.cpp"])
        dependson(["Engine"])  # Game → Engine → Physics → Math
```

**Ordre de build automatique** :
```
1. Math
2. Physics
3. Engine
4. Game
```

#### links()

Liaison avec bibliothèques système :

```python
with project("OpenGLApp"):
    consoleapp()
    
    # Bibliothèques système
    links([
        "GL",      # OpenGL
        "GLU",     # OpenGL Utilities
        "glfw3",   # GLFW
        "pthread"  # Threads
    ])
```

#### libdirs()

Chemins de recherche pour bibliothèques :

```python
with project("App"):
    consoleapp()
    
    libdirs([
        "/usr/local/lib",
        "third_party/libs"
    ])
    
    links(["mylib"])
```

### 5.4 Files

#### Patterns

```python
files([
    "src/**.cpp",           # Tous les .cpp récursivement
    "src/**.h",             # Tous les .h
    "include/*.h",          # .h non récursifs
    "platform/linux/*.cpp"  # Spécifique plateforme
])
```

#### Exclusion

```python
files(["src/**.cpp"])

excludefiles([
    "src/old/**",
    "src/experimental/**"
])
```

#### Préfixe "/"

```python
location("Engine")

files([
    "/src/**.cpp",      # Relatif à Engine/src
    "/include/**.h"     # Relatif à Engine/include
])
```

### 5.5 Defines

#### Globaux

```python
with project("App"):
    defines([
        "APP_VERSION=1.0",
        "USE_OPENGL",
        "_DEBUG"
    ])
```

#### Conditionnels

```python
with project("App"):
    
    with filter("configurations:Debug"):
        defines(["DEBUG", "_DEBUG"])
    
    with filter("configurations:Release"):
        defines(["NDEBUG", "RELEASE"])
    
    with filter("system:Windows"):
        defines(["_WIN32", "WIN32_LEAN_AND_MEAN"])
    
    with filter("system:Linux"):
        defines(["_LINUX", "__linux__"])
```

---

## Chapitre 6: Configurations et Plateformes

### 6.1 Configurations

Les **configurations** définissent les variantes de build.

#### Standard

```python
with workspace("MyApp"):
    configurations(["Debug", "Release"])
```

#### Personnalisées

```python
with workspace("GameEngine"):
    configurations([
        "Debug",
        "Release",
        "Dist",          # Distribution
        "Profile",       # Profiling
        "Coverage"       # Code coverage
    ])
```

#### Configuration par Projet

```python
with project("Engine"):
    staticlib()
    
    # Debug
    with filter("configurations:Debug"):
        defines(["DEBUG", "_DEBUG"])
        optimize("Off")
        symbols("On")
    
    # Release
    with filter("configurations:Release"):
        defines(["NDEBUG"])
        optimize("Speed")
        symbols("Off")
    
    # Dist (optimisation maximale)
    with filter("configurations:Dist"):
        defines(["NDEBUG", "DIST_BUILD"])
        optimize("Full")
        symbols("Off")
```

### 6.2 Platforms

Les **plateformes** ciblent différents OS.

#### Plateformes Supportées

```python
with workspace("CrossPlatform"):
    platforms([
        "Windows",      # Windows 10/11
        "Linux",        # Ubuntu, Fedora, etc.
        "MacOS",        # macOS 10.15+
        "Android",      # Android 5.0+ (API 21+)
        "iOS",          # iOS 12+
        "Emscripten"    # WebAssembly
    ])
```

#### Configuration Spécifique

```python
with project("Game"):
    consoleapp()
    
    # Commun
    files(["src/core/**.cpp"])
    
    # Windows
    with filter("system:Windows"):
        files(["src/platform/windows/**.cpp"])
        defines(["PLATFORM_WINDOWS"])
        links(["kernel32", "user32", "gdi32"])
    
    # Linux
    with filter("system:Linux"):
        files(["src/platform/linux/**.cpp"])
        defines(["PLATFORM_LINUX"])
        links(["X11", "pthread", "dl"])
    
    # Android
    with filter("system:Android"):
        files(["src/platform/android/**.cpp"])
        defines(["PLATFORM_ANDROID"])
        links(["log", "android", "EGL", "GLESv3"])
```

### 6.3 Filters

Les **filters** permettent la configuration conditionnelle.

#### Syntaxe

```python
with filter("pattern"):
    # Configuration conditionnelle
```

#### Patterns

**Configuration** :
```python
with filter("configurations:Debug"):
    # ...

with filter("configurations:Release or configurations:Dist"):
    # ...
```

**Plateforme** :
```python
with filter("system:Windows"):
    # ...

with filter("system:Linux or system:MacOS"):
    # ...
```

**Combinaison** :
```python
with filter("configurations:Debug and system:Windows"):
    defines(["DEBUG_WINDOWS"])
```

#### Imbrication

```python
with project("App"):
    
    with filter("system:Windows"):
        files(["src/windows/**.cpp"])
        
        with filter("configurations:Debug"):
            defines(["WIN_DEBUG"])
        
        with filter("configurations:Release"):
            defines(["WIN_RELEASE"])
```

### 6.4 Optimization

```python
with project("Engine"):
    
    with filter("configurations:Debug"):
        optimize("Off")     # -O0
        symbols("On")       # -g
    
    with filter("configurations:Release"):
        optimize("Speed")   # -O2
        symbols("Off")      # -g0
    
    with filter("configurations:Dist"):
        optimize("Full")    # -O3
        symbols("Off")
```

**Niveaux d'optimisation** :

| Niveau | Flag GCC/Clang | Description |
|--------|----------------|-------------|
| `Off` | `-O0` | Aucune optimisation |
| `Size` | `-Os` | Taille minimale |
| `Speed` | `-O2` | Performance équilibrée |
| `Full` | `-O3` | Performance maximale |

---

## Chapitre 7: Toolchains

### 7.1 Qu'est-ce qu'un Toolchain ?

Un **toolchain** définit les outils de compilation.

#### Composants

- **Compiler** : g++, clang++, cl
- **Linker** : ld, link.exe
- **Archiver** : ar, lib.exe

### 7.2 Toolchains Prédéfinis

```python
with workspace("MyApp"):
    
    # GCC (défaut Linux)
    with toolchain("default", "g++"):
        cppcompiler("g++")
    
    # Clang
    with toolchain("clang", "clang++"):
        cppcompiler("clang++")
    
    # MSVC (Windows)
    with toolchain("msvc", "cl"):
        cppcompiler("cl")
```

### 7.3 Configuration Avancée

```python
with workspace("Advanced"):
    
    with toolchain("gcc-11", "g++-11"):
        cppcompiler("/usr/bin/g++-11")
        ccompiler("/usr/bin/gcc-11")
        linker("/usr/bin/g++-11")
        archiver("/usr/bin/ar")
        
        # Flags globaux
        cflags(["-Wall", "-Wextra"])
        cxxflags(["-std=c++20", "-pedantic"])
        ldflags(["-lpthread"])
        
        # Defines
        defines(["CUSTOM_TOOLCHAIN"])
```

### 7.4 Toolchain par Projet

```python
with workspace("Multi"):
    
    with toolchain("gcc", "g++"):
        # ...
    
    with toolchain("clang", "clang++"):
        # ...
    
    # Projet avec GCC
    with project("EngineGCC"):
        staticlib()
        usetoolchain("gcc")
    
    # Projet avec Clang
    with project("EngineClang"):
        staticlib()
        usetoolchain("clang")
```

### 7.5 Fonctions Toolchain Avancées

#### Flags Individuels

```python
with toolchain("custom", "g++"):
    
    # Ajouter un flag
    addflag("-ffast-math")
    
    # Flags C
    addcflag("-std=c11")
    
    # Flags C++
    addcxxflag("-std=c++20")
    
    # Flags linker
    addldflag("-lpthread")
```

#### Position Independent Code

```python
with toolchain("pic", "g++"):
    pic()   # -fPIC (shared lib)
    pie()   # -fPIE (executable)
```

#### Sanitizers

```python
with toolchain("asan", "clang++"):
    sanitize("address")      # AddressSanitizer
    sanitize("thread")       # ThreadSanitizer
    sanitize("undefined")    # UndefinedBehaviorSanitizer
```

#### Warnings

```python
with toolchain("strict", "g++"):
    warnings("all")          # -Wall
    warnings("extra")        # -Wextra
    warnings("pedantic")     # -pedantic
    warnings("error")        # -Werror
```

#### Profiling & Coverage

```python
with toolchain("profile", "g++"):
    profile(True)    # -pg
    coverage(True)   # --coverage
```

#### macOS Frameworks

```python
with toolchain("macos", "clang++"):
    framework("Cocoa")
    framework("OpenGL")
    framework("CoreFoundation")
```

---

## Chapitre 8: Tests Unitaires

### 8.1 Système de Tests Intégré

Jenga inclut **Unitest**, un framework de tests moderne.

#### Caractéristiques

✅ Auto-injection de main
✅ Dépendances automatiques
✅ Reporter élégant
✅ Parallélisation
✅ Filtrage

### 8.2 Création de Tests

#### Syntaxe (IMBRIQUÉ)

```python
with workspace("Calculator"):
    
    with project("Calculator"):
        consoleapp()
        files(["src/**.cpp"])
        
        # Tests DANS le projet !
        with test("Unit"):
            testfiles(["tests/**.cpp"])
            testmainfile("src/main.cpp")  # Exclu
```

**Résultat** :
- Projet `Calculator`
- Projet `Calculator_Unit_Tests` (auto-créé)
- Dépendances auto : `Calculator` + `__Unitest__`

### 8.3 Écrire des Tests

#### Exemple Simple

```cpp
// tests/math_tests.cpp
#include <cassert>
#include <iostream>

void test_addition() {
    assert(2 + 2 == 4);
    std::cout << "✓ test_addition passed" << std::endl;
}

void test_multiplication() {
    assert(3 * 4 == 12);
    std::cout << "✓ test_multiplication passed" << std::endl;
}

int main() {
    test_addition();
    test_multiplication();
    std::cout << "\n✅ All tests passed!" << std::endl;
    return 0;
}
```

### 8.4 Main Auto-Injecté

Si vous n'écrivez pas de main, Jenga l'injecte :

```cpp
// Votre test (pas de main nécessaire)
#include <cassert>

void test_add() {
    assert(1 + 1 == 2);
}

// Main injecté automatiquement par Jenga
// int main() { ... }
```

### 8.5 Options de Tests

```python
with test("Advanced"):
    testfiles(["tests/**.cpp"])
    
    testoptions([
        "--verbose",           # Sortie détaillée
        "--parallel",          # Tests parallèles
        "--filter=Math*",      # Filtrer par nom
        "--report=results.xml" # Rapport XML
    ])
```

### 8.6 Reporter

**Sortie console** :
```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                       UNIT TEST FRAMEWORK - TEST REPORT                         ║
╚══════════════════════════════════════════════════════════════════════════════════╝

  STATUS  TEST NAME                              ASSERTIONS    SUCCESS RATE    TIME
  ──────  ─────────────────────────────────────  ────────────  ─────────────  ───────
  ✓    Calculator::Addition                       4/4          100.0%         0.8ms
  ✓    Calculator::Subtraction                    3/3          100.0%         0.5ms

┌─────────────────────────────────── SUMMARY ───────────────────────────────────┐
│ Tests:        2 passed, 0 failed, 2 total                                     │
│ Success Rate: 100.0%                                                          │
│ Result:       ✅ ALL TESTS PASSED                                             │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

Fin de la Partie II - Concepts Fondamentaux

[Suite dans BOOK_PART_3.md]
