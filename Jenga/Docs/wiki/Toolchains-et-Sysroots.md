# Toolchains et Sysroots / Toolchains & Sysroots

**Langues / Languages :** [Français](#français) · [English](#english)

---

## Français

### 1. Détection automatique

Appelez `RegisterJengaGlobalToolchains()` au début du workspace pour détecter
automatiquement les toolchains installées. Jenga reconnaît jusqu'à **11
toolchains** selon l'environnement :

| Toolchain | Déclencheur | Compilateur | Cible |
|-----------|-------------|-------------|-------|
| `host-apple-clang` | `clang` Apple | clang/clang++ | macOS (hôte) |
| `host-clang` | `clang` non-Apple | clang/clang++ | hôte |
| `host-gcc` | `gcc` | gcc/g++ | hôte |
| `msvc` | Windows + `cl.exe` | cl.exe (MSVC 2019+) | Windows x64/x86 |
| `clang-mingw` | Clang + MSYS2/UCRT | clang/clang++ | Windows MinGW |
| `mingw` | `x86_64-w64-mingw32-gcc` | gcc/g++ | Windows MinGW |
| `gcc-cross-linux` | `x86_64-linux-gnu-gcc` | gcc cross | Linux x86_64 |
| `clang-cross-linux` | clang + triple | clang cross | Linux x86_64 |
| `emscripten` | `emcc` ou `$EMSDK` | emcc/em++ | Web/wasm32 |
| `android-ndk` | `$ANDROID_NDK_ROOT` | clang NDK | Android arm64 |
| `zig-*` (6 variantes) | `zig` ou `$ZIG_ROOT` | zig cc/c++ | Linux/Windows/macOS/Android/Web |
| `ohos-ndk` | `$OHOS_SDK` | clang OHOS | HarmonyOS arm64 |

Variables d'environnement principales :

| Variable | Toolchain |
|----------|-----------|
| `ANDROID_NDK_ROOT` / `ANDROID_SDK_ROOT` | `android-ndk` |
| `EMSDK` | `emscripten` |
| `CLANG_BASE` | `clang-native`, `clang-cross-linux` |
| `MINGW_ROOT` | `clang-mingw`, `mingw` |
| `ZIG_ROOT` | `zig-*` |
| `OHOS_SDK` / `HARMONY_OS_SDK` | `ohos-ndk` (HarmonyOS) |

### 2. Matrice hôte → cible

| Hôte ↓ \ Cible → | Windows | Linux | macOS | Android | iOS | Xbox | HarmonyOS | Web |
|------------------|:-------:|:-----:|:-----:|:-------:|:---:|:----:|:---------:|:---:|
| **Windows** | ✅ MSVC | ✅ MinGW/Zig | ❌ | ✅ NDK | ❌ | ✅ GDK | ✅ | ✅ |
| **Linux** | ✅ MinGW/Zig | ✅ GCC/Clang | ❌ | ✅ NDK | ❌ | ❌ | ✅ | ✅ |
| **macOS** | ❌ | ✅ (Zig) | ✅ Apple Clang | ✅ NDK | ✅ Xcode | ❌ | ✅ | ✅ |

Contraintes : iOS/macOS exigent un hôte macOS + Xcode ; Xbox exige Windows + GDK.

### 3. Gestion rapide (CLI)

```bash
jenga install toolchain list                       # lister
jenga install toolchain detect                     # détecter + régénérer la config
jenga install toolchain install zig --version 0.13.0
jenga install toolchain install emsdk --path /opt/emsdk
jenga install toolchain install android-ndk --path /path/to/ndk
```

### 4. Toolchain personnalisée (DSL)

```python
with toolchain("linux_cross", "clang"):
    settarget("Linux", "x86_64", "gnu")
    targettriple("x86_64-unknown-linux-gnu")
    sysroot("/chemin/sysroot/linux-x86_64")
    ccompiler("clang")
    cppcompiler("clang++")
    cflags(["--target=x86_64-unknown-linux-gnu"])
    cxxflags(["--target=x86_64-unknown-linux-gnu"])
    ldflags(["--target=x86_64-unknown-linux-gnu"])

# puis dans le projet :
usetoolchain("linux_cross")
```

### 5. Toolchain personnalisée (config globale JSON)

```bash
jenga config toolchain add monclang ./toolchain-clang.json
jenga config toolchain list
```

Format JSON attendu :

```json
{
  "name": "my-custom-toolchain",
  "compilerFamily": "clang",
  "targetOs": "Linux",
  "targetArch": "arm64",
  "targetEnv": "gnu",
  "targetTriple": "aarch64-linux-gnu",
  "sysroot": "/path/to/sysroot",
  "ccPath": "/path/to/cc",
  "cxxPath": "/path/to/c++",
  "arPath": "/path/to/ar",
  "ldPath": "/path/to/ld",
  "cflags": ["--flag1"],
  "cxxflags": ["--flag2"],
  "ldflags": ["--flag3"]
}
```

### 6. Sysroots (cross-compilation)

```bash
# Script fourni pour générer un sysroot Linux
python scripts/setup_linux_sysroot.py

# Enregistrement persistant
jenga config sysroot add linux_x64 ./sysroot/linux-x86_64 --os Linux --arch x86_64
jenga config sysroot list
```

Utilisation dans `.jenga` :

```python
sysroot(".../sysroot/linux-x86_64")
includedirs([".../sysroot/linux-x86_64/usr/include"])
libdirs([".../sysroot/linux-x86_64/usr/lib/x86_64-linux-gnu"])
```

### 7. Zig comme cross-compilateur

Zig fournit 6 toolchains automatiques : `zig-linux-x86_64`,
`zig-windows-x86_64`, `zig-macos-x86_64`, `zig-macos-arm64`,
`zig-android-arm64`, `zig-web-wasm32`. Détecté via `$ZIG_ROOT` ou les wrappers
`zig-cc` / `zig-c++`. Voir l'exemple `21_zig_cross_compile`.

### 8. Dépannage

- `Toolchain not defined` → vérifier que `usetoolchain("nom")` correspond à une
  toolchain déclarée ou détectée.
- `sysroot headers missing` → vérifier `usr/include` et `usr/lib/...`.
- Toolchain non détectée → vérifier les variables d'environnement (section 1).

---

## English

### 1. Automatic detection

Call `RegisterJengaGlobalToolchains()` at the start of the workspace to
auto-detect installed toolchains. Jenga recognizes up to **11 toolchains**
depending on the environment (host-apple-clang, host-clang, host-gcc, msvc,
clang-mingw, mingw, gcc-cross-linux, clang-cross-linux, emscripten, android-ndk,
zig-* and ohos-ndk).

Main environment variables:

| Variable | Toolchain |
|----------|-----------|
| `ANDROID_NDK_ROOT` / `ANDROID_SDK_ROOT` | `android-ndk` |
| `EMSDK` | `emscripten` |
| `CLANG_BASE` | `clang-native`, `clang-cross-linux` |
| `MINGW_ROOT` | `clang-mingw`, `mingw` |
| `ZIG_ROOT` | `zig-*` |
| `OHOS_SDK` / `HARMONY_OS_SDK` | `ohos-ndk` (HarmonyOS) |

### 2. Host → target matrix

| Host ↓ \ Target → | Windows | Linux | macOS | Android | iOS | Xbox | HarmonyOS | Web |
|-------------------|:-------:|:-----:|:-----:|:-------:|:---:|:----:|:---------:|:---:|
| **Windows** | ✅ MSVC | ✅ MinGW/Zig | ❌ | ✅ NDK | ❌ | ✅ GDK | ✅ | ✅ |
| **Linux** | ✅ MinGW/Zig | ✅ GCC/Clang | ❌ | ✅ NDK | ❌ | ❌ | ✅ | ✅ |
| **macOS** | ❌ | ✅ (Zig) | ✅ Apple Clang | ✅ NDK | ✅ Xcode | ❌ | ✅ | ✅ |

Constraints: iOS/macOS require a macOS host + Xcode; Xbox requires Windows + GDK.

### 3. Quick management (CLI)

```bash
jenga install toolchain list
jenga install toolchain detect
jenga install toolchain install zig --version 0.13.0
jenga install toolchain install emsdk --path /opt/emsdk
jenga install toolchain install android-ndk --path /path/to/ndk
```

### 4. Custom toolchain (DSL)

```python
with toolchain("linux_cross", "clang"):
    settarget("Linux", "x86_64", "gnu")
    targettriple("x86_64-unknown-linux-gnu")
    sysroot("/path/sysroot/linux-x86_64")
    ccompiler("clang"); cppcompiler("clang++")
    cflags(["--target=x86_64-unknown-linux-gnu"])
    cxxflags(["--target=x86_64-unknown-linux-gnu"])
    ldflags(["--target=x86_64-unknown-linux-gnu"])

usetoolchain("linux_cross")
```

### 5. Custom toolchain (global JSON config)

```bash
jenga config toolchain add myclang ./toolchain-clang.json
jenga config toolchain list
```

Expected JSON: `name`, `compilerFamily`, `targetOs`, `targetArch`, `targetEnv`,
`targetTriple`, `sysroot`, `ccPath`, `cxxPath`, `arPath`, `ldPath`, `cflags`,
`cxxflags`, `ldflags` (see the French section for a full sample).

### 6. Sysroots (cross-compilation)

```bash
python scripts/setup_linux_sysroot.py
jenga config sysroot add linux_x64 ./sysroot/linux-x86_64 --os Linux --arch x86_64
jenga config sysroot list
```

```python
sysroot(".../sysroot/linux-x86_64")
includedirs([".../sysroot/linux-x86_64/usr/include"])
libdirs([".../sysroot/linux-x86_64/usr/lib/x86_64-linux-gnu"])
```

### 7. Zig as a cross-compiler

Zig provides 6 automatic toolchains (`zig-linux-x86_64`, `zig-windows-x86_64`,
`zig-macos-x86_64`, `zig-macos-arm64`, `zig-android-arm64`, `zig-web-wasm32`).
Detected via `$ZIG_ROOT` or the `zig-cc`/`zig-c++` wrappers. See example
`21_zig_cross_compile`.

### 8. Troubleshooting

- `Toolchain not defined` → ensure `usetoolchain("name")` matches a declared or
  detected toolchain.
- `sysroot headers missing` → check `usr/include` and `usr/lib/...`.
- Toolchain not detected → check the environment variables (section 1).
