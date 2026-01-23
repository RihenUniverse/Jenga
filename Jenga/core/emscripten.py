#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Emscripten Support
Handles WebAssembly compilation with Emscripten
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


class EmscriptenBuilder:
    """Emscripten-specific build operations"""
    
    def __init__(self, workspace, project, config: str):
        self.workspace = workspace
        self.project = project
        self.config = config
        
        # Detect Emscripten SDK
        self.emsdk_path = os.environ.get("EMSDK")
        if not self.emsdk_path:
            raise RuntimeError("EMSDK environment variable not set. Please activate Emscripten SDK.")
    
    def get_emscripten_flags(self) -> list:
        """Get Emscripten-specific compiler flags"""
        flags = []
        
        # Optimization flags
        if self.config == "Debug":
            flags.extend(["-g", "-O0"])
        elif self.config == "Release":
            flags.extend(["-O2"])
        elif self.config == "Dist":
            flags.extend(["-O3", "-flto"])
        
        # WebAssembly flags
        flags.extend([
            "-s", "WASM=1",
            "-s", "USE_SDL=2",  # If using SDL
        ])
        
        return flags
    
    def get_emscripten_link_flags(self) -> list:
        """Get Emscripten linker flags"""
        flags = []
        
        # Export functions for JavaScript
        flags.extend([
            "-s", "EXPORTED_FUNCTIONS=['_main']",
            "-s", "EXPORTED_RUNTIME_METHODS=['ccall','cwrap']",
        ])
        
        # Memory settings
        flags.extend([
            "-s", "ALLOW_MEMORY_GROWTH=1",
            "-s", "INITIAL_MEMORY=16777216",  # 16MB
        ])
        
        # Enable pthreads if needed
        # flags.extend(["-s", "USE_PTHREADS=1"])
        
        return flags
    
    def build_wasm(self, sources: list, output: str) -> bool:
        """Build WebAssembly module"""
        
        Reporter.info("Building WebAssembly module...")
        
        # The main compilation system will handle this with emcc/em++
        # This is just configuration
        
        return True
    
    def generate_html_shell(self, output_dir: str) -> bool:
        """Generate HTML shell for running WASM"""
        
        Reporter.info("Generating HTML shell...")
        
        html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Nken Application</title>
    <style>
        body { margin: 0; padding: 0; background: #000; }
        canvas { display: block; margin: 0 auto; }
        #output { color: #fff; font-family: monospace; }
    </style>
</head>
<body>
    <canvas id="canvas"></canvas>
    <div id="output"></div>
    <script>
        var Module = {
            canvas: document.getElementById('canvas'),
            print: function(text) {
                document.getElementById('output').innerHTML += text + '<br>';
            }
        };
    </script>
    <script src="app.js"></script>
</body>
</html>
"""
        
        output_path = Path(output_dir) / "index.html"
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        Reporter.success(f"HTML shell created: {output_path}")
        return True


def configure_emscripten_toolchain() -> Optional[object]:
    """Configure toolchain for Emscripten compilation"""
    
    # Check if Emscripten is available
    emsdk_path = os.environ.get("EMSDK")
    if not emsdk_path:
        Display.error("EMSDK environment variable not set")
        Display.info("Please install and activate Emscripten SDK:")
        Display.info("  https://emscripten.org/docs/getting_started/downloads.html")
        return None
    
    from core.api import Toolchain
    
    # Emscripten uses emcc/em++ which wrap clang
    toolchain = Toolchain(
        name="emscripten",
        compiler="em++",
        cppcompiler="em++",
        ccompiler="emcc",
        archiver="emar",
        linker="em++"
    )
    
    # Emscripten-specific defines
    toolchain.defines = [
        "EMSCRIPTEN",
        "__EMSCRIPTEN__",
        "WEB_BUILD",
    ]
    
    # Standard flags
    toolchain.cxxflags = [
        "-std=c++17",
        "-s", "WASM=1",
    ]
    
    toolchain.ldflags = [
        "-s", "WASM=1",
        "-s", "ALLOW_MEMORY_GROWTH=1",
        "--shell-file", "shell.html",  # Custom shell if needed
    ]
    
    return toolchain


def setup_emscripten_project(project, workspace):
    """Setup a project for Emscripten build"""
    
    # Add Emscripten-specific settings
    project.defines.extend([
        "EMSCRIPTEN",
        "__EMSCRIPTEN__",
    ])
    
    # Output should be .html or .js
    if not project.targetname:
        project.targetname = project.name
    
    # Add post-build to generate HTML shell if needed
    if project.kind.value in ["ConsoleApp", "WindowedApp"]:
        html_gen_cmd = f"echo 'WebAssembly build complete: {project.targetname}.wasm'"
        if html_gen_cmd not in project.postbuildcommands:
            project.postbuildcommands.append(html_gen_cmd)


# Usage example in .nken file:
"""
# In jenga.nken:

# Add Emscripten platform
platforms(["Windows", "Linux", "MacOS", "Emscripten"])

# Configure Emscripten toolchain
with toolchain("emscripten", "em++"):
    defines(["EMSCRIPTEN", "WEB_BUILD"])
    cppcompiler("em++")
    ccompiler("emcc")

# Project configuration
with project("MyWebApp"):
    windowedapp()
    language("C++")
    cppdialect("C++17")
    
    files(["src/**.cpp"])
    includedirs(["src"])
    
    # Select Emscripten toolchain for this project
    toolchain_select("emscripten")
    
    # Platform-specific settings
    with filter("system:Emscripten"):
        defines(["USE_WEBGL"])
        targetname("webapp")
        
    objdir("Build/Obj/%{cfg.buildcfg}/%{prj.name}")
    targetdir("Build/Web/%{cfg.buildcfg}")

# Build command:
# nken.bat build --platform Emscripten --toolchain emscripten
"""
