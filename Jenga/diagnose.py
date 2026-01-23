#!/usr/bin/env python3
"""
Jenga Build System - Diagnostic Tool
Checks installation and identifies common issues
"""

import sys
import shutil
from pathlib import Path

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def check_item(condition, success_msg, fail_msg):
    if condition:
        print(f"✓ {success_msg}")
        return True
    else:
        print(f"✗ {fail_msg}")
        return False

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║       Jenga Build System - Diagnostic Tool v1.0.0            ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    issues = []
    
    # Python Version
    print_header("Python Environment")
    print(f"Python Version: {sys.version}")
    if sys.version_info >= (3, 7):
        print("✓ Python version is compatible (3.7+)")
    else:
        print("✗ Python 3.7+ required")
        issues.append("Python version too old")
    
    # File Structure
    print_header("File Structure")
    
    structure_checks = [
        ("Tools/jenga/core/api.py", "Core API"),
        ("Tools/jenga/Commands/build.py", "Build Command"),
        ("Tools/jenga/utils/display.py", "Display Utils"),
    ]
    
    for path, desc in structure_checks:
        exists = Path(path).exists()
        check_item(exists, f"{desc}: {path}", f"{desc} missing: {path}")
        if not exists:
            issues.append(f"Missing: {path}")
    
    # Unitest Structure
    print_header("Unitest Framework")
    
    unitest_tools = Path("Tools/jenga/Unitest/src/Unitest/Unitest.cpp")
    unitest_root = Path("Unitest/src/Unitest/Unitest.cpp")
    
    if unitest_tools.exists():
        print(f"✓ Unitest found in Tools: {unitest_tools}")
    else:
        print(f"✗ Unitest not in Tools: {unitest_tools}")
    
    if unitest_root.exists():
        print(f"✓ Unitest found in workspace root: {unitest_root}")
    else:
        print(f"⚠ Unitest not in workspace root: {unitest_root}")
        if unitest_tools.exists():
            print(f"  → Solution: Copy Unitest to workspace root")
            print(f"     cp -r Tools/jenga/Unitest Unitest")
            issues.append("Unitest not in workspace root")
    
    # Jenga Configuration
    print_header("Configuration Files")
    
    jenga_files = list(Path(".").glob("*.jenga"))
    if jenga_files:
        print(f"✓ Found {len(jenga_files)} .jenga file(s):")
        for f in jenga_files:
            print(f"  • {f}")
    else:
        print("✗ No .jenga configuration file found")
        print("  → Create a .jenga file to define your workspace")
        issues.append("No .jenga file")
    
    # Build Cache
    print_header("Build System")
    
    cache_dir = Path(".cjenga")
    if cache_dir.exists():
        print(f"✓ Cache directory exists: {cache_dir}")
        cache_file = cache_dir / "cbuild.json"
        if cache_file.exists():
            print(f"✓ Cache file exists: {cache_file}")
        else:
            print(f"⚠ Cache file will be created on first build")
    else:
        print(f"⚠ Cache directory will be created on first build: {cache_dir}")
    
    # Compilers
    print_header("Compilers")
    
    compilers = {
        "g++": "GCC C++ Compiler (Linux/MinGW)",
        "clang++": "Clang C++ Compiler",
        "cl": "MSVC C++ Compiler (Windows)"
    }
    
    found_compiler = False
    for compiler, desc in compilers.items():
        path = shutil.which(compiler)
        if path:
            print(f"✓ {desc}")
            print(f"  Path: {path}")
            found_compiler = True
        else:
            print(f"✗ {desc} not found")
    
    if not found_compiler:
        print("\n⚠ No C++ compiler found!")
        print("Install one of:")
        print("  • Windows: MinGW-w64 or Visual Studio")
        print("  • Linux: sudo apt-get install build-essential")
        print("  • macOS: xcode-select --install")
        issues.append("No compiler found")
    
    # Android (if applicable)
    print_header("Android Development (Optional)")
    
    android_sdk = Path.home() / "Android" / "Sdk"
    if android_sdk.exists():
        print(f"✓ Android SDK found: {android_sdk}")
    else:
        print("ℹ Android SDK not found (optional)")
        print("  For Android builds, install Android SDK")
    
    # Java (for Android signing)
    keytool = shutil.which("keytool")
    if keytool:
        print(f"✓ Java keytool available: {keytool}")
    else:
        print("ℹ Java keytool not found (needed for Android signing)")
    
    # Scripts
    print_header("Wrapper Scripts")
    
    scripts = []
    if Path("jenga.sh").exists():
        scripts.append("jenga.sh (Linux/Mac)")
    if Path("jenga.bat").exists():
        scripts.append("jenga.bat (Windows)")
    
    if scripts:
        for script in scripts:
            print(f"✓ {script}")
    else:
        print("⚠ No wrapper scripts found")
        issues.append("No wrapper scripts")
    
    # Summary
    print_header("Diagnostic Summary")
    
    if not issues:
        print("✅ All checks passed! Your Jenga installation looks good.")
        print("\nNext steps:")
        print("  1. Create a .jenga file (if not already done)")
        print("  2. Run: jenga build")
    else:
        print(f"⚠ Found {len(issues)} issue(s):\n")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        
        print("\n🔧 Recommended fixes:")
        
        if "Unitest not in workspace root" in issues:
            print("\n  Fix Unitest:")
            print("    # Windows")
            print("    xcopy /E /I Tools\\jenga\\Unitest Unitest")
            print("\n    # Linux/Mac")
            print("    cp -r Tools/jenga/Unitest Unitest")
        
        if "No compiler found" in issues:
            print("\n  Install compiler:")
            print("    # Windows: Download MinGW-w64")
            print("    # Linux: sudo apt-get install build-essential")
            print("    # macOS: xcode-select --install")
        
        if "No .jenga file" in issues:
            print("\n  Create .jenga:")
            print("    with workspace('MyApp'):")
            print("        with project('App'):")
            print("            consoleapp()")
            print("            files(['src/**.cpp'])")
    
    print("\n" + "="*60)
    print("For more help, see TROUBLESHOOTING.md")
    print("="*60 + "\n")
    
    return 0 if not issues else 1

if __name__ == "__main__":
    sys.exit(main())
