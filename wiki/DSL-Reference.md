# DSL Reference

La DSL Jenga est exposée via:

```python
from Jenga import *
```

## Context managers principaux

- `workspace("Nom")`
- `project("NomProjet")`
- `toolchain("Nom", "clang|gcc|msvc|...")`
- `filter("system:Windows")`
- `unitest()`
- `test()`
- `include("autre.jenga")`
- `batchinclude([...])`

## Exemple complet

```python
from Jenga import *

with workspace("GameWorkspace"):
    configurations(["Debug", "Release"])
    targetoses([TargetOS.WINDOWS, TargetOS.LINUX])
    targetarchs([TargetArch.X86_64, TargetArch.ARM64])
    startproject("Game")

    with toolchain("linux_clang", "clang"):
        settarget("Linux", "x86_64", "gnu")
        cppcompiler("clang++")
        ccompiler("clang")
        cxxflags(["-O2"])

    usetoolchain("linux_clang")

    with project("Engine"):
        staticlib()
        language("C++")
        cppdialect("C++20")
        files(["engine/src/**.cpp", "engine/include/**.hpp"])
        includedirs(["engine/include"])

    with project("Game"):
        windowedapp()
        language("C++")
        files(["game/src/**.cpp"])
        includedirs(["game/include"])
        dependson(["Engine"])

        with filter("system:Windows"):
            links(["d3d11", "dxgi"])
            defines(["PLATFORM_WINDOWS"])
```

## Fonctions DSL utiles (projets)

- type de projet: `consoleapp`, `windowedapp`, `staticlib`, `sharedlib`, `testsuite`
- sources: `files`, `excludefiles`, `excludemainfiles`
- includes/libs: `includedirs`, `libdirs`, `links`, `dependson`, `dependfiles`
- sorties: `objdir`, `targetdir`, `targetname`
- compilation: `language`, `cppdialect`, `cdialect`, `defines`, `warnings`, `optimize`, `symbols`
- hooks: `prebuild`, `postbuild`, `prelink`, `postlink`

## Fonctions DSL utiles (toolchain)

- cible: `settarget`, `targettriple`, `sysroot`
- executables: `ccompiler`, `cppcompiler`, `linker`, `archiver`
- flags: `cflags`, `cxxflags`, `ldflags`, `asmflags`, `arflags`
- options avancées: `sanitize`, `pic`, `pie`, `nostdlib`, `nostdinc`

## Bonnes pratiques

- garde les patterns de fichiers explicites (`src/**.cpp`, `include/**.hpp`)
- mets un `startproject(...)` pour simplifier `jenga run`
- dédie un projet pour chaque bibliothèque majeure
- utilise `dependson([...])` pour garder un graphe clair
