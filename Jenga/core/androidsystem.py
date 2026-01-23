#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Android Support
Handles Android NDK compilation and APK packaging
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

try:
    from ..utils.display import Display
    from ..utils.reporter import Reporter
except ImportError:
    from utils.display import Display
    from utils.reporter import Reporter


class AndroidBuilder:
    """Android-specific build operations"""
    
    def __init__(self, workspace, project, config: str):
        self.workspace = workspace
        self.project = project
        self.config = config
        
        # Validate Android SDK/NDK paths
        self.sdk_path = workspace.androidsdkpath
        self.ndk_path = workspace.androidndkpath
        self.jdk_path = workspace.javajdkpath
        
        if not self.sdk_path:
            raise RuntimeError("Android SDK path not configured (use androidsdkpath)")
        if not self.ndk_path:
            raise RuntimeError("Android NDK path not configured (use androidndkpath)")
    
    def get_android_toolchain(self) -> dict:
        """Get Android NDK toolchain configuration"""
        
        ndk_path = Path(self.ndk_path)
        
        # Determine host platform
        import platform
        system = platform.system().lower()
        
        if system == "windows":
            host_tag = "windows-x86_64"
            exe_ext = ".exe"
        elif system == "linux":
            host_tag = "linux-x86_64"
            exe_ext = ""
        elif system == "darwin":
            host_tag = "darwin-x86_64"
            exe_ext = ""
        else:
            raise RuntimeError(f"Unsupported host platform: {system}")
        
        # NDK toolchain paths
        toolchain_root = ndk_path / "toolchains" / "llvm" / "prebuilt" / host_tag
        
        # Target architecture (can be made configurable)
        target = "aarch64-linux-android"  # ARM64 default
        api_level = self.project.androidminsdk or 21
        
        toolchain = {
            "cxx": str(toolchain_root / "bin" / f"{target}{api_level}-clang++{exe_ext}"),
            "cc": str(toolchain_root / "bin" / f"{target}{api_level}-clang{exe_ext}"),
            "ar": str(toolchain_root / "bin" / f"llvm-ar{exe_ext}"),
            "sysroot": str(toolchain_root / "sysroot"),
            "target": target,
        }
        
        return toolchain
    
    def get_android_flags(self) -> list:
        """Get Android-specific compiler flags"""
        flags = [
            "-fPIC",
            "-ffunction-sections",
            "-fdata-sections",
            "-funwind-tables",
            "-fstack-protector-strong",
            "-no-canonical-prefixes",
        ]
        
        return flags
    
    def get_android_defines(self) -> list:
        """Get Android-specific defines"""
        defines = [
            "ANDROID",
            "__ANDROID__",
            f"__ANDROID_API__={self.project.androidminsdk}",
        ]
        
        return defines
    
    def build_native_library(self, output_file: str) -> bool:
        """Build native library (.so) for Android"""
        
        Reporter.info("Building Android native library...")
        
        # This would integrate with the main compilation system
        # The toolchain would be configured for Android
        
        return True
    
    def create_apk(self, native_lib: str, output_apk: str) -> bool:
        """Create Android APK (simplified version)"""
        
        Reporter.info("Creating Android APK...")
        
        # This is a simplified outline - full APK creation requires:
        # 1. Android manifest
        # 2. Resources compilation (aapt2)
        # 3. DEX compilation (d8)
        # 4. APK packaging (zipalign)
        # 5. APK signing (apksigner)
        
        Display.warning("APK creation not fully implemented yet")
        Display.info("Native library built at: " + native_lib)
        
        return True


def configure_android_toolchain(workspace) -> Optional[object]:
    """Configure toolchain for Android compilation"""
    
    if not workspace.androidndkpath:
        Display.error("Android NDK path not configured")
        return None
    
    # Create a specialized Android toolchain
    from core.api import Toolchain
    
    ndk_path = Path(workspace.androidndkpath)
    
    # Determine host
    import platform
    system = platform.system().lower()
    
    if system == "windows":
        host_tag = "windows-x86_64"
        exe_ext = ".exe"
    elif system == "linux":
        host_tag = "linux-x86_64"
        exe_ext = ""
    elif system == "darwin":
        host_tag = "darwin-x86_64"
        exe_ext = ""
    else:
        raise RuntimeError(f"Unsupported host platform: {system}")
    
    toolchain_root = ndk_path / "toolchains" / "llvm" / "prebuilt" / host_tag
    
    # Default to ARM64
    target = "aarch64-linux-android"
    api_level = 21
    
    toolchain = Toolchain(
        name="android",
        compiler=f"{target}{api_level}-clang++",
        cppcompiler=f"{target}{api_level}-clang++",
        ccompiler=f"{target}{api_level}-clang",
        archiver="llvm-ar",
        sysroot=str(toolchain_root / "sysroot"),
        targettriple=target,
        toolchain_dir=str(toolchain_root / "bin")
    )
    
    # Set paths
    toolchain.cppcompiler_path = str(toolchain_root / "bin" / f"{target}{api_level}-clang++{exe_ext}")
    toolchain.ccompiler_path = str(toolchain_root / "bin" / f"{target}{api_level}-clang{exe_ext}")
    toolchain.archiver_path = str(toolchain_root / "bin" / f"llvm-ar{exe_ext}")
    
    # Android-specific flags
    toolchain.cxxflags = [
        "-fPIC",
        "-ffunction-sections",
        "-fdata-sections",
        "-funwind-tables",
        "-fstack-protector-strong",
    ]
    
    toolchain.defines = [
        "ANDROID",
        "__ANDROID__",
        f"__ANDROID_API__={api_level}",
    ]
    
    return toolchain
