# 🎯 Utiliser MSVC (Visual Studio) avec Jenga

## ✅ Support MSVC Complet

Jenga Build System supporte maintenant **Microsoft Visual C++ (MSVC)** avec **cl.exe**, **link.exe**, et **lib.exe**.

## 🔧 Détection Automatique

Jenga détecte automatiquement MSVC et adapte les flags de compilation :

### Détecté Automatiquement
- ✅ `cl.exe` → Compilateur MSVC
- ✅ `link.exe` → Linker MSVC
- ✅ `lib.exe` → Archiver MSVC

### Flags Automatiques

**GCC/Clang** → **MSVC** :
```
-std=c++20    →  /std:c++20
-O0           →  /Od
-O2           →  /O2
-O3           →  /Ox
-g            →  /Zi /FS
-DDEFINE      →  /DDEFINE
-Iinclude     →  /Iinclude
-c file.cpp   →  /c file.cpp
-o output.o   →  /Fooutput.obj
-shared       →  /DLL
-L/path       →  /LIBPATH:/path
-llib         →  lib.lib
```

## 📋 Configuration

### Option 1: Détection Automatique (Recommandé)

Si `cl.exe` est dans votre PATH, Jenga l'utilisera automatiquement :

```python
with workspace("MyApp"):
    # Pas de configuration nécessaire !
    # Jenga détecte cl.exe automatiquement
    
    with project("App"):
        consoleapp()
        language("C++")
        cppdialect("C++20")
        files(["src/**.cpp"])
```

### Option 2: Toolchain Explicite

Forcer l'utilisation de MSVC :

```python
with workspace("MyApp"):
    
    # Définir toolchain MSVC
    with toolchain("msvc", "cl.exe"):
        cppcompiler("cl.exe")
        ccompiler("cl.exe")
        linker("link.exe")
        archiver("lib.exe")
    
    with project("App"):
        consoleapp()
        usetoolchain("msvc")
        files(["src/**.cpp"])
```

### Option 3: Chemin Complet

Si cl.exe n'est pas dans PATH :

```python
with toolchain("msvc", "cl.exe"):
    cppcompiler("C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/cl.exe")
    linker("C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/link.exe")
    archiver("C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/lib.exe")
```

## 🚀 Utilisation

### Compilation Simple

```python
# myapp.jenga
with workspace("MyApp"):
    configurations(["Debug", "Release"])
    
    with project("App"):
        consoleapp()
        language("C++")
        cppdialect("C++20")
        
        files(["src/**.cpp"])
        includedirs(["include"])
        
        with filter("configurations:Debug"):
            defines(["DEBUG", "_DEBUG"])
            optimize("Off")
            symbols("On")
        
        with filter("configurations:Release"):
            defines(["NDEBUG"])
            optimize("Full")
            symbols("Off")
```

**Build** :
```powershell
jenga build
```

**Résultat** :
```
Compiling with MSVC:
  cl.exe /std:c++20 /Od /Zi /FS /DDEBUG /D_DEBUG /Iinclude /c src/main.cpp /Fosrc/main.obj
Linking with link.exe:
  link.exe /nologo /OUT:App.exe /DEBUG src/main.obj
```

### Bibliothèque Statique

```python
with project("MyLib"):
    staticlib()
    language("C++")
    
    files(["src/**.cpp"])
    includedirs(["include"])
```

**Compilation** :
```
cl.exe /std:c++20 /c src/lib.cpp /Fosrc/lib.obj
lib.exe /nologo /OUT:MyLib.lib src/lib.obj
```

### Bibliothèque Partagée (DLL)

```python
with project("MyDLL"):
    sharedlib()
    language("C++")
    
    files(["src/**.cpp"])
    defines(["MYDLL_EXPORTS"])
```

**Compilation** :
```
cl.exe /std:c++20 /DMYDLL_EXPORTS /c src/dll.cpp /Fosrc/dll.obj
link.exe /nologo /DLL /OUT:MyDLL.dll src/dll.obj
```

## 🔗 Linkage avec MSVC

### Bibliothèques Système Windows

```python
with project("WinApp"):
    windowedapp()
    
    links([
        "kernel32",   # → kernel32.lib
        "user32",     # → user32.lib
        "gdi32",      # → gdi32.lib
        "shell32"     # → shell32.lib
    ])
```

### Dépendances entre Projets

```python
with workspace("Multi"):
    
    with project("Math"):
        staticlib()
        files(["Math/**.cpp"])
    
    with project("App"):
        consoleapp()
        files(["App/**.cpp"])
        
        # Lie automatiquement Math.lib
        dependson(["Math"])
```

**Link** :
```
link.exe /nologo App/main.obj Build/Lib/Debug/Math.lib /OUT:App.exe
```

## 📊 Flags de Compilation MSVC

### Standards C++

```python
cppdialect("C++11")  # → /std:c++11
cppdialect("C++14")  # → /std:c++14
cppdialect("C++17")  # → /std:c++17
cppdialect("C++20")  # → /std:c++20
```

### Optimisation

```python
optimize("Off")    # → /Od  (Debug)
optimize("Size")   # → /O1  (Taille)
optimize("Speed")  # → /O2  (Vitesse)
optimize("Full")   # → /Ox  (Maximum)
```

### Symboles Debug

```python
symbols("On")   # → /Zi /FS  (Debug info)
symbols("Off")  # → (pas de debug)
```

### Runtime Library

Automatiquement sélectionné :
```
Debug   → /MDd  (Multithreaded Debug DLL)
Release → /MD   (Multithreaded DLL)
```

### Flags Additionnels

Automatiquement ajoutés par Jenga :
```
/EHsc    # Exception handling
/W3      # Warning level 3
/nologo  # Pas de banner
```

## 🎯 Exemple Complet Multi-Toolchain

```python
with workspace("CrossCompiler"):
    configurations(["Debug", "Release"])
    
    # Toolchain GCC
    with toolchain("gcc", "g++"):
        cppcompiler("g++")
    
    # Toolchain MSVC
    with toolchain("msvc", "cl.exe"):
        cppcompiler("cl.exe")
        linker("link.exe")
        archiver("lib.exe")
    
    # Toolchain Clang
    with toolchain("clang", "clang++"):
        cppcompiler("clang++")
    
    # Projet avec GCC
    with project("App_GCC"):
        consoleapp()
        usetoolchain("gcc")
        files(["src/**.cpp"])
    
    # Projet avec MSVC
    with project("App_MSVC"):
        consoleapp()
        usetoolchain("msvc")
        files(["src/**.cpp"])
    
    # Projet avec Clang
    with project("App_Clang"):
        consoleapp()
        usetoolchain("clang")
        files(["src/**.cpp"])
```

**Build** :
```powershell
jenga build
```

**Résultat** :
- `App_GCC.exe` (compilé avec g++)
- `App_MSVC.exe` (compilé avec cl.exe)
- `App_Clang.exe` (compilé avec clang++)

## 🔍 Vérification

### Diagnostic

```powershell
python diagnose.py
```

**Output** :
```
============================================================
  Compilers
============================================================
✓ GCC C++ Compiler (Linux/MinGW)
  Path: C:\msys64\ucrt64\bin\g++.EXE
✓ Clang C++ Compiler
  Path: C:\msys64\ucrt64\bin\clang++.EXE
✓ MSVC C++ Compiler (Windows)
  Path: C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\cl.EXE
```

### Mode Verbose

Pour voir les commandes exactes :

```powershell
jenga build --verbose
```

**Output** :
```
Command: cl.exe /std:c++20 /Od /Zi /FS /DDEBUG /EHsc /W3 /nologo /MDd /Iinclude /c src/main.cpp /Fosrc/main.obj
Link command: link.exe /nologo src/main.obj /OUT:Build/Bin/Debug/App.exe /DEBUG
```

## ⚠ Notes Importantes

### PATH Environnement

Pour utiliser MSVC directement, ouvrez **Developer Command Prompt for VS** ou configurez l'environnement :

```powershell
# Developer PowerShell for VS 2022
# Ouvre automatiquement avec cl.exe dans PATH
```

Ou manuellement :
```powershell
# Appeler vcvarsall.bat
"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" x64
```

### Extensions Fichiers

MSVC utilise :
- `.obj` au lieu de `.o` (objets)
- `.lib` au lieu de `.a` (static libs)
- `.dll` au lieu de `.so` (shared libs)

Jenga gère automatiquement ces différences !

### Warnings

MSVC a des warnings différents de GCC/Clang. Les erreurs sont formatées automatiquement.

## 🎉 Succès !

Votre build avec MSVC devrait maintenant fonctionner :

```
Building project: MyApp
ℹ Found 5 source file(s)
✓   [1/5] Compiled: main.cpp
✓   [2/5] Compiled: utils.cpp
✓   [3/5] Compiled: core.cpp
✓   [4/5] Compiled: logger.cpp
✓   [5/5] Compiled: math.cpp
ℹ Linking...
✓ Built: E:\Projets\MyApp\Build\Bin\Debug\MyApp.exe

✓ Build completed successfully
```

---

**Version** : Jenga Build System v1.0.1
**Support MSVC** : Complet (cl.exe, link.exe, lib.exe)
**Date** : 2026-01-23
