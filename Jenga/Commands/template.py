#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Build System - Template Command
Create projects from templates
"""

import sys
import os
from pathlib import Path
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.display import Display


# Template registry
TEMPLATES = {
    "cli": {
        "name": "CLI Application",
        "description": "Command-line tool with argument parsing",
        "type": "consoleapp",
    },
    "game": {
        "name": "Game Engine",
        "description": "Basic game engine structure with ECS",
        "type": "consoleapp",
    },
    "lib": {
        "name": "Library",
        "description": "Reusable C++ library",
        "type": "staticlib",
    },
    "gui": {
        "name": "GUI Application",
        "description": "GUI app with Dear ImGui",
        "type": "windowedapp",
    },
    "opengl": {
        "name": "OpenGL Application",
        "description": "OpenGL rendering application with GLFW",
        "type": "consoleapp",
    },
    "vulkan": {
        "name": "Vulkan Application",
        "description": "Vulkan rendering application",
        "type": "consoleapp",
    },
    "android": {
        "name": "Android Native",
        "description": "Android native application",
        "type": "androidapp",
    },
}


def execute(args: list) -> int:
    """Main entry point for template command"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Create from templates")
    subparsers = parser.add_subparsers(dest='subcommand', help='Template commands')
    
    # List templates
    list_parser = subparsers.add_parser('list', help='List available templates')
    
    # Create from template
    create_parser = subparsers.add_parser('create', help='Create from template')
    create_parser.add_argument('template', help='Template name')
    create_parser.add_argument('name', help='Project name')
    create_parser.add_argument('--location', default='.', help='Where to create')
    
    parsed = parser.parse_args(args)
    
    if parsed.subcommand == 'list':
        return list_templates()
    elif parsed.subcommand == 'create':
        return create_from_template(parsed.template, parsed.name, parsed.location)
    else:
        parser.print_help()
        return 1


def list_templates() -> int:
    """List all available templates"""
    
    Display.section("Available Templates")
    
    for template_id, template in TEMPLATES.items():
        print(f"\n  {Display.bold(template_id)}")
        print(f"    {template['name']}")
        print(f"    {template['description']}")
    
    print(f"\n{Display.info_prefix()} Use: jenga template create <template> <name>")
    
    return 0


def create_from_template(template_id: str, name: str, location: str) -> int:
    """Create project from template"""
    
    if template_id not in TEMPLATES:
        Display.error(f"Template '{template_id}' not found")
        Display.info("Use 'jenga template list' to see available templates")
        return 1
    
    template = TEMPLATES[template_id]
    
    Display.section(f"Creating: {template['name']}")
    Display.info(f"Name: {name}")
    Display.info(f"Location: {location}")
    
    # Create based on template
    if template_id == 'cli':
        return _create_cli_template(name, location)
    elif template_id == 'game':
        return _create_game_template(name, location)
    elif template_id == 'lib':
        return _create_lib_template(name, location)
    elif template_id == 'gui':
        return _create_gui_template(name, location)
    elif template_id == 'opengl':
        return _create_opengl_template(name, location)
    elif template_id == 'vulkan':
        return _create_vulkan_template(name, location)
    elif template_id == 'android':
        return _create_android_template(name, location)
    
    return 0


def _create_cli_template(name: str, location: str) -> int:
    """Create CLI application template"""
    
    project_dir = Path(location) / name
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Create structure
    (project_dir / "src").mkdir(exist_ok=True)
    (project_dir / "include").mkdir(exist_ok=True)
    
    # main.cpp
    main_cpp = f"""#include <iostream>
#include <string>
#include <vector>

void print_help() {{
    std::cout << "{name} - Command Line Tool\\n";
    std::cout << "\\nUsage: {name} [options] <args>\\n";
    std::cout << "\\nOptions:\\n";
    std::cout << "  -h, --help     Show this help\\n";
    std::cout << "  -v, --version  Show version\\n";
}}

int main(int argc, char** argv) {{
    std::vector<std::string> args(argv + 1, argv + argc);
    
    if (args.empty()) {{
        print_help();
        return 0;
    }}
    
    for (const auto& arg : args) {{
        if (arg == "-h" || arg == "--help") {{
            print_help();
            return 0;
        }}
        
        if (arg == "-v" || arg == "--version") {{
            std::cout << "{name} version 1.0.0\\n";
            return 0;
        }}
    }}
    
    std::cout << "Processing: ";
    for (const auto& arg : args) {{
        std::cout << arg << " ";
    }}
    std::cout << "\\n";
    
    return 0;
}}
"""
    (project_dir / "src" / "main.cpp").write_text(main_cpp)
    
    # .jenga file
    jenga_content = f"""with workspace("{name}"):
    configurations(["Debug", "Release"])
    
    with project("{name}"):
        consoleapp()
        language("C++")
        cppdialect("C++17")
        
        files(["src/**.cpp"])
        includedirs(["include"])
        
        targetdir("Build/Bin/%{{cfg.buildcfg}}")
        
        with filter("configurations:Debug"):
            defines(["DEBUG"])
            optimize("Off")
            symbols("On")
        
        with filter("configurations:Release"):
            defines(["NDEBUG"])
            optimize("Full")
            symbols("Off")
"""
    (project_dir / f"{name.lower()}.jenga").write_text(jenga_content)
    
    # README.md
    readme = f"""# {name}

Command-line tool created with Jenga Build System.

## Build

```bash
jenga build
```

## Run

```bash
jenga run -- --help
```
"""
    (project_dir / "README.md").write_text(readme)
    
    Display.success(f"✓ CLI template created: {project_dir}")
    
    return 0


def _create_game_template(name: str, location: str) -> int:
    """Create game engine template"""
    
    project_dir = Path(location) / name
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Structure
    (project_dir / "src" / "core").mkdir(parents=True, exist_ok=True)
    (project_dir / "src" / "ecs").mkdir(parents=True, exist_ok=True)
    (project_dir / "include" / name.lower()).mkdir(parents=True, exist_ok=True)
    
    # Entity.h
    entity_h = """#pragma once
#include <cstdint>

using Entity = uint32_t;

constexpr Entity NULL_ENTITY = 0;
"""
    (project_dir / "include" / name.lower() / "Entity.h").write_text(entity_h)
    
    # main.cpp
    main_cpp = f"""#include <iostream>
#include "{name.lower()}/Entity.h"

int main() {{
    std::cout << "{name} Game Engine\\n";
    std::cout << "Initializing...\\n";
    
    // Game loop
    bool running = true;
    while (running) {{
        // Update
        
        // Render
        
        // Simple exit after one frame for now
        running = false;
    }}
    
    std::cout << "Shutting down...\\n";
    return 0;
}}
"""
    (project_dir / "src" / "main.cpp").write_text(main_cpp)
    
    # .jenga
    jenga_content = f"""with workspace("{name}"):
    configurations(["Debug", "Release"])
    
    with project("{name}"):
        consoleapp()
        language("C++")
        cppdialect("C++17")
        
        files(["src/**.cpp"])
        includedirs(["include"])
        
        targetdir("Build/Bin/%{{cfg.buildcfg}}")
        
        with filter("configurations:Debug"):
            symbols("On")
        
        with filter("configurations:Release"):
            optimize("Full")
"""
    (project_dir / f"{name.lower()}.jenga").write_text(jenga_content)
    
    Display.success(f"✓ Game template created: {project_dir}")
    
    return 0


def _create_lib_template(name: str, location: str) -> int:
    """Create library template"""
    
    project_dir = Path(location) / name
    project_dir.mkdir(parents=True, exist_ok=True)
    
    (project_dir / "src").mkdir(exist_ok=True)
    (project_dir / "include" / name.lower()).mkdir(parents=True, exist_ok=True)
    (project_dir / "tests").mkdir(exist_ok=True)
    
    # Header
    header = f"""#pragma once

namespace {name.lower()} {{

void initialize();
void shutdown();

}} // namespace {name.lower()}
"""
    (project_dir / "include" / name.lower() / f"{name.lower()}.h").write_text(header)
    
    # Source
    source = f"""#include "{name.lower()}/{name.lower()}.h"
#include <iostream>

namespace {name.lower()} {{

void initialize() {{
    std::cout << "{name} initialized\\n";
}}

void shutdown() {{
    std::cout << "{name} shutdown\\n";
}}

}} // namespace {name.lower()}
"""
    (project_dir / "src" / f"{name.lower()}.cpp").write_text(source)
    
    # .jenga
    jenga_content = f"""with workspace("{name}"):
    configurations(["Debug", "Release"])
    
    # Library
    with project("{name}"):
        staticlib()
        language("C++")
        cppdialect("C++17")
        
        files(["src/**.cpp"])
        includedirs(["include"])
        
        targetdir("Build/Lib/%{{cfg.buildcfg}}")
    
    # Example usage
    with project("{name}Example"):
        consoleapp()
        language("C++")
        cppdialect("C++17")
        
        files(["tests/example.cpp"])
        includedirs(["include"])
        
        dependson(["{name}"])
        
        targetdir("Build/Bin/%{{cfg.buildcfg}}")
"""
    (project_dir / f"{name.lower()}.jenga").write_text(jenga_content)
    
    # Example
    example = f"""#include <{name.lower()}/{name.lower()}.h>

int main() {{
    {name.lower()}::initialize();
    {name.lower()}::shutdown();
    return 0;
}}
"""
    (project_dir / "tests" / "example.cpp").write_text(example)
    
    Display.success(f"✓ Library template created: {project_dir}")
    
    return 0


def _create_gui_template(name: str, location: str) -> int:
    """Create GUI template with ImGui"""
    
    Display.info("Creating GUI template...")
    Display.warning("This template requires Dear ImGui")
    Display.info("Add with: jenga add library imgui")
    
    # Create basic structure
    _create_cli_template(name, location)
    
    Display.success(f"✓ GUI template created (needs ImGui setup)")
    
    return 0


def _create_opengl_template(name: str, location: str) -> int:
    """Create OpenGL template"""
    
    Display.info("Creating OpenGL template...")
    Display.warning("This template requires GLFW and GLAD")
    Display.info("Add with: jenga add library glfw")
    
    _create_cli_template(name, location)
    
    Display.success(f"✓ OpenGL template created (needs GLFW/GLAD setup)")
    
    return 0


def _create_vulkan_template(name: str, location: str) -> int:
    """Create Vulkan template"""
    
    Display.info("Creating Vulkan template...")
    Display.warning("This template requires Vulkan SDK")
    
    _create_cli_template(name, location)
    
    Display.success(f"✓ Vulkan template created (needs Vulkan SDK)")
    
    return 0


def _create_android_template(name: str, location: str) -> int:
    """Create Android template"""
    
    Display.info("Creating Android native template...")
    Display.warning("This template requires Android NDK")
    
    project_dir = Path(location) / name
    project_dir.mkdir(parents=True, exist_ok=True)
    
    (project_dir / "src").mkdir(exist_ok=True)
    
    # Native code
    native_cpp = f"""#include <jni.h>
#include <android/log.h>
#include <string>

#define LOG_TAG "{name}"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

extern "C" JNIEXPORT jstring JNICALL
Java_com_example_{name.lower()}_MainActivity_stringFromJNI(
        JNIEnv* env,
        jobject /* this */) {{
    std::string hello = "Hello from {name}!";
    LOGI("%s", hello.c_str());
    return env->NewStringUTF(hello.c_str());
}}
"""
    (project_dir / "src" / "native.cpp").write_text(native_cpp)
    
    # .jenga
    jenga_content = f"""with workspace("{name}"):
    configurations(["Debug", "Release"])
    platforms(["Android"])
    
    # Android paths (configure these)
    androidsdkpath("/path/to/android-sdk")
    androidndkpath("/path/to/android-ndk")
    
    with project("{name}"):
        androidapp()
        language("C++")
        cppdialect("C++17")
        
        files(["src/**.cpp"])
        
        # Android config
        androidapplicationid("com.example.{name.lower()}")
        androidminsdk(21)
        androidtargetsdk(33)
        
        targetdir("Build/Android/%{{cfg.buildcfg}}")
"""
    (project_dir / f"{name.lower()}.jenga").write_text(jenga_content)
    
    Display.success(f"✓ Android template created: {project_dir}")
    Display.info("\nNext steps:")
    print("  1. Configure Android SDK/NDK paths in .jenga")
    print("  2. jenga build --platform Android")
    print("  3. jenga package --platform Android --type apk")
    
    return 0


if __name__ == "__main__":
    sys.exit(execute(sys.argv[1:]))
