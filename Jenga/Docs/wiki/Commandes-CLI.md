# Commandes CLI / CLI Commands

**Langues / Languages :** [Français](#français) · [English](#english)

---

## Français

Jenga expose **24 commandes**. Syntaxe générale : `jenga <commande> [options]`.
Beaucoup de commandes acceptent un **alias court** (ex. `b` = `build`).

### Flags globaux

- `--version` / `-v` — affiche la version
- `--help` / `-h` — aide générale

### Flags communs (cycle de build)

- `--config CONFIG` — configuration (`Debug`, `Release`…) ; défaut `Debug`
- `--platform PLATFORM` — cible (`Windows`, `Linux-x86_64`, `Android-arm64`…),
  ou `jengaall` pour toutes les plateformes déclarées
- `--target` / `--project` — projet ciblé
- `--no-cache` — ignore le cache incrémental
- `--no-daemon` — n'utilise pas le daemon
- `--verbose` / `-v` — sortie détaillée
- `--jenga-file PATH` — chemin du workspace (sinon auto-détecté)

### Cycle de développement

| Commande | Alias | Rôle | Options clés |
|----------|-------|------|--------------|
| `build` | `b` | Compile le workspace ou un projet | `--config --platform --target --jobs/-j --no-cache --no-daemon`, options Android (`--android-build-system`, `--android-abis`, `--use-android-mk`, `--android-ndk-mk-mode`) |
| `run` | `r` | Exécute un projet (build si besoin) | `project --args --build --target/--device` |
| `gdb` | `g` (`debug`) | Débogue un projet avec GDB (ou LLDB) | `project --config --break/-b --run --batch --args --build --debugger (auto\|gdb\|lldb)` |
| `test` | `t` | Compile et lance les suites de tests | `--project --no-build` |
| `clean` | `c` | Supprime objets/binaires/cache | `--all --config --platform --project` |
| `rebuild` | — | `clean` puis `build` | `--clean-all` + options build |
| `watch` | `w` | Rebuild automatique sur changement | `--polling --no-daemon` |
| `info` | `i` | Workspace, projets, toolchains, daemon | `--verbose` |

```bash
jenga build --config Release --platform Linux-x86_64 --target CoreLib
jenga run MonApp --args --level hard --fullscreen
jenga test --project Core_Tests --config Debug
jenga build -j8                     # 8 jobs parallèles
jenga build --platform jengaall     # toutes les plateformes déclarées
```

#### Débogage avec `gdb`

`jenga gdb` (re)compile en `Debug` si besoin, localise le binaire et lance GDB
(ou LLDB en l'absence de GDB). Détection automatique du debugger.

```bash
jenga gdb                              # débogue le startProject en Debug
jenga gdb MonApp --break main          # breakpoint sur main (répétable avec -b)
jenga gdb MonApp -b fichier.cpp:42 --run   # breakpoint + démarrage immédiat
jenga gdb MonApp --args --level hard   # passe des args au programme débogué
jenga gdb MonApp --debugger lldb       # force LLDB
jenga gdb MonApp --batch               # exécute + backtrace + quitte (CI)
```

### Création & édition

| Commande | Alias | Rôle | Options clés |
|----------|-------|------|--------------|
| `workspace` | `init` | Crée un workspace | `name --path --configs --oses --archs --interactive/-i` |
| `project` | `create` | Crée un projet ou un élément de code | `name --kind --lang --location --element --name --template -i` |
| `file` | `add` | Ajoute sources/includes/libs/defines | `project --src --inc --link --def --type -i` |

```bash
jenga workspace MonJeu --interactive
jenga project Moteur --kind static --lang C++
jenga project Outil --location apps          # -> apps/Outil/
jenga project --element class --name Player --project Moteur
jenga file MonApp --src "src/**.cpp" --inc include --link pthread
```

`--kind` : `console`, `windowed`, `static`, `shared`, `test`.
`--element` : `class`, `struct`, `enum`, `union`, `interface`, `function`,
`source`, `header`, `custom`.

> **Placement des projets** : `jenga project Foo` crée le projet dans un dossier
> **portant son nom** sous le workspace (`<workspace>/Foo/`). Avec
> `--location apps`, le projet est placé dans `<workspace>/apps/Foo/`. Le DSL
> généré renseigne `location("Foo")` (ou `location("apps/Foo")`).

### Génération IDE & documentation

| Commande | Alias | Rôle | Options clés |
|----------|-------|------|--------------|
| `gen` | — | Génère fichiers projet IDE | `--cmake --makefile --mk --android-mk --vs2022 --xcode --all --output/-o` |
| `docs` | `d` | Génère la doc (Doxygen → MD/HTML/PDF) | selon projet |
| `ide-setup` | `ide` | Configure l'éditeur pour `.jenga` | `--editor (auto\|vscode\|lsp\|all) --force --info` |

```bash
jenga gen --cmake --vs2022 --output generated
jenga ide-setup --editor vscode
```

### Packaging, déploiement, signature

| Commande | Rôle | Options clés |
|----------|------|--------------|
| `package` | Crée un package distribuable | `--platform (requis) --type --config --output/-o --project --ios-builder` |
| `deploy` | Déploie sur un appareil | `--platform (requis) --target/--device --apk --hap --list-devices --uninstall --run` |
| `sign` | Signe un APK/IPA | `--apk --ipa --keystore --alias --storepass --keypass --project` |
| `keygen` | Génère une keystore | `--alias --validity --output/-o -i --harmony` |
| `publish` | Publie sur un registre | `--registry (requis) --package --version --api-key --repo --dry-run` |

```bash
jenga package --platform windows --type msi --project MonApp -o ./dist
jenga package --platform android --type apk --project MonApp
jenga deploy --platform android --target emulator-5554 --run
jenga keygen --interactive
jenga sign --apk app.apk --keystore my.jks --alias key --storepass xxx --keypass xxx
```

> Types par plateforme : Android `apk`/`aab`, iOS `ipa`, Windows `msi`/`exe`/`zip`,
> Linux `deb`/`rpm`/`appimage`/`snap`, macOS `pkg`/`dmg`, Web `zip`, HarmonyOS `hap`.

### Outillage & analyse

| Commande | Rôle | Options clés |
|----------|------|--------------|
| `bench` | Lance des benchmarks | `--project --iterations --output/-o` |
| `profile` | Profilage CPU/mémoire | `--platform (requis) --tool --duration --output/-o` |
| `install` | Dépendances / toolchains globales | sous-commandes `toolchain list\|detect\|install` |
| `config` | Configuration globale Jenga | `init\|show\|set\|get`, `toolchain …`, `sysroot …` |
| `examples` | Liste/copie les exemples | sous-commandes `list\|copy` |
| `help` | Aide générale ou d'une commande | `command` |

```bash
jenga install toolchain list
jenga install toolchain install android-ndk --path /path/to/ndk
jenga config set max_parallel_jobs 12
jenga bench --project BenchApp --iterations 20
jenga help build
```

### Liste des alias

`b`=build · `r`=run · `t`=test · `c`=clean · `w`=watch · `i`=info · `e`=examples ·
`d`=docs · `k`=keygen · `s`=sign · `h`=help · `init`=workspace · `create`=project ·
`add`=file · `ide`=ide-setup.

---

## English

Jenga exposes **24 commands**. General syntax: `jenga <command> [options]`.
Many commands accept a **short alias** (e.g. `b` = `build`).

### Global flags

- `--version` / `-v` — print version
- `--help` / `-h` — general help

### Common flags (build cycle)

- `--config CONFIG` — configuration (`Debug`, `Release`…); default `Debug`
- `--platform PLATFORM` — target (`Windows`, `Linux-x86_64`, `Android-arm64`…),
  or `jengaall` for every declared platform
- `--target` / `--project` — targeted project
- `--no-cache` — ignore the incremental cache
- `--no-daemon` — do not use the daemon
- `--verbose` / `-v` — verbose output
- `--jenga-file PATH` — workspace path (otherwise auto-detected)

### Development cycle

| Command | Alias | Purpose | Key options |
|---------|-------|---------|-------------|
| `build` | `b` | Compile workspace or a project | `--config --platform --target --jobs/-j --no-cache --no-daemon`, Android options (`--android-build-system`, `--android-abis`, `--use-android-mk`, `--android-ndk-mk-mode`) |
| `run` | `r` | Run a project (build if needed) | `project --args --build --target/--device` |
| `gdb` | `g` (`debug`) | Debug a project with GDB (or LLDB) | `project --config --break/-b --run --batch --args --build --debugger (auto\|gdb\|lldb)` |
| `test` | `t` | Build and run test suites | `--project --no-build` |
| `clean` | `c` | Remove objects/binaries/cache | `--all --config --platform --project` |
| `rebuild` | — | `clean` then `build` | `--clean-all` + build options |
| `watch` | `w` | Auto-rebuild on change | `--polling --no-daemon` |
| `info` | `i` | Workspace, projects, toolchains, daemon | `--verbose` |

```bash
jenga build --config Release --platform Linux-x86_64 --target CoreLib
jenga run MyApp --args --level hard --fullscreen
jenga test --project Core_Tests --config Debug
jenga build -j8                     # 8 parallel jobs
jenga build --platform jengaall     # every declared platform
```

#### Debugging with `gdb`

`jenga gdb` (re)builds in `Debug` if needed, locates the binary and launches GDB
(or LLDB when GDB is missing). The debugger is auto-detected.

```bash
jenga gdb                              # debug the startProject in Debug
jenga gdb MyApp --break main           # breakpoint on main (repeatable with -b)
jenga gdb MyApp -b file.cpp:42 --run   # breakpoint + start immediately
jenga gdb MyApp --args --level hard    # pass args to the debugged program
jenga gdb MyApp --debugger lldb        # force LLDB
jenga gdb MyApp --batch                # run + backtrace + quit (CI)
```

### Creation & editing

| Command | Alias | Purpose | Key options |
|---------|-------|---------|-------------|
| `workspace` | `init` | Create a workspace | `name --path --configs --oses --archs --interactive/-i` |
| `project` | `create` | Create a project or code element | `name --kind --lang --location --element --name --template -i` |
| `file` | `add` | Add sources/includes/libs/defines | `project --src --inc --link --def --type -i` |

```bash
jenga workspace MyGame --interactive
jenga project Engine --kind static --lang C++
jenga project Tool --location apps           # -> apps/Tool/
jenga project --element class --name Player --project Engine
jenga file MyApp --src "src/**.cpp" --inc include --link pthread
```

`--kind`: `console`, `windowed`, `static`, `shared`, `test`.
`--element`: `class`, `struct`, `enum`, `union`, `interface`, `function`,
`source`, `header`, `custom`.

> **Project placement**: `jenga project Foo` creates the project inside a folder
> **named after it** under the workspace (`<workspace>/Foo/`). With
> `--location apps`, the project goes to `<workspace>/apps/Foo/`. The generated
> DSL sets `location("Foo")` (or `location("apps/Foo")`).

### IDE generation & documentation

| Command | Alias | Purpose | Key options |
|---------|-------|---------|-------------|
| `gen` | — | Generate IDE project files | `--cmake --makefile --mk --android-mk --vs2022 --xcode --all --output/-o` |
| `docs` | `d` | Generate docs (Doxygen → MD/HTML/PDF) | project-dependent |
| `ide-setup` | `ide` | Configure editor for `.jenga` | `--editor (auto\|vscode\|lsp\|all) --force --info` |

```bash
jenga gen --cmake --vs2022 --output generated
jenga ide-setup --editor vscode
```

### Packaging, deployment, signing

| Command | Purpose | Key options |
|---------|---------|-------------|
| `package` | Create a distributable package | `--platform (required) --type --config --output/-o --project --ios-builder` |
| `deploy` | Deploy to a device | `--platform (required) --target/--device --apk --hap --list-devices --uninstall --run` |
| `sign` | Sign an APK/IPA | `--apk --ipa --keystore --alias --storepass --keypass --project` |
| `keygen` | Generate a keystore | `--alias --validity --output/-o -i --harmony` |
| `publish` | Publish to a registry | `--registry (required) --package --version --api-key --repo --dry-run` |

```bash
jenga package --platform windows --type msi --project MyApp -o ./dist
jenga package --platform android --type apk --project MyApp
jenga deploy --platform android --target emulator-5554 --run
jenga keygen --interactive
jenga sign --apk app.apk --keystore my.jks --alias key --storepass xxx --keypass xxx
```

> Types per platform: Android `apk`/`aab`, iOS `ipa`, Windows `msi`/`exe`/`zip`,
> Linux `deb`/`rpm`/`appimage`/`snap`, macOS `pkg`/`dmg`, Web `zip`, HarmonyOS `hap`.

### Tooling & analysis

| Command | Purpose | Key options |
|---------|---------|-------------|
| `bench` | Run benchmarks | `--project --iterations --output/-o` |
| `profile` | CPU/memory profiling | `--platform (required) --tool --duration --output/-o` |
| `install` | Dependencies / global toolchains | subcommands `toolchain list\|detect\|install` |
| `config` | Global Jenga configuration | `init\|show\|set\|get`, `toolchain …`, `sysroot …` |
| `examples` | List/copy examples | subcommands `list\|copy` |
| `help` | General or per-command help | `command` |

```bash
jenga install toolchain list
jenga install toolchain install android-ndk --path /path/to/ndk
jenga config set max_parallel_jobs 12
jenga bench --project BenchApp --iterations 20
jenga help build
```

### Alias list

`b`=build · `r`=run · `t`=test · `c`=clean · `w`=watch · `i`=info · `e`=examples ·
`d`=docs · `k`=keygen · `s`=sign · `h`=help · `init`=workspace · `create`=project ·
`add`=file · `ide`=ide-setup.
