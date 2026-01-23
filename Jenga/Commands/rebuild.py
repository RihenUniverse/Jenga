#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Rebuild Command
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from Commands import build, clean
from utils.display import Display


def execute(options: dict) -> bool:
    """Execute rebuild command (clean + build)"""
    
    Display.info("Rebuild: Cleaning first...")
    
    # Clean
    if not clean.execute(options):
        Display.error("Clean failed")
        return False
    
    print()  # Blank line
    
    Display.info("Rebuild: Building...")
    
    # Build
    if not build.execute(options):
        Display.error("Build failed")
        return False
    
    return True


if __name__ == "__main__":
    execute({})
