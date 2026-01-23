# 📦 Guide Complet - Projets Externes et Inclusion

## Table des Matières

1. [Introduction](#introduction)
2. [Définir des Projets Externes](#définir-des-projets-externes)
3. [Inclure des Projets](#inclure-des-projets)
4. [Inclusion Sélective](#inclusion-sélective)
5. [Exemples Complets](#exemples-complets)
6. [Dépendances entre Projets Externes](#dépendances-entre-projets-externes)
7. [Best Practices](#best-practices)

---

## Introduction

Jenga permet de **réutiliser des projets** définis dans d'autres fichiers `.jenga` sans dupliquer le code.

### Avantages

✅ **Réutilisabilité** - Définir une bibliothèque une seule fois
✅ **Modularité** - Organiser les projets en modules
✅ **Maintenabilité** - Un seul endroit à mettre à jour
✅ **Flexibilité** - Inclure tous ou seulement certains projets

---

## Définir des Projets Externes

Il existe **deux façons** de définir des projets externes :

### 1. Projets dans un Workspace Externe

**Fichier** : `external/MathLib/mathlib.jenga`

```python
# Workspace externe complet
with workspace("MathLib"):
    configurations(["Debug", "Release"])
    
    # Projet 1: Vector Math
    with project("Vector"):
        staticlib()
        language("C++")
        cppdialect("C++17")
        
        location("Vector")
        files(["src/**.cpp"])
        includedirs(["include"])
    
    # Projet 2: Matrix Math
    with project("Matrix"):
        staticlib()
        language("C++")
        
        location("Matrix")
        files(["src/**.cpp"])
        includedirs(["include"])
        
        # Dépend de Vector
        dependson(["Vector"])
    
    # Projet 3: Advanced Math (optionnel)
    with project("Advanced"):
        staticlib()
        location("Advanced")
        files(["src/**.cpp"])
        
        dependson(["Vector", "Matrix"])
```

**Structure** :
```
external/MathLib/
├── mathlib.jenga
├── Vector/
│   ├── src/
│   │   └── vector.cpp
│   └── include/
│       └── vector.h
├── Matrix/
│   ├── src/
│   │   └── matrix.cpp
│   └── include/
│       └── matrix.h
└── Advanced/
    ├── src/
    │   └── advanced.cpp
    └── include/
        └── advanced.h
```

### 2. Projets HORS Workspace (Standalone)

**Fichier** : `libs/Logger/logger.jenga`

```python
# Pas de workspace ! Projets définis directement

# Projet 1: Core Logger
with project("Logger"):
    staticlib()
    language("C++")
    
    location(".")  # Relatif au fichier .jenga
    files(["src/Logger.cpp"])
    includedirs(["include"])

# Projet 2: File Logger
with project("FileLogger"):
    staticlib()
    
    location(".")
    files(["src/FileLogger.cpp"])
    includedirs(["include"])
    
    # Dépend de Logger
    dependson(["Logger"])

# Projet 3: Network Logger (optionnel)
with project("NetworkLogger"):
    staticlib()
    
    location(".")
    files(["src/NetworkLogger.cpp"])
    
    dependson(["Logger"])
```

**⚠ Important** : Quand il n'y a pas de workspace dans le fichier externe, les projets sont ajoutés **directement** au workspace appelant.

---

## Inclure des Projets

### Syntaxe de Base

```python
include(jenga_file: str, projects: list = None)
```

**Arguments** :
- `jenga_file` : Chemin vers le fichier `.jenga`
- `projects` : Liste des projets à inclure (optionnel)
  - `None` ou omis : Inclure **TOUS** les projets
  - `["ProjectA", "ProjectB"]` : Inclure **seulement** ces projets
  - `["*"]` : Explicite - inclure tous (équivalent à `None`)

### Inclusion Complète (Tous les Projets)

```python
with workspace("MyApp"):
    
    # Inclure TOUS les projets de mathlib.jenga
    include("external/MathLib/mathlib.jenga")
    
    # Projets disponibles: Vector, Matrix, Advanced
    
    with project("App"):
        consoleapp()
        dependson(["Vector", "Matrix"])
```

**Résultat** : Les 3 projets (Vector, Matrix, Advanced) sont ajoutés au workspace.

---

## Inclusion Sélective

### Inclure Certains Projets

```python
with workspace("MyApp"):
    
    # Inclure SEULEMENT Vector et Matrix
    include("external/MathLib/mathlib.jenga", ["Vector", "Matrix"])
    
    # Advanced n'est PAS inclus !
    
    with project("App"):
        consoleapp()
        dependson(["Vector", "Matrix"])
```

**Résultat** : Seulement Vector et Matrix sont ajoutés. Advanced est ignoré.

### Exemples Pratiques

#### Exemple 1: Logger Minimal

```python
with workspace("SimpleApp"):
    
    # Inclure seulement le logger de base
    include("libs/Logger/logger.jenga", ["Logger"])
    
    # FileLogger et NetworkLogger ne sont PAS inclus
    
    with project("App"):
        consoleapp()
        dependson(["Logger"])
```

#### Exemple 2: Logger Complet

```python
with workspace("ServerApp"):
    
    # Inclure Logger + FileLogger + NetworkLogger
    include("libs/Logger/logger.jenga", ["Logger", "FileLogger", "NetworkLogger"])
    
    with project("Server"):
        consoleapp()
        dependson(["Logger", "FileLogger", "NetworkLogger"])
```

#### Exemple 3: Math Avancé Seulement

```python
with workspace("ScientificApp"):
    
    # Inclure tout le module Math
    include("external/MathLib/mathlib.jenga")
    
    # Mais on utilise seulement Advanced
    with project("App"):
        consoleapp()
        # Advanced dépend de Vector et Matrix, donc tout est lié automatiquement
        dependson(["Advanced"])
```

---

## Exemples Complets

### Exemple 1: Projet Externe Complet

**Fichier** : `external/Graphics/graphics.jenga`

```python
# Workspace Graphics avec plusieurs projets
with workspace("Graphics"):
    configurations(["Debug", "Release"])
    
    # Core Graphics
    with project("GraphicsCore"):
        staticlib()
        language("C++")
        cppdialect("C++20")
        
        location("Core")
        files(["src/**.cpp"])
        includedirs(["include"])
    
    # OpenGL Renderer
    with project("OpenGLRenderer"):
        staticlib()
        
        location("OpenGL")
        files(["src/**.cpp"])
        includedirs(["include"])
        
        dependson(["GraphicsCore"])
        links(["GL", "GLEW"])
    
    # Vulkan Renderer
    with project("VulkanRenderer"):
        staticlib()
        
        location("Vulkan")
        files(["src/**.cpp"])
        includedirs(["include"])
        
        dependson(["GraphicsCore"])
        links(["vulkan"])
    
    # 2D Helper (optionnel)
    with project("Graphics2D"):
        staticlib()
        
        location("2D")
        files(["src/**.cpp"])
        
        dependson(["GraphicsCore"])
```

**Utilisation - OpenGL seulement** :

```python
with workspace("MyGame"):
    
    # Inclure seulement OpenGL
    include("external/Graphics/graphics.jenga", ["GraphicsCore", "OpenGLRenderer"])
    
    with project("Game"):
        consoleapp()
        files(["src/**.cpp"])
        
        dependson(["OpenGLRenderer"])
        # GraphicsCore est automatiquement lié (dépendance d'OpenGLRenderer)
```

**Utilisation - Multi-renderer** :

```python
with workspace("GraphicsDemo"):
    
    # Inclure tous les renderers
    include("external/Graphics/graphics.jenga", 
            ["GraphicsCore", "OpenGLRenderer", "VulkanRenderer"])
    
    with project("Demo"):
        consoleapp()
        files(["src/**.cpp"])
        
        # Choisir le renderer au build time
        with filter("configurations:Debug"):
            dependson(["OpenGLRenderer"])
        
        with filter("configurations:Release"):
            dependson(["VulkanRenderer"])
```

### Exemple 2: Bibliothèque Sans Workspace

**Fichier** : `libs/Utils/utils.jenga`

```python
# Pas de workspace - projets standalone

# String utilities
with project("StringUtils"):
    staticlib()
    language("C++")
    
    location("String")
    files(["src/**.cpp"])
    includedirs(["include"])

# File utilities
with project("FileUtils"):
    staticlib()
    
    location("File")
    files(["src/**.cpp"])
    includedirs(["include"])

# Time utilities
with project("TimeUtils"):
    staticlib()
    
    location("Time")
    files(["src/**.cpp"])
    includedirs(["include"])

# All utilities (dépend de tous)
with project("Utils"):
    staticlib()
    
    location(".")
    files(["src/utils.cpp"])
    
    dependson(["StringUtils", "FileUtils", "TimeUtils"])
```

**Utilisation - Sélective** :

```python
with workspace("MyApp"):
    
    # Inclure seulement StringUtils et FileUtils
    include("libs/Utils/utils.jenga", ["StringUtils", "FileUtils"])
    
    with project("App"):
        consoleapp()
        dependson(["StringUtils", "FileUtils"])
```

---

## Dépendances entre Projets Externes

### Dépendances Automatiques

Les dépendances sont **résolues automatiquement** :

```python
# external/Math/math.jenga
with workspace("Math"):
    
    with project("Vector"):
        staticlib()
        files(["vector.cpp"])
    
    with project("Matrix"):
        staticlib()
        files(["matrix.cpp"])
        dependson(["Vector"])  # Matrix → Vector
    
    with project("Advanced"):
        staticlib()
        files(["advanced.cpp"])
        dependson(["Matrix"])  # Advanced → Matrix → Vector
```

**Utilisation** :

```python
with workspace("App"):
    
    # Inclure seulement Advanced
    include("external/Math/math.jenga", ["Advanced"])
    
    # ⚠ ERREUR ! Matrix et Vector ne sont pas inclus
    # Advanced ne peut pas compiler sans ses dépendances
```

**Solution 1** : Inclure les dépendances

```python
with workspace("App"):
    
    # Inclure Advanced + ses dépendances
    include("external/Math/math.jenga", ["Advanced", "Matrix", "Vector"])
    
    with project("App"):
        consoleapp()
        dependson(["Advanced"])
        # L'ordre de build est automatique: Vector → Matrix → Advanced → App
```

**Solution 2** : Inclure tout

```python
with workspace("App"):
    
    # Inclure tout le module Math
    include("external/Math/math.jenga")
    
    with project("App"):
        consoleapp()
        dependson(["Advanced"])  # Dépendances automatiques
```

### Dépendances entre Fichiers Externes

Vous pouvez inclure plusieurs fichiers externes :

```python
with workspace("GameEngine"):
    
    # Inclure Math library
    include("external/Math/math.jenga", ["Vector", "Matrix"])
    
    # Inclure Graphics library
    include("external/Graphics/graphics.jenga", ["GraphicsCore"])
    
    # Inclure Physics library
    include("external/Physics/physics.jenga")
    
    # Votre projet peut utiliser tous ces modules
    with project("Engine"):
        staticlib()
        files(["src/**.cpp"])
        
        dependson([
            "Vector",         # De Math
            "Matrix",         # De Math
            "GraphicsCore",   # De Graphics
            "PhysicsCore"     # De Physics
        ])
```

---

## Best Practices

### 1. Organisation des Fichiers

**Recommandé** :

```
MyProject/
├── myproject.jenga          # Workspace principal
├── external/                # Bibliothèques externes avec workspace
│   ├── MathLib/
│   │   ├── mathlib.jenga
│   │   └── (sources)
│   └── Graphics/
│       ├── graphics.jenga
│       └── (sources)
├── libs/                    # Bibliothèques standalone (sans workspace)
│   ├── Logger/
│   │   ├── logger.jenga
│   │   └── (sources)
│   └── Utils/
│       ├── utils.jenga
│       └── (sources)
└── src/                     # Votre code
    └── main.cpp
```

### 2. Nommage Cohérent

```python
# ✅ Bon : Noms clairs et distincts
with project("MathVector"):
    ...

with project("MathMatrix"):
    ...

# ❌ Éviter : Noms génériques
with project("Core"):  # Trop générique
    ...
```

### 3. Documentation des Dépendances

```python
# external/Graphics/graphics.jenga

"""
Graphics Library
================

Projets disponibles:
- GraphicsCore : Core graphics system (requis par tous)
- OpenGLRenderer : OpenGL 4.5 renderer (dépend de GraphicsCore)
- VulkanRenderer : Vulkan 1.2 renderer (dépend de GraphicsCore)
- Graphics2D : 2D helper utilities (dépend de GraphicsCore)

Inclusions recommandées:
- Pour OpenGL : include(..., ["GraphicsCore", "OpenGLRenderer"])
- Pour Vulkan : include(..., ["GraphicsCore", "VulkanRenderer"])
- Pour 2D : include(..., ["GraphicsCore", "Graphics2D"])
"""

with workspace("Graphics"):
    # ...
```

### 4. Versionning

```python
# libs/MyLib/mylib.jenga

# Version de la bibliothèque
LIB_VERSION = "2.1.0"

with project("MyLib"):
    staticlib()
    
    defines([f"MYLIB_VERSION={LIB_VERSION}"])
    
    # ...
```

### 5. Chemins Relatifs vs Absolus

```python
# ✅ Bon : Chemins relatifs au workspace
include("external/Math/math.jenga")

# ⚠ Acceptable : Absolu si bibliothèque système
include("/usr/local/share/mylib/mylib.jenga")

# ❌ Éviter : Chemins hardcodés spécifiques
include("C:/Users/John/Projects/lib/mylib.jenga")
```

---

## Résumé des Syntaxes

```python
# Inclure TOUS les projets
include("path/to/file.jenga")
include("path/to/file.jenga", ["*"])  # Équivalent

# Inclure UN projet
include("path/to/file.jenga", ["ProjectA"])

# Inclure PLUSIEURS projets
include("path/to/file.jenga", ["ProjectA", "ProjectB", "ProjectC"])

# Exemple complet
with workspace("MyApp"):
    
    # Inclusion complète
    include("external/FullLib/lib.jenga")
    
    # Inclusion sélective
    include("external/Graphics/graphics.jenga", ["GraphicsCore", "OpenGLRenderer"])
    
    # Inclusion minimale
    include("libs/Logger/logger.jenga", ["Logger"])
    
    with project("App"):
        consoleapp()
        dependson(["GraphicsCore", "Logger"])
```

---

**Version** : Jenga Build System v1.0.1
**Date** : 2026-01-23
