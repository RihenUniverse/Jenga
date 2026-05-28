# Premier Workspace / First Workspace

**Langues / Languages :** [Français](#français) · [English](#english)

---

## Français

Cette page propose un parcours « clé en main » pour démarrer rapidement.

### 1. Créer un workspace

#### Mode interactif (recommandé pour débuter)

```bash
jenga workspace DemoWorkspace --interactive
```

Le mode interactif pose une série de questions : nom, chemin, configurations
(`Debug, Release`), OS cibles, architectures, compilateur préféré, dialecte C++,
création d'un projet initial, activation de Unitest.

#### Mode direct

```bash
jenga workspace DemoWorkspace \
  --configs Debug,Release \
  --oses Windows,Linux,macOS \
  --archs x86_64
```

### 2. Ajouter un projet

```bash
jenga project DemoApp --kind console --lang C++
```

`--kind` accepte : `console`, `windowed`, `static`, `shared`, `test`.

> Chaque projet est créé dans un **dossier portant son nom**, sous le workspace.
> Avec `--location apps`, le projet va dans `apps/DemoApp/`.

### 3. Structure générée

```text
DemoWorkspace/
├── DemoWorkspace.jenga      # point d'entrée du workspace
└── DemoApp/                 # dossier au nom du projet
    ├── src/
    │   └── main.cpp
    └── include/
```

Avec plusieurs projets, chacun a son propre dossier :

```text
DemoWorkspace/
├── DemoWorkspace.jenga
├── DemoApp/                 # jenga project DemoApp
│   └── src/main.cpp
├── Engine/                  # jenga project Engine --kind static
│   ├── src/
│   └── include/
└── apps/
    └── Tool/                # jenga project Tool --location apps
        └── src/main.cpp
```

### 4. Anatomie d'un fichier `.jenga`

Un fichier `.jenga` est du **Python standard** enrichi du DSL Jenga :

```python
from Jenga import *

with workspace("DemoWorkspace"):
    configurations(["Debug", "Release"])
    targetoses([TargetOS.WINDOWS, TargetOS.LINUX, TargetOS.MACOS])
    targetarchs([TargetArch.X86_64])
    startproject("DemoApp")

    with project("DemoApp"):
        consoleapp()
        language("C++")
        cppdialect("C++20")
        files(["src/**.cpp", "include/**.hpp"])
        includedirs(["include"])

        # Spécifique à une plateforme via un filtre
        with filter("system:Windows"):
            links(["user32"])
        with filter("config:Debug"):
            defines(["DEBUG_MODE"])
```

> Pour la cross-compilation et la détection automatique des toolchains, ajoutez
> `RegisterJengaGlobalToolchains()` au début du workspace (voir
> [Toolchains et Sysroots](Toolchains-et-Sysroots.md)).

### 5. Compiler, exécuter, déboguer

```bash
jenga build --config Debug
jenga run DemoApp
jenga gdb DemoApp --break main --run    # déboguer avec GDB (ou LLDB)
jenga build --config Release --platform Linux-x86_64   # cross-compile
jenga build -j8                                        # 8 jobs parallèles
```

### 6. Ajouter du contenu rapidement

```bash
jenga file DemoApp --src "src/utils.cpp"   # ajoute des sources
jenga file DemoApp --inc include           # ajoute un include dir
jenga file DemoApp --link pthread          # ajoute une lib
jenga file DemoApp --def APP_VERSION=1     # ajoute un define
```

Voir aussi : [Commandes CLI](Commandes-CLI.md) · [DSL Reference](DSL-Reference.md) ·
[Exemples](Exemples.md).

---

## English

This page is a turnkey path to get started quickly.

### 1. Create a workspace

#### Interactive mode (recommended for beginners)

```bash
jenga workspace DemoWorkspace --interactive
```

Interactive mode asks a series of questions: name, path, configurations
(`Debug, Release`), target OSes, architectures, preferred compiler, C++ dialect,
whether to create an initial project, and whether to enable Unitest.

#### Direct mode

```bash
jenga workspace DemoWorkspace \
  --configs Debug,Release \
  --oses Windows,Linux,macOS \
  --archs x86_64
```

### 2. Add a project

```bash
jenga project DemoApp --kind console --lang C++
```

`--kind` accepts: `console`, `windowed`, `static`, `shared`, `test`.

> Each project is created inside a **folder named after it**, under the
> workspace. With `--location apps`, the project goes to `apps/DemoApp/`.

### 3. Generated structure

```text
DemoWorkspace/
├── DemoWorkspace.jenga      # workspace entry point
└── DemoApp/                 # folder named after the project
    ├── src/
    │   └── main.cpp
    └── include/
```

With multiple projects, each gets its own folder:

```text
DemoWorkspace/
├── DemoWorkspace.jenga
├── DemoApp/                 # jenga project DemoApp
│   └── src/main.cpp
├── Engine/                  # jenga project Engine --kind static
│   ├── src/
│   └── include/
└── apps/
    └── Tool/                # jenga project Tool --location apps
        └── src/main.cpp
```

### 4. Anatomy of a `.jenga` file

A `.jenga` file is **plain Python** enriched with the Jenga DSL:

```python
from Jenga import *

with workspace("DemoWorkspace"):
    configurations(["Debug", "Release"])
    targetoses([TargetOS.WINDOWS, TargetOS.LINUX, TargetOS.MACOS])
    targetarchs([TargetArch.X86_64])
    startproject("DemoApp")

    with project("DemoApp"):
        consoleapp()
        language("C++")
        cppdialect("C++20")
        files(["src/**.cpp", "include/**.hpp"])
        includedirs(["include"])

        # Platform-specific via a filter
        with filter("system:Windows"):
            links(["user32"])
        with filter("config:Debug"):
            defines(["DEBUG_MODE"])
```

> For cross-compilation and automatic toolchain detection, add
> `RegisterJengaGlobalToolchains()` at the top of the workspace (see
> [Toolchains & Sysroots](Toolchains-et-Sysroots.md)).

### 5. Build, run, debug

```bash
jenga build --config Debug
jenga run DemoApp
jenga gdb DemoApp --break main --run    # debug with GDB (or LLDB)
jenga build --config Release --platform Linux-x86_64   # cross-compile
jenga build -j8                                        # 8 parallel jobs
```

### 6. Add content quickly

```bash
jenga file DemoApp --src "src/utils.cpp"   # add sources
jenga file DemoApp --inc include           # add an include dir
jenga file DemoApp --link pthread          # add a library
jenga file DemoApp --def APP_VERSION=1     # add a define
```

See also: [CLI Commands](Commandes-CLI.md) · [DSL Reference](DSL-Reference.md) ·
[Examples](Exemples.md).
