#!/usr/bin/env python3
"""
Zig compiler wrapper - translates standard compiler interface to Zig syntax.

Usage:
    zig-wrapper.py [cc|c++|ar] [args...]

Examples:
    zig-wrapper.py c++ -c -o output.o source.cpp
    -> zig c++ -c source.cpp -o output.o

    zig-wrapper.py ar rcs libfoo.a obj1.o obj2.o
    -> zig ar rcs libfoo.a obj1.o obj2.o
"""

import sys
import subprocess
from pathlib import Path

ZIG_EXE = r"C:\Zig\zig-x86_64-windows-0.16.0\zig.exe"

def main():
    if len(sys.argv) < 2:
        print("Error: Missing command (cc/c++/ar)")
        sys.exit(1)

    # Get command (cc, c++, ar)
    zig_cmd = sys.argv[1]
    args = sys.argv[2:]

    # Find zig.exe
    zig_path = Path(ZIG_EXE)
    if not zig_path.exists():
        # Try PATH
        import shutil
        zig_found = shutil.which("zig")
        if zig_found:
            zig_path = Path(zig_found)
        else:
            print("Error: zig.exe not found")
            sys.exit(1)

    # Build command: zig <cmd> <args>
    cmd = [str(zig_path), zig_cmd] + args

    # Execute
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
