# Installation

## Prérequis

- Python 3.8+
- Un compilateur adapté à ta plateforme:
  - Windows: MSVC, Clang, MinGW, Zig
  - Linux: GCC/Clang
  - macOS: Xcode/Apple Clang

## Installation depuis le code source

Dans la racine du dépôt:

```bash
pip install -e .
```

## Vérifier que Jenga fonctionne

```bash
python3 Jenga/jenga.py --version
```

Selon ta plateforme:

```bash
# Linux/macOS
bash ./jenga.sh --help

# Windows
jenga.bat --help
```

## Erreurs courantes

### `No .jenga workspace file found`

Tu lances une commande build/run/test dans un dossier qui n'a pas encore de workspace.

Solution:

```bash
jenga workspace MonWorkspace
```

### `keytool not found` (signature Android)

Le JDK n'est pas installé ou pas dans le `PATH`.

Solution:

- installer Java JDK
- vérifier:

```bash
keytool -help
```
