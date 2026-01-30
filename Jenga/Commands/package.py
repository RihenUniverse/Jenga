#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Build System - Package Command
Packages applications for distribution (APK, AAB, ZIP, DMG, etc.)
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.loader import load_workspace
from core.api import ProjectKind
from utils.display import Display, Colors


def execute(options: dict) -> bool:
    """Execute package command"""
    
    # Load workspace
    workspace = load_workspace()
    if not workspace:
        return False
    
    config = options.get('config', 'Release')
    platform = options.get('platform', 'Linux')
    project_name = options.get('project')
    output_type = options.get('type', 'auto')  # auto, apk, aab, zip, dmg, exe
    
    Display.section("Packaging Application")
    
    # Get project to package
    if project_name:
        if project_name not in workspace.projects:
            Display.error(f"Project '{project_name}' not found")
            return False
        project = workspace.projects[project_name]
    else:
        # Use start project or first executable
        if workspace.startproject and workspace.startproject in workspace.projects:
            project = workspace.projects[workspace.startproject]
        else:
            # Find first executable project
            for name, proj in workspace.projects.items():
                if proj.kind in [ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP]:
                    project = proj
                    break
            else:
                Display.error("No executable project found to package")
                return False
    
    Display.info(f"Packaging project: {project.name}")
    Display.info(f"Configuration: {config}")
    Display.info(f"Platform: {platform}")
    
    # Determine package type based on platform
    if output_type == 'auto':
        if platform == 'Android':
            output_type = 'apk'  # or 'aab' for Play Store
        elif platform == 'iOS':
            output_type = 'ipa'
        elif platform == 'Windows':
            output_type = 'zip'
        elif platform == 'MacOS':
            output_type = 'dmg'
        else:
            output_type = 'zip'
    
    Display.info(f"Package type: {output_type.upper()}")
    
    # Execute packaging based on platform
    if platform == 'Android':
        return _package_android(workspace, project, config, output_type, options)
    elif platform == 'iOS':
        return _package_ios(workspace, project, config, options)
    elif platform == 'Windows':
        return _package_windows(workspace, project, config, options)
    elif platform == 'MacOS':
        return _package_macos(workspace, project, config, options)
    else:
        return _package_generic(workspace, project, config, platform, options)
    

def _package_android(workspace, project, config, package_type, options):
    """Package Android application as APK or AAB using Gradle"""
    
    Display.step(f"Building Android {package_type.upper()}...")
    
    # Validate
    if not workspace.androidsdkpath:
        Display.error("Android SDK path not set")
        Display.info("Use: androidsdkpath(\"/path/to/sdk\")")
        return False
    
    if not workspace.androidndkpath:
        Display.error("Android NDK path not set")
        Display.info("Use: androidndkpath(\"/path/to/ndk\")")
        return False
    
    # Import enhanced builder
    from core.androidsystem import build_android_with_gradle
    
    # Build
    output_path = build_android_with_gradle(workspace, project, config, package_type)
    
    if output_path:
        Display.success(f"\n✅ Android {package_type.upper()} created!")
        Display.info(f"   Location: {output_path}")
        Display.info(f"   Size: {output_path.stat().st_size / (1024*1024):.2f} MB")
        
        if package_type == 'apk':
            print(f"\n{Display.info_prefix()} Install:")
            print(f"   adb install {output_path}")
        elif package_type == 'aab':
            print(f"\n{Display.info_prefix()} Upload to Play Store")
        
        return True
    else:
        Display.error(f"Failed to build {package_type.upper()}")
        return False


# def _package_android(workspace, project, config, package_type, options):
#     """Package Android application as APK or AAB"""
    
#     Display.step("Building Android package...")
    
#     # Check for Android SDK/NDK
#     if not workspace.androidsdkpath:
#         Display.error("Android SDK path not set in workspace")
#         Display.info("Set it with: androidsdkpath(\"/path/to/android-sdk\")")
#         return False
    
#     sdk_path = Path(workspace.androidsdkpath)
#     if not sdk_path.exists():
#         Display.error(f"Android SDK not found at: {sdk_path}")
#         return False
    
#     # Build tools
#     build_tools_dir = sdk_path / "build-tools"
#     if not build_tools_dir.exists():
#         Display.error("Android build-tools not found")
#         return False
    
#     # Get latest build tools version
#     build_tools_versions = sorted([d.name for d in build_tools_dir.iterdir() if d.is_dir()])
#     if not build_tools_versions:
#         Display.error("No Android build-tools version found")
#         return False
    
#     build_tools_version = build_tools_versions[-1]
#     build_tools_path = build_tools_dir / build_tools_version
    
#     Display.info(f"Using build-tools: {build_tools_version}")
    
#     # Paths
#     aapt = build_tools_path / "aapt"
#     aapt2 = build_tools_path / "aapt2"
#     zipalign = build_tools_path / "zipalign"
#     apksigner = build_tools_path / "apksigner"
    
#     if not aapt.exists() and not aapt2.exists():
#         Display.error("aapt/aapt2 not found in build-tools")
#         return False
    
#     # Project directories
#     project_dir = Path(workspace.location) / project.location
#     build_dir = Path(workspace.location) / "Build" / platform / config
#     package_dir = build_dir / "Package"
#     package_dir.mkdir(parents=True, exist_ok=True)
    
#     # App ID
#     app_id = project.androidapplicationid or f"com.example.{project.name.lower()}"
#     version_code = project.androidversioncode or 1
#     version_name = project.androidversionname or "1.0"
    
#     Display.info(f"App ID: {app_id}")
#     Display.info(f"Version: {version_name} ({version_code})")
    
#     if package_type == 'aab':
#         return _build_aab(workspace, project, config, package_dir, options)
#     else:
#         return _build_apk(workspace, project, config, package_dir, build_tools_path, options)


def _build_apk(workspace, project, config, package_dir, build_tools_path, options):
    """Build Android APK"""
    
    Display.step("Building APK...")
    
    # Temporary APK structure
    apk_temp = package_dir / "apk_temp"
    apk_temp.mkdir(parents=True, exist_ok=True)
    
    # Create APK directory structure
    (apk_temp / "lib").mkdir(exist_ok=True)
    (apk_temp / "assets").mkdir(exist_ok=True)
    (apk_temp / "res").mkdir(exist_ok=True)
    (apk_temp / "META-INF").mkdir(exist_ok=True)
    
    # Create AndroidManifest.xml
    manifest_path = apk_temp / "AndroidManifest.xml"
    _create_android_manifest(project, manifest_path)
    
    # Copy native libraries
    lib_dir = Path(workspace.location) / "Build" / "Android" / config / "Lib"
    if lib_dir.exists():
        Display.info("Copying native libraries...")
        for lib_file in lib_dir.glob("*.so"):
            abi_dir = apk_temp / "lib" / "arm64-v8a"  # TODO: Support multiple ABIs
            abi_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(lib_file, abi_dir / lib_file.name)
    
    # Copy assets if specified
    if project.dependfiles:
        Display.info("Copying assets...")
        for pattern in project.dependfiles:
            # TODO: Copy assets
            pass
    
    # Package APK using aapt or aapt2
    aapt = build_tools_path / "aapt"
    platform_dir = Path(workspace.androidsdkpath) / "platforms"
    
    # Find latest platform
    platforms = sorted([d.name for d in platform_dir.iterdir() if d.is_dir() and d.name.startswith("android-")])
    if platforms:
        android_jar = platform_dir / platforms[-1] / "android.jar"
    else:
        Display.error("No Android platform found")
        return False
    
    apk_name = f"{project.name}-{config}.apk"
    apk_unsigned = package_dir / f"{project.name}-unsigned.apk"
    apk_aligned = package_dir / f"{project.name}-aligned.apk"
    apk_signed = package_dir / apk_name
    
    Display.info("Creating unsigned APK...")
    
    # Create APK with aapt
    try:
        cmd = [
            str(aapt), "package",
            "-f", "-M", str(manifest_path),
            "-I", str(android_jar),
            "-F", str(apk_unsigned),
            str(apk_temp)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            Display.error(f"Failed to create APK: {result.stderr}")
            return False
    except Exception as e:
        Display.error(f"Error creating APK: {e}")
        return False
    
    Display.success("✓ Unsigned APK created")
    
    # Align APK
    zipalign = build_tools_path / "zipalign"
    if zipalign.exists():
        Display.info("Aligning APK...")
        try:
            cmd = [str(zipalign), "-f", "4", str(apk_unsigned), str(apk_aligned)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                Display.warning(f"Failed to align APK: {result.stderr}")
                apk_aligned = apk_unsigned
            else:
                Display.success("✓ APK aligned")
        except Exception as e:
            Display.warning(f"Could not align APK: {e}")
            apk_aligned = apk_unsigned
    else:
        apk_aligned = apk_unsigned
    
    # Sign APK if requested
    if project.androidsign and project.androidkeystore:
        Display.info("Signing APK...")
        success = _sign_apk(apk_aligned, apk_signed, project, build_tools_path)
        if not success:
            Display.warning("APK not signed, using aligned version")
            apk_signed = apk_aligned
    else:
        Display.warning("APK signing not configured")
        Display.info("To enable signing, set: androidsign(True), androidkeystore(\"/path/to/key.jks\")")
        apk_signed = apk_aligned
    
    # Final APK
    final_apk = package_dir / apk_name
    if apk_signed != final_apk:
        shutil.copy2(apk_signed, final_apk)
    
    Display.success(f"\n✓ APK created: {final_apk}")
    Display.info(f"  Size: {final_apk.stat().st_size / (1024*1024):.2f} MB")
    
    return True


def _build_aab(workspace, project, config, package_dir, options):
    """Build Android App Bundle (AAB) for Play Store"""
    
    Display.step("Building AAB (Android App Bundle)...")
    Display.warning("AAB building requires bundletool and gradle")
    Display.info("This feature is under development")
    
    # TODO: Implement AAB building with bundletool
    # bundletool build-bundle --modules=base.zip --output=app.aab
    
    return False


def _sign_apk(apk_path, output_path, project, build_tools_path):
    """Sign APK with keystore"""
    
    keystore = project.androidkeystore
    keystore_pass = project.androidkeystorepass or "android"
    key_alias = project.androidkeyalias or "key0"
    
    if not Path(keystore).exists():
        Display.error(f"Keystore not found: {keystore}")
        return False
    
    apksigner = build_tools_path / "apksigner"
    
    if apksigner.exists():
        # Use apksigner (v2/v3 signature)
        try:
            cmd = [
                str(apksigner), "sign",
                "--ks", keystore,
                "--ks-pass", f"pass:{keystore_pass}",
                "--ks-key-alias", key_alias,
                "--out", str(output_path),
                str(apk_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                Display.error(f"Failed to sign APK: {result.stderr}")
                return False
            
            Display.success("✓ APK signed successfully")
            return True
            
        except Exception as e:
            Display.error(f"Error signing APK: {e}")
            return False
    else:
        Display.error("apksigner not found in build-tools")
        return False


def _create_android_manifest(project, output_path):
    """Create AndroidManifest.xml"""
    
    app_id = project.androidapplicationid or f"com.example.{project.name.lower()}"
    version_code = project.androidversioncode or 1
    version_name = project.androidversionname or "1.0"
    min_sdk = project.androidminsdk or 21
    target_sdk = project.androidtargetsdk or 33
    
    manifest = f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{app_id}"
    android:versionCode="{version_code}"
    android:versionName="{version_name}">
    
    <uses-sdk
        android:minSdkVersion="{min_sdk}"
        android:targetSdkVersion="{target_sdk}" />
    
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
    
    <application
        android:label="{project.name}"
        android:hasCode="false"
        android:debuggable="false">
        
        <activity
            android:name="android.app.NativeActivity"
            android:label="{project.name}"
            android:exported="true">
            <meta-data
                android:name="android.app.lib_name"
                android:value="{project.name.lower()}" />
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""
    
    with open(output_path, 'w') as f:
        f.write(manifest)


def _package_ios(workspace, project, config, options):
    """Package iOS application as IPA"""
    
    Display.step("Building iOS IPA...")
    Display.warning("iOS packaging requires Xcode and proper provisioning")
    
    # TODO: Implement iOS IPA packaging
    # xcodebuild -exportArchive -archivePath ... -exportPath ... -exportOptionsPlist ...
    
    Display.info("This feature is under development")
    return False


def _package_windows(workspace, project, config, options):
    """Package Windows application"""
    
    Display.step("Packaging Windows application...")
    
    build_dir = Path(workspace.location) / "Build" / "Windows" / config / "Bin"
    exe_file = build_dir / f"{project.name}.exe"
    
    if not exe_file.exists():
        Display.error(f"Executable not found: {exe_file}")
        Display.info("Build the project first with: jenga build")
        return False
    
    # Create package directory
    package_dir = Path(workspace.location) / "Build" / "Packages"
    package_dir.mkdir(parents=True, exist_ok=True)
    
    # Create ZIP package
    import zipfile
    
    zip_name = f"{project.name}-{config}-Windows.zip"
    zip_path = package_dir / zip_name
    
    Display.info(f"Creating package: {zip_name}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add executable
        zipf.write(exe_file, exe_file.name)
        
        # Add DLLs
        for dll in build_dir.glob("*.dll"):
            zipf.write(dll, dll.name)
        
        # Add assets
        if project.dependfiles:
            for pattern in project.dependfiles:
                # TODO: Add assets to ZIP
                pass
    
    Display.success(f"✓ Package created: {zip_path}")
    Display.info(f"  Size: {zip_path.stat().st_size / (1024*1024):.2f} MB")
    
    return True


def _package_macos(workspace, project, config, options):
    """Package macOS application as .app bundle or DMG"""
    
    Display.step("Packaging macOS application...")
    
    # TODO: Implement macOS .app bundle and DMG creation
    # create-dmg --volname "App Name" --window-pos 200 120 --window-size 600 400 ...
    
    Display.info("This feature is under development")
    return False


def _package_generic(workspace, project, config, platform, options):
    """Generic packaging for other platforms (ZIP)"""
    
    Display.step(f"Packaging {platform} application...")
    
    build_dir = Path(workspace.location) / "Build" / platform / config / "Bin"
    exe_file = build_dir / project.name
    
    if not exe_file.exists():
        Display.error(f"Executable not found: {exe_file}")
        return False
    
    # Create package directory
    package_dir = Path(workspace.location) / "Build" / "Packages"
    package_dir.mkdir(parents=True, exist_ok=True)
    
    # Create ZIP
    import zipfile
    
    zip_name = f"{project.name}-{config}-{platform}.zip"
    zip_path = package_dir / zip_name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(exe_file, exe_file.name)
        
        # Add shared libraries
        for so in build_dir.glob("*.so"):
            zipf.write(so, so.name)
        
        for dylib in build_dir.glob("*.dylib"):
            zipf.write(dylib, dylib.name)
    
    Display.success(f"✓ Package created: {zip_path}")
    
    return True


if __name__ == "__main__":
    execute({})
