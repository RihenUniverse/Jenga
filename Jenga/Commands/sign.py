#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Build System - Sign Command
Signs applications (Android APK, iOS IPA, macOS apps, Windows executables)
"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.loader import load_workspace
from utils.display import Display, Colors


def execute(options: dict) -> bool:
    """Execute sign command"""
    
    # Load workspace
    workspace = load_workspace()
    if not workspace:
        return False
    
    platform = options.get('platform', 'Android')
    project_name = options.get('project')
    apk_path = options.get('apk')
    keystore = options.get('keystore')
    
    Display.section(f"Signing {platform} Application")
    
    # Get project
    if project_name:
        if project_name not in workspace.projects:
            Display.error(f"Project '{project_name}' not found")
            return False
        project = workspace.projects[project_name]
    else:
        # Use start project
        if workspace.startproject and workspace.startproject in workspace.projects:
            project = workspace.projects[workspace.startproject]
        else:
            Display.error("No project specified. Use --project <name>")
            return False
    
    if platform == 'Android':
        return _sign_android(workspace, project, apk_path, keystore, options)
    elif platform == 'iOS':
        return _sign_ios(workspace, project, options)
    elif platform == 'Windows':
        return _sign_windows(workspace, project, options)
    elif platform == 'MacOS':
        return _sign_macos(workspace, project, options)
    else:
        Display.error(f"Signing not supported for platform: {platform}")
        return False


def _sign_android(workspace, project, apk_path, keystore_path, options):
    """Sign Android APK"""
    
    Display.step("Signing Android APK...")
    
    # Get APK path
    if not apk_path:
        config = options.get('config', 'Release')
        package_dir = Path(workspace.location) / "Build" / "Packages"
        apk_path = package_dir / f"{project.name}-{config}.apk"
    else:
        apk_path = Path(apk_path)
    
    if not apk_path.exists():
        Display.error(f"APK not found: {apk_path}")
        Display.info("Build and package the APK first with: jenga package")
        return False
    
    Display.info(f"APK: {apk_path}")
    
    # Get keystore
    if keystore_path:
        keystore = keystore_path
    elif project.androidkeystore:
        keystore = project.androidkeystore
    else:
        Display.error("No keystore specified")
        Display.info("Options:")
        Display.info("  1. Use --keystore /path/to/keystore.jks")
        Display.info("  2. Set in .jenga: androidkeystore(\"/path/to/keystore.jks\")")
        Display.info("  3. Generate with: jenga keygen")
        return False
    
    keystore = Path(keystore)
    if not keystore.exists():
        Display.error(f"Keystore not found: {keystore}")
        Display.info("Generate a keystore with: jenga keygen")
        return False
    
    Display.info(f"Keystore: {keystore}")
    
    # Get signing parameters
    keystore_pass = options.get('storepass') or project.androidkeystorepass or "android"
    key_alias = options.get('alias') or project.androidkeyalias or "key0"
    
    # Find apksigner
    if not workspace.androidsdkpath:
        Display.error("Android SDK path not set")
        Display.info("Set it with: androidsdkpath(\"/path/to/android-sdk\")")
        return False
    
    sdk_path = Path(workspace.androidsdkpath)
    build_tools_dir = sdk_path / "build-tools"
    
    if not build_tools_dir.exists():
        Display.error("Build-tools not found in Android SDK")
        return False
    
    # Get latest build tools
    build_tools_versions = sorted([d.name for d in build_tools_dir.iterdir() if d.is_dir()])
    if not build_tools_versions:
        Display.error("No build-tools version found")
        return False
    
    build_tools_version = build_tools_versions[-1]
    apksigner = build_tools_dir / build_tools_version / "apksigner"
    
    if not apksigner.exists():
        # Try apksigner.bat on Windows
        apksigner = build_tools_dir / build_tools_version / "apksigner.bat"
        if not apksigner.exists():
            Display.error("apksigner not found in build-tools")
            return False
    
    Display.info(f"Using apksigner from: {build_tools_version}")
    
    # Output signed APK
    signed_apk = apk_path.parent / f"{apk_path.stem}-signed.apk"
    
    # Sign APK
    Display.info("Signing APK...")
    
    try:
        cmd = [
            str(apksigner), "sign",
            "--ks", str(keystore),
            "--ks-pass", f"pass:{keystore_pass}",
            "--ks-key-alias", key_alias,
            "--out", str(signed_apk),
            str(apk_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            Display.error(f"Failed to sign APK:")
            print(result.stderr)
            return False
        
        Display.success(f"\n✓ APK signed successfully!")
        Display.info(f"  Signed APK: {signed_apk}")
        Display.info(f"  Size: {signed_apk.stat().st_size / (1024*1024):.2f} MB")
        
        # Verify signature
        Display.info("\nVerifying signature...")
        
        verify_cmd = [str(apksigner), "verify", str(signed_apk)]
        verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
        
        if verify_result.returncode == 0:
            Display.success("✓ APK signature verified")
        else:
            Display.warning("⚠ Could not verify signature")
        
        return True
        
    except Exception as e:
        Display.error(f"Error signing APK: {e}")
        return False


def _sign_ios(workspace, project, options):
    """Sign iOS IPA"""
    
    Display.step("Signing iOS IPA...")
    Display.warning("iOS signing requires valid provisioning profiles and certificates")
    
    # TODO: Implement iOS code signing
    # codesign --force --sign "iPhone Developer: ..." --entitlements ... MyApp.app
    
    Display.info("This feature is under development")
    Display.info("For now, use Xcode for iOS code signing")
    
    return False


def _sign_windows(workspace, project, options):
    """Sign Windows executable with Authenticode"""
    
    Display.step("Signing Windows executable...")
    Display.warning("Windows code signing requires a valid certificate")
    
    # TODO: Implement Windows Authenticode signing
    # signtool sign /f certificate.pfx /p password /tr http://timestamp.digicert.com /td sha256 /fd sha256 MyApp.exe
    
    Display.info("This feature is under development")
    Display.info("Use signtool.exe from Windows SDK for code signing")
    
    return False


def _sign_macos(workspace, project, options):
    """Sign macOS application"""
    
    Display.step("Signing macOS application...")
    Display.warning("macOS signing requires a valid Developer ID certificate")
    
    # TODO: Implement macOS code signing
    # codesign --force --deep --sign "Developer ID Application: ..." MyApp.app
    
    Display.info("This feature is under development")
    Display.info("Use codesign from Xcode Command Line Tools")
    
    return False


if __name__ == "__main__":
    execute({})