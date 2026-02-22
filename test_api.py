#!/usr/bin/env python3
"""
Comprehensive test suite for Jenga Core API.
Tests all user-facing DSL functions.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from Jenga import *
from Jenga.Core.Api import (
    _currentWorkspace, _currentProject, _currentFilter,
    ProjectKind, Language, Optimization, WarningLevel,
    TargetOS, TargetArch, TargetEnv, CompilerFamily,
    Workspace, Project, Toolchain, UnitestConfig,
)
from Jenga.Core.Api import test as jenga_test
import Jenga.Core.Api as Api

passed = 0
failed = 0
errors = []

def check(name, condition, detail=""):
    global passed, failed, errors
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        msg = f"  [FAIL] {name}" + (f" — {detail}" if detail else "")
        print(msg)
        errors.append(msg)

def reset_state():
    Api._currentWorkspace = None
    Api._currentProject = None
    Api._currentToolchain = None
    Api._currentFilter = None

# ============================================================================
# 1. ENUMS
# ============================================================================
print("\n=== 1. Enums ===")

check("ProjectKind values", len(ProjectKind) == 5)
check("ProjectKind.CONSOLE_APP", ProjectKind.CONSOLE_APP.value == "ConsoleApp")
check("ProjectKind.WINDOWED_APP", ProjectKind.WINDOWED_APP.value == "WindowedApp")
check("ProjectKind.STATIC_LIB", ProjectKind.STATIC_LIB.value == "StaticLib")
check("ProjectKind.SHARED_LIB", ProjectKind.SHARED_LIB.value == "SharedLib")
check("ProjectKind.TEST_SUITE", ProjectKind.TEST_SUITE.value == "TestSuite")

check("Language values", len(Language) == 7)
check("Language.CPP", Language.CPP.value == "C++")
check("Language.RUST", Language.RUST.value == "Rust")
check("Language.ZIG", Language.ZIG.value == "Zig")

check("Optimization values", len(Optimization) == 4)
check("WarningLevel values", len(WarningLevel) == 7)

check("TargetOS count", len(TargetOS) >= 14)
check("TargetOS.WINDOWS", TargetOS.WINDOWS.value == "Windows")
check("TargetOS.ANDROID", TargetOS.ANDROID.value == "Android")
check("TargetOS.WEB", TargetOS.WEB.value == "Web")
check("TargetOS.HARMONYOS", TargetOS.HARMONYOS.value == "HarmonyOS")

check("TargetArch count", len(TargetArch) >= 10)
check("TargetArch.ARM64", TargetArch.ARM64.value == "arm64")
check("TargetArch.WASM32", TargetArch.WASM32.value == "wasm32")

check("TargetEnv values", len(TargetEnv) >= 6)
check("CompilerFamily values", len(CompilerFamily) >= 6)

# ============================================================================
# 2. WORKSPACE context manager
# ============================================================================
print("\n=== 2. Workspace ===")
reset_state()

with workspace("TestWorkspace") as wks:
    check("workspace created", wks is not None)
    check("workspace name", wks.name == "TestWorkspace")
    check("workspace default configs", wks.configurations == ["Debug", "Release"])
    check("workspace type", isinstance(wks, Workspace))

    configurations(["Debug", "Release", "Profile"])
    check("configurations()", wks.configurations == ["Debug", "Release", "Profile"])

    targetoses([TargetOS.WINDOWS, TargetOS.LINUX, TargetOS.ANDROID])
    check("targetoses()", len(wks.targetOses) == 3)
    check("targetoses() contains ANDROID", TargetOS.ANDROID in wks.targetOses)

    targetarchs([TargetArch.X86_64, TargetArch.ARM64])
    check("targetarchs()", len(wks.targetArchs) == 2)

    platforms(["Windows", "Linux"])
    check("platforms()", wks.platforms == ["Windows", "Linux"])

    androidsdkpath("/fake/sdk")
    check("androidsdkpath()", wks.androidSdkPath == "/fake/sdk")
    androidndkpath("/fake/ndk")
    check("androidndkpath()", wks.androidNdkPath == "/fake/ndk")

    # ========================================================================
    # 3. PROJECT context manager
    # ========================================================================
    print("\n=== 3. Project ===")

    with project("MyApp") as prj:
        check("project created", prj is not None)
        check("project name", prj.name == "MyApp")
        check("project in workspace", "MyApp" in wks.projects)

        consoleapp()
        check("consoleapp()", prj.kind == ProjectKind.CONSOLE_APP)
        windowedapp()
        check("windowedapp()", prj.kind == ProjectKind.WINDOWED_APP)
        staticlib()
        check("staticlib()", prj.kind == ProjectKind.STATIC_LIB)
        sharedlib()
        check("sharedlib()", prj.kind == ProjectKind.SHARED_LIB)
        consoleapp()

        language("C++")
        check("language('C++')", prj.language == Language.CPP)
        language("C")
        check("language('C')", prj.language == Language.C)
        language("C++")

        cppdialect("C++20")
        check("cppdialect('C++20')", prj.cppdialect == "C++20")
        cdialect("C17")
        check("cdialect('C17')", prj.cdialect == "C17")

        files(["src/**.cpp", "src/**.h"])
        check("files()", len(prj.files) == 2)
        check("files() content", "src/**.cpp" in prj.files)

        excludefiles(["src/generated/**"])
        check("excludefiles()", "src/generated/**" in prj.excludeFiles)

        includedirs(["include", "third_party/include"])
        check("includedirs()", len(prj.includeDirs) == 2)

        libdirs(["lib", "third_party/lib"])
        check("libdirs()", len(prj.libDirs) == 2)

        objdir("Build/Obj/%{cfg.buildcfg}")
        check("objdir()", prj.objDir == "Build/Obj/%{cfg.buildcfg}")

        targetdir("Build/Bin/%{cfg.buildcfg}")
        check("targetdir()", prj.targetDir == "Build/Bin/%{cfg.buildcfg}")

        targetname("myapp")
        check("targetname()", prj.targetName == "myapp")

        links(["pthread", "dl"])
        check("links()", len(prj.links) == 2)

        dependson(["LibA", "LibB"])
        check("dependson()", len(prj.dependsOn) == 2)

        defines(["DEBUG", "VERSION=2"])
        check("defines()", "DEBUG" in prj.defines and "VERSION=2" in prj.defines)

        optimize("Speed")
        check("optimize('Speed')", prj.optimize == Optimization.SPEED)
        optimize("Size")
        check("optimize('Size')", prj.optimize == Optimization.SIZE)

        symbols(True)
        check("symbols(True)", prj.symbols == True)
        symbols(False)
        check("symbols(False)", prj.symbols == False)

        warnings("Extra")
        check("warnings('Extra')", prj.warnings == WarningLevel.EXTRA)

        cflags(["-Wall"])
        check("cflags()", "-Wall" in prj.cflags)
        cxxflags(["-std=c++20", "-fno-rtti"])
        check("cxxflags()", "-std=c++20" in prj.cxxflags)
        ldflags(["-lm"])
        check("ldflags()", "-lm" in prj.ldflags)

        pchheader("pch.h")
        check("pchheader()", prj.pchHeader == "pch.h")
        pchsource("pch.cpp")
        check("pchsource()", prj.pchSource == "pch.cpp")

        prebuild(["echo pre"])
        check("prebuild()", "echo pre" in prj.preBuildCommands)
        postbuild(["echo post"])
        check("postbuild()", "echo post" in prj.postBuildCommands)
        prelink(["echo prelink"])
        check("prelink()", "echo prelink" in prj.preLinkCommands)
        postlink(["echo postlink"])
        check("postlink()", "echo postlink" in prj.postLinkCommands)

        androidapplicationid("com.test.app")
        check("androidapplicationid()", prj.androidApplicationId == "com.test.app")
        androidminsdk(24)
        check("androidminsdk()", prj.androidMinSdk == 24)
        androidtargetsdk(34)
        check("androidtargetsdk()", prj.androidTargetSdk == 34)
        androidabis(["arm64-v8a", "x86_64"])
        check("androidabis()", len(prj.androidAbis) == 2)
        androidnativeactivity(True)
        check("androidnativeactivity()", prj.androidNativeActivity == True)

        iosbundleid("com.test.ios")
        check("iosbundleid()", prj.iosBundleId == "com.test.ios")
        iosversion("2.0")
        check("iosversion()", prj.iosVersion == "2.0")
        iosminsdk("14.0")
        check("iosminsdk()", prj.iosMinSdk == "14.0")
        iosbuildsystem("xbuilder")
        check("iosbuildsystem('xbuilder')", prj.iosBuildSystem == "xcode")
        iosbuildsystem("direct")
        check("iosbuildsystem('direct')", prj.iosBuildSystem == "direct")
        iosdistributiontype("ad-hoc")
        check("iosdistributiontype()", prj.iosDistributionType == "ad-hoc")
        iosteamid("TEAM123")
        check("iosteamid()", prj.iosTeamId == "TEAM123")
        iosprovisioningprofile("ProfileName")
        check("iosprovisioningprofile()", prj.iosProvisioningProfile == "ProfileName")

        emscriptenshellfile("shell.html")
        check("emscriptenshellfile()", prj.emscriptenShellFile == "shell.html")
        emscriptencanvasid("mycanvas")
        check("emscriptencanvasid()", prj.emscriptenCanvasId == "mycanvas")
        emscripteninitialmemory(32)
        check("emscripteninitialmemory()", prj.emscriptenInitialMemory == 32)

    # ========================================================================
    # 4. FILTER context manager
    # ========================================================================
    print("\n=== 4. Filter ===")

    with project("FilterTest") as prj:
        consoleapp()
        language("C++")
        files(["src/**.cpp"])

        with filter("system:Windows"):
            defines(["WIN32", "_WINDOWS"])
            links(["user32", "gdi32"])
            check("filter defines", "system:Windows" in prj._filteredDefines)
            check("filter links", "system:Windows" in prj._filteredLinks)

        with filter("config:Debug"):
            defines(["_DEBUG"])
            optimize("Off")
            check("filter config:Debug defines", "config:Debug" in prj._filteredDefines)

        with filter("config:Release"):
            optimize("Speed")
            symbols(False)
            check("filter config:Release optimize", "config:Release" in prj._filteredOptimize)

        with filter("system:Linux"):
            links(["pthread", "dl", "X11"])
            check("filter system:Linux links", "system:Linux" in prj._filteredLinks)

        with filter("system:Android"):
            links(["android", "log", "EGL"])
            check("filter system:Android links", "system:Android" in prj._filteredLinks)

    # ========================================================================
    # 5. TOOLCHAIN context manager
    # ========================================================================
    print("\n=== 5. Toolchain ===")

    with toolchain("my-clang", CompilerFamily.CLANG) as tc:
        check("toolchain created", tc is not None)
        check("toolchain name", tc.name == "my-clang")
        check("toolchain family", tc.compilerFamily == CompilerFamily.CLANG)
        check("toolchain in workspace", "my-clang" in wks.toolchains)

        settarget(TargetOS.LINUX, TargetArch.X86_64, TargetEnv.GNU)
        check("settarget()", tc.targetOs == TargetOS.LINUX)
        check("settarget() arch", tc.targetArch == TargetArch.X86_64)

        ccompiler("/usr/bin/clang")
        check("ccompiler()", tc.ccPath == "/usr/bin/clang")
        cppcompiler("/usr/bin/clang++")
        check("cppcompiler()", tc.cxxPath == "/usr/bin/clang++")

        linker("/usr/bin/ld.lld")
        check("linker()", tc.ldPath == "/usr/bin/ld.lld")
        archiver("/usr/bin/llvm-ar")
        check("archiver()", tc.arPath == "/usr/bin/llvm-ar")

        sysroot("/usr/aarch64-linux-gnu")
        check("sysroot()", tc.sysroot == "/usr/aarch64-linux-gnu")

        targettriple("x86_64-unknown-linux-gnu")
        check("targettriple()", tc.targetTriple == "x86_64-unknown-linux-gnu")

    with toolchain("android-custom", "android-ndk") as tc:
        check("toolchain string family", tc.compilerFamily == CompilerFamily.ANDROID_NDK)

    # ========================================================================
    # 6. UNITEST context manager
    # ========================================================================
    print("\n=== 6. Unitest ===")

    with unitest() as u:
        u.Compile(cxxflags=["-fexceptions"])
        check("unitest config mode", wks.unitestConfig.mode == "compile")
        check("unitest cxxflags", "-fexceptions" in wks.unitestConfig.cxxflags)

    check("__Unitest__ project created", "__Unitest__" in wks.projects)

    # ========================================================================
    # 7. TEST context manager
    # ========================================================================
    print("\n=== 7. Test ===")

    with project("Calculator") as prj:
        staticlib()
        language("C++")
        files(["src/**.cpp"])
        includedirs(["include"])

        with jenga_test() as t:
            testfiles(["tests/**.cpp"])
            check("test project created", t is not None)
            check("test project name", t.name == "Calculator_Tests")
            check("test project kind", t.kind == ProjectKind.TEST_SUITE)
            check("test isTest", t.isTest == True)
            check("test parentProject", t.parentProject == "Calculator")
            check("test dependsOn", "__Unitest__" in t.dependsOn)
            check("testfiles()", "tests/**.cpp" in t.testFiles)

    check("Calculator_Tests in workspace", "Calculator_Tests" in wks.projects)

    # ========================================================================
    # 8. PROJECT-level TOOLCHAIN
    # ========================================================================
    print("\n=== 8. Project Toolchain ===")

    with project("ToolchainedApp") as prj:
        consoleapp()
        usetoolchain("my-clang")
        check("usetoolchain()", prj.toolchain == "my-clang")
        check("usetoolchain explicit", prj._explicitToolchain == True)

# ============================================================================
# 9. MULTI-PROJECT DEPENDENCIES
# ============================================================================
print("\n=== 9. Multi-project Dependencies ===")
reset_state()

with workspace("MultiProject") as wks:
    configurations(["Debug", "Release"])
    targetoses([TargetOS.WINDOWS])
    targetarchs([TargetArch.X86_64])

    with project("Engine") as engine:
        staticlib()
        language("C++")
        files(["engine/**.cpp"])
        includedirs(["engine/include"])
        check("Engine created", "Engine" in wks.projects)

    with project("Game") as game:
        consoleapp()
        language("C++")
        files(["game/**.cpp"])
        dependson(["Engine"])
        links(["Engine"])
        check("Game depends on Engine", "Engine" in game.dependsOn)
        check("Game links Engine", "Engine" in game.links)

    check("workspace has 2 projects", len(wks.projects) == 2)

# ============================================================================
# 10. DATACLASS DEFAULTS
# ============================================================================
print("\n=== 10. Dataclass Defaults ===")

p = Project(name="defaults_test")
check("default kind", p.kind == ProjectKind.CONSOLE_APP)
check("default language", p.language == Language.CPP)
check("default cppdialect", p.cppdialect == "C++17")
check("default cdialect", p.cdialect == "C11")
check("default optimize", p.optimize == Optimization.OFF)
check("default symbols", p.symbols == True)
check("default warnings", p.warnings == WarningLevel.DEFAULT)
check("default androidMinSdk", p.androidMinSdk == 21)
check("default androidTargetSdk", p.androidTargetSdk == 33)
check("default isTest", p.isTest == False)

w = Workspace(name="defaults_ws")
check("workspace default configs", w.configurations == ["Debug", "Release"])
check("workspace default platforms", w.platforms == ["Windows"])

tc = Toolchain(name="test_tc", compilerFamily=CompilerFamily.GCC)
check("toolchain default targetOs", tc.targetOs is None)
tc.setTarget("WINDOWS", "X86_64", "MSVC")
check("toolchain setTarget() applied", tc.targetOs == TargetOS.WINDOWS)
check("toolchain setTarget() arch", tc.targetArch == TargetArch.X86_64)
check("toolchain setTarget() env", tc.targetEnv == TargetEnv.MSVC)

# ============================================================================
# 11. ERROR HANDLING
# ============================================================================
print("\n=== 11. Error Handling ===")
reset_state()

try:
    with toolchain("orphan", "clang") as tc:
        pass
    check("toolchain outside workspace raises", False, "should have raised")
except RuntimeError:
    check("toolchain outside workspace raises", True)

reset_state()
try:
    with unitest() as u:
        pass
    check("unitest outside workspace raises", False, "should have raised")
except RuntimeError:
    check("unitest outside workspace raises", True)

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
if errors:
    print("\nFailed tests:")
    for e in errors:
        print(e)
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
