# Templates toolchains par plateforme (basé sur GUIDE_ZIG_MULTIPLATFORM.md, cross-compilation-guide.md, recapitulatif-cross-compilation.md, android.md)

## Zig multi-cibles
```python
with toolchain("zig_windows", "clang"):
    settarget("Windows", "x86_64", "mingw")
    ccompiler("zig")
    cppcompiler("zig")
    linker("zig")
    cflags(["cc", "-target", "x86_64-windows-gnu"])
    cxxflags(["c++", "-target", "x86_64-windows-gnu"])

with toolchain("zig_linux", "clang"):
    settarget("Linux", "x86_64", "gnu")
    ccompiler("zig")
    cppcompiler("zig")
    linker("zig")
    cflags(["cc", "-target", "x86_64-linux-gnu"])
    cxxflags(["c++", "-target", "x86_64-linux-gnu"])

with toolchain("zig_android_arm64", "clang"):
    settarget("Android", "arm64", "android")
    ccompiler("zig")
    cppcompiler("zig")
    linker("zig")
    cflags(["cc", "-target", "aarch64-linux-android21"])
    cxxflags(["c++", "-target", "aarch64-linux-android21"])
```

## Emscripten (Web)
```python
with toolchain("emscripten", "emscripten"):
    settarget("Web", "wasm32")
    ccompiler("emcc")
    cppcompiler("em++")
    linker("em++")
    archiver("emar")
```

## Android NDK + APK sans Android Studio
```python
with workspace("AndroidDemo"):
    targetoses([TargetOS.ANDROID])
    targetarchs([TargetArch.ARM64])
    androidsdkpath(r"C:/Android/sdk")
    androidndkpath(r"C:/Android/sdk/ndk/27.0.12077973")

    with project("NativeApp"):
        windowedapp()   # ou consoleapp()
        files(["src/**.cpp"])
        androidapplicationid("com.demo.native")
        androidminsdk(24)
        androidtargetsdk(34)
        androidnativeactivity(True)
```

## HarmonyOS
```python
with toolchain("harmony_arm64", "clang"):
    settarget("HarmonyOS", "arm64")
    targettriple("aarch64-linux-ohos")
    ccompiler("<HARMONY_SDK>/native/llvm/bin/clang")
    cppcompiler("<HARMONY_SDK>/native/llvm/bin/clang++")
    archiver("<HARMONY_SDK>/native/llvm/bin/llvm-ar")
```

## Xbox
```python
with toolchain("xbox_gdk", "msvc"):
    settarget("XboxOne", "x86_64") # ou XboxSeries
    ccompiler("cl.exe")
    cppcompiler("cl.exe")
    linker("link.exe")
    archiver("lib.exe")
```

## macOS/iOS (macOS requis)
```python
with toolchain("apple_clang", "apple-clang"):
    settarget("macOS", "arm64")
    ccompiler("clang")
    cppcompiler("clang++")

with toolchain("apple_ios", "apple-clang"):
    settarget("iOS", "arm64", "ios")
    ccompiler("clang")
    cppcompiler("clang++")
```

## PS3 / PS4 / PS5 (snippets SDK propriétaires)
```python
with toolchain("ps3_sdk", "clang"):
    settarget("PS3", "ppc64")
    targettriple("powerpc64-scei-ps3")

with toolchain("ps4_sdk", "clang"):
    settarget("PS4", "x86_64")
    targettriple("x86_64-scei-ps4")

with toolchain("ps5_sdk", "clang"):
    settarget("PS5", "x86_64")
    targettriple("x86_64-scei-ps5")
```
