# Toolchains conseillées par exemple

Ce fichier donne une toolchain recommandée pour chaque exemple.

- `01_hello_console`: `host-clang` (Linux/macOS) ou `clang-cl`/`mingw` (Windows)
- `02_static_library`: `host-clang` / `host-gcc`
- `03_shared_library`: `host-clang` / `host-gcc`
- `04_unit_tests`: `host-clang` (retirer flags MSVC sur Linux)
- `05_android_ndk`: `android-ndk` (Target: `Android-arm64`)
- `06_ios_app`: `host-apple-clang` (macOS uniquement)
- `07_web_wasm`: `emscripten` (`emcc`/`em++`)
- `08_custom_toolchain`: toolchain du projet (`custom_clang`)
- `09_multi_projects`: `host-clang` / `host-gcc`
- `10_modules_cpp20`: `host-clang` récent (modules C++20)
- `11_benchmark`: `host-clang` / `host-gcc`
- `12_external_includes`: `host-clang` / `host-gcc`
- `13_packaging`: `host-clang` / `host-gcc`
- `14_cross_compile`: `linux_cross` (clang `--target=x86_64-unknown-linux-gnu`) ou `zig-linux-x86_64`
- `15_window_win32`: `clang-cl` ou `msvc` (Windows SDK requis)
- `16_window_x11_linux`: `host-clang` / `host-gcc` (+ libs X11)
- `17_window_macos_cocoa`: `host-apple-clang` (macOS)
- `18_window_android_native`: `android-ndk`
- `19_window_web_canvas`: `emscripten`
- `20_window_ios_uikit`: `host-apple-clang` (macOS)
- `21_zig_cross_compile`: `zig-linux-x86_64` (ou toolchain Zig equivalente)
- `22_nk_multiplatform_sandbox`: `clang-mingw` (Windows) / `host-clang` (Linux/macOS)
- `23_android_sdl3_ndk_mk`: `android-ndk` (mode natif) ou `android-ndk` + `ndk-build` (mode `--android-build-system ndk-mk`)

## Snippets cibles consoles

### HarmonyOS
```python
with toolchain("harmony_arm64", "clang"):
    settarget("HarmonyOS", "arm64")
    targettriple("aarch64-linux-ohos")
    ccompiler("<HARMONY_SDK>/native/llvm/bin/clang")
    cppcompiler("<HARMONY_SDK>/native/llvm/bin/clang++")
    archiver("<HARMONY_SDK>/native/llvm/bin/llvm-ar")
    sysroot("<HARMONY_SDK>/native/sysroot")
    cflags(["--target=aarch64-linux-ohos"])
    cxxflags(["--target=aarch64-linux-ohos"])
```

### Xbox One / Series (GDK)
```python
with toolchain("xbox_gdk", "msvc"):
    settarget("XboxOne", "x86_64")  # ou XboxSeries
    ccompiler("cl.exe")
    cppcompiler("cl.exe")
    linker("link.exe")
    archiver("lib.exe")
    # GDK env: GameDK, GXDKEDITION/GRDKEDITION
```

### PS3 / PS4 / PS5 (snippets de configuration)
```python
# PS3 (SDK propriétaire)
with toolchain("ps3_sdk", "clang"):
    settarget("PS3", "ppc64")
    targettriple("powerpc64-scei-ps3")
    ccompiler("<PS3_SDK>/host/bin/ppu-lv2-gcc")
    cppcompiler("<PS3_SDK>/host/bin/ppu-lv2-g++")

# PS4
with toolchain("ps4_sdk", "clang"):
    settarget("PS4", "x86_64")
    targettriple("x86_64-scei-ps4")
    ccompiler("<ORBIS_SDK>/host_tools/bin/clang")
    cppcompiler("<ORBIS_SDK>/host_tools/bin/clang++")

# PS5
with toolchain("ps5_sdk", "clang"):
    settarget("PS5", "x86_64")
    targettriple("x86_64-scei-ps5")
    ccompiler("<PROSPERO_SDK>/host_tools/bin/clang")
    cppcompiler("<PROSPERO_SDK>/host_tools/bin/clang++")
```

Notes:
- PS3/PS4/PS5 nécessitent SDK propriétaires Sony et licences.
- Les chemins exacts dépendent de votre installation SDK.
