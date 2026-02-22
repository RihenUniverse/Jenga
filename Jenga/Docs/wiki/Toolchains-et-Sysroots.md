# Toolchains et Sysroots

## 1) Gestion rapide des toolchains globales

### Lister

```bash
jenga install toolchain list
```

### Détecter localement et générer la config Python globale

```bash
jenga install toolchain detect
```

### Installer / enregistrer

```bash
jenga install toolchain install zig --version 0.13.0
jenga install toolchain install emsdk --path /opt/emsdk
jenga install toolchain install android-ndk --path /path/to/ndk
```

## 2) Gestion de config globale

```bash
jenga config init
jenga config show
jenga config set max_parallel_jobs 12
jenga config get max_parallel_jobs
```

Toolchains JSON:

```bash
jenga config toolchain add monclang ./toolchain-clang-example.json
jenga config toolchain list
```

Sysroots:

```bash
jenga config sysroot add linux_x64 ./sysroot/linux-x86_64 --os Linux --arch x86_64
jenga config sysroot list
```

## 3) Exemple DSL: toolchain custom Linux

```python
with toolchain("linux_cross", "clang"):
    settarget("Linux", "x86_64", "gnu")
    targettriple("x86_64-unknown-linux-gnu")
    sysroot("E:/Projets/Closed/Jenga/sysroot/linux-x86_64")
    ccompiler("clang")
    cppcompiler("clang++")
    cflags(["--target=x86_64-unknown-linux-gnu"])
    cxxflags(["--target=x86_64-unknown-linux-gnu"])
    ldflags(["--target=x86_64-unknown-linux-gnu"])
```

## 4) Création de sysroot Linux (script)

Le dépôt contient:

- `scripts/setup_linux_sysroot.py`

Exemple:

```bash
python3 scripts/setup_linux_sysroot.py
```

Puis utiliser dans `.jenga`:

```python
sysroot(".../sysroot/linux-x86_64")
includedirs([".../sysroot/linux-x86_64/usr/include"])
libdirs([".../sysroot/linux-x86_64/usr/lib/x86_64-linux-gnu"])
```

## 5) Dépannage express

- `Toolchain not defined`:
  - vérifier que `usetoolchain("nom")` correspond à une toolchain déclarée
- `sysroot headers missing`:
  - vérifier les dossiers `usr/include` et `usr/lib/...` dans le sysroot
