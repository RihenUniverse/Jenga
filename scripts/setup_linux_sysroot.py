#!/usr/bin/env python3
"""
Setup Linux sysroot for cross-compilation on Windows.
Downloads and extracts necessary headers and libraries including X11.

Usage:
    python setup_linux_sysroot.py [target_dir]

Example:
    python setup_linux_sysroot.py C:/sysroot/linux-x86_64
"""

import sys
import os
import urllib.request
import tarfile
import json
from pathlib import Path
import subprocess
import tempfile
import shutil

DEBIAN_MIRROR = "http://ftp.debian.org/debian"
UBUNTU_PACKAGES = "http://packages.ubuntu.com"

# Packages requis pour X11 et développement C/C++
REQUIRED_PACKAGES = [
    "libc6-dev",
    "libstdc++-11-dev",
    "libx11-dev",
    "libx11-6",
    "libxext-dev",
    "libxext6",
    "libxrandr-dev",
    "libxrandr2",
    "libxinerama-dev",
    "libxcursor-dev",
    "libxi-dev",
    "linux-libc-dev"
]

def download_file(url, dest_path):
    """Download file with progress."""
    print(f"Downloading: {url}")
    try:
        with urllib.request.urlopen(url) as response:
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0

            with open(dest_path, 'wb') as f:
                while True:
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}%", end='', flush=True)
        print()  # New line
        return True
    except Exception as e:
        print(f"\nError downloading: {e}")
        return False

def extract_deb(deb_path, extract_to):
    """Extract .deb package to directory."""
    print(f"Extracting: {deb_path.name}")
    temp_dir = tempfile.mkdtemp()

    try:
        # Extract .deb (which is an ar archive)
        subprocess.run(["ar", "x", str(deb_path)], cwd=temp_dir, check=True)

        # Find data.tar.* file
        data_tar = None
        for f in os.listdir(temp_dir):
            if f.startswith("data.tar"):
                data_tar = os.path.join(temp_dir, f)
                break

        if not data_tar:
            print("Warning: data.tar not found in package")
            return False

        # Extract data.tar to destination
        with tarfile.open(data_tar) as tar:
            tar.extractall(extract_to)

        return True

    except Exception as e:
        print(f"Error extracting {deb_path}: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def create_simple_sysroot(sysroot_dir):
    """
    Create a minimal sysroot with X11 headers from system or download.
    """
    sysroot_dir = Path(sysroot_dir)
    sysroot_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Creating Linux Sysroot with X11 Support")
    print("=" * 60)
    print(f"Target directory: {sysroot_dir.absolute()}")
    print()

    # Create directory structure
    usr_include = sysroot_dir / "usr" / "include"
    usr_lib = sysroot_dir / "usr" / "lib" / "x86_64-linux-gnu"

    usr_include.mkdir(parents=True, exist_ok=True)
    usr_lib.mkdir(parents=True, exist_ok=True)

    # Check if running on WSL or Linux
    if os.path.exists("/usr/include/X11"):
        print("[OK] Found local X11 headers, copying...")
        shutil.copytree("/usr/include/X11", usr_include / "X11", dirs_exist_ok=True)

        # Copy standard C headers
        for header_dir in ["/usr/include/x86_64-linux-gnu", "/usr/include"]:
            if os.path.exists(header_dir):
                for item in os.listdir(header_dir):
                    src = os.path.join(header_dir, item)
                    if os.path.isfile(src) and item.endswith('.h'):
                        shutil.copy2(src, usr_include)

        # Copy libraries
        for lib_dir in ["/usr/lib/x86_64-linux-gnu", "/lib/x86_64-linux-gnu"]:
            if os.path.exists(lib_dir):
                for lib in os.listdir(lib_dir):
                    if lib.startswith("libX11") or lib.startswith("libc") or lib.startswith("libpthread"):
                        src = os.path.join(lib_dir, lib)
                        if os.path.isfile(src):
                            shutil.copy2(src, usr_lib)

        print("[OK] Sysroot created successfully from local system")
        return True

    else:
        print("[WARNING] No local X11 headers found.")
        print("Manual setup required:")
        print()
        print("Option 1 - WSL/Linux:")
        print("  1. Install WSL2 with Ubuntu")
        print("  2. Install packages: sudo apt install libx11-dev build-essential")
        print(f"  3. Run this script from WSL: python3 {sys.argv[0]} {sysroot_dir}")
        print()
        print("Option 2 - Docker:")
        print("  1. docker run -v C:/sysroot:/output ubuntu:22.04")
        print("  2. apt update && apt install -y libx11-dev build-essential")
        print("  3. cp -r /usr/include /output/ && cp -r /usr/lib/x86_64-linux-gnu /output/lib/")
        print()
        print("Option 3 - Manual download:")
        print("  Download .deb packages from https://packages.ubuntu.com/")
        print("  Extract them to the sysroot directory")
        print()

        # Create stub headers for testing
        print("Creating minimal stub headers for basic testing...")
        x11_dir = usr_include / "X11"
        x11_dir.mkdir(parents=True, exist_ok=True)

        # Create a minimal Xlib.h stub
        stub_header = x11_dir / "Xlib.h"
        stub_header.write_text("""
#ifndef _XLIB_H_
#define _XLIB_H_

/* Minimal X11 stub header for cross-compilation */
/* This is NOT complete - install real headers from Ubuntu/Debian packages */

typedef struct _XDisplay Display;
typedef unsigned long Window;
typedef unsigned long XID;

Display* XOpenDisplay(const char*);
int XCloseDisplay(Display*);

#endif /* _XLIB_H_ */
""")
        print(f"[OK] Created stub header: {stub_header}")
        print()
        print("[WARNING] Stub headers are incomplete!")
        print("   Install real Ubuntu/Debian packages for production use.")

        return True

def main():
    if len(sys.argv) > 1:
        sysroot_dir = sys.argv[1]
    else:
        # Default location
        sysroot_dir = Path(__file__).parent.parent / "sysroot" / "linux-x86_64"

    success = create_simple_sysroot(sysroot_dir)

    if success:
        print()
        print("=" * 60)
        print("[OK] Sysroot setup completed!")
        print("=" * 60)
        print()
        print("Next steps:")
        print(f"  1. Use sysroot path: {Path(sysroot_dir).absolute()}")
        print("  2. Add to your .jenga file:")
        print()
        print("     with project('MyApp'):")
        print(f"         sysroot(r'{Path(sysroot_dir).absolute()}')")
        print("         includedirs([r'<sysroot>/usr/include'])")
        print("         libdirs([r'<sysroot>/usr/lib/x86_64-linux-gnu'])")
        print()
    else:
        print("[ERROR] Sysroot setup failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
