# FAQ / Dépannage

## `No .jenga workspace file found`

Tu exécutes une commande dans un dossier sans fichier workspace.

Solution:

```bash
jenga workspace MonWorkspace
```

Ou préciser un fichier:

```bash
jenga build --jenga-file ./MonWorkspace.jenga
```

## `Project 'X' not found`

Le nom du projet n'existe pas dans le workspace chargé.

Vérifier:

- le nom exact dans le `.jenga`
- le bon fichier workspace

## `Toolchain 'X' not defined`

Tu appelles `usetoolchain("X")` sans l'avoir déclaré.

Solution:

- déclarer un bloc `with toolchain("X", "..."):` dans le workspace
- ou charger une toolchain globale via `jenga install toolchain ...`

## Build lent ou incohérent

Essayer:

```bash
jenga clean --all
jenga build --no-cache --no-daemon --verbose
```

## Erreur Android SDK / NDK introuvable

Vérifier:

- variables d'environnement (`ANDROID_SDK_ROOT`, `ANDROID_NDK_ROOT`)
- ou configuration DSL:

```python
androidsdkpath("...")
androidndkpath("...")
```

## Tests qui ne se lancent pas

Vérifier:

- présence du bloc `unitest()`
- présence du bloc `test()` dans un `project()`
- existence des fichiers listés dans `testfiles([...])`

## Génération docs vide

Vérifier:

- présence de commentaires Doxygen / `///`
- sources dans `src/` et `include/`
- commande:

```bash
jenga docs extract --verbose
```
