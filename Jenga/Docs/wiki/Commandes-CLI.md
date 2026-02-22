# Commandes CLI

## Cycle principal

```bash
jenga build   --config Debug --platform Windows
jenga run     MonApp --config Debug
jenga test    --config Debug
jenga clean   --all
jenga rebuild --config Release
jenga watch   --config Debug
```

## Détails utiles

### `jenga build`

- compile workspace complet ou projet ciblé
- options clés:
  - `--config`
  - `--platform`
  - `--target`
  - `--no-cache`
  - `--no-daemon`

Exemple:

```bash
jenga build --config Release --platform Linux --target CoreLib
```

### `jenga run`

- exécute le projet demandé
- utilise `startproject` si aucun projet n'est fourni

Exemple:

```bash
jenga run MonApp --args --level hard --fullscreen
```

### `jenga test`

- build puis exécute les projets de test
- options:
  - `--project`
  - `--no-build`

Exemple:

```bash
jenga test --project Core_Tests --config Debug
```

### `jenga info`

- affiche workspace, projets, toolchains détectées, statut daemon

```bash
jenga info --verbose
```

### `jenga gen`

- génère des fichiers externes:
  - `--cmake`
  - `--makefile`
  - `--vs2022`
  - `--xcode`

```bash
jenga gen --cmake --output generated
```

## Aliases courts

- `b` -> `build`
- `r` -> `run`
- `t` -> `test`
- `c` -> `clean`
- `w` -> `watch`
- `i` -> `info`
- `e` -> `examples`
- `d` -> `docs`
- `k` -> `keygen`
- `s` -> `sign`

## Commandes d'aide

```bash
jenga help
jenga help build
```
