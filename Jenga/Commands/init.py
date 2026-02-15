#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Init command – Crée un nouveau workspace Jenga.
Alias : workspace
Peut fonctionner en mode interactif ou avec arguments directs.
"""

import argparse
import sys
import re
from pathlib import Path
from typing import List, Optional

from ..Utils import Colored, FileSystem, Display
from ..Core.Loader import Loader
from ..Core import Api


class InitCommand:
    """jenga workspace [NAME] [--path DIR] [--configs LIST] [--oses LIST] [--interactive]"""

    @staticmethod
    def Execute(args: List[str]) -> int:
        parser = argparse.ArgumentParser(
            prog="jenga workspace",
            description="Create a new Jenga workspace.",
            epilog="Examples:\n"
                   "  jenga workspace MyGame\n"
                   "  jenga workspace --interactive\n"
                   "  jenga workspace --path ./projects/MyLib"
        )
        parser.add_argument("name", nargs="?", help="Workspace name")
        parser.add_argument("--path", default=".", help="Directory where to create the workspace (default: current)")
        parser.add_argument("--configs", default="Debug,Release", help="Comma-separated build configurations (default: Debug,Release)")
        parser.add_argument("--oses", default="Windows,Linux,macOS", help="Comma-separated target OSes (default: Windows,Linux,macOS)")
        parser.add_argument("--archs", default="x86_64", help="Comma-separated target architectures (default: x86_64)")
        parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
        parser.add_argument("--no-interactive", action="store_true", help="Non-interactive mode (default if arguments provided)")
        parsed = parser.parse_args(args)

        # Mode interactif si demandé ou si aucun nom fourni
        interactive = parsed.interactive or (parsed.name is None and not parsed.no_interactive)

        if interactive:
            return InitCommand._RunInteractive(parsed)
        else:
            if not parsed.name:
                Colored.PrintError("Workspace name required. Use --interactive or provide a name.")
                return 1
            return InitCommand._RunDirect(parsed)

    @staticmethod
    def _RunDirect(args) -> int:
        """Création directe avec arguments."""
        workspace_root = Path(args.path).resolve()
        workspace_name = args.name

        # Vérifier si le répertoire existe déjà
        if not workspace_root.exists():
            FileSystem.MakeDirectory(workspace_root)
        else:
            # Vérifier s'il y a déjà un workspace
            existing = FileSystem.FindWorkspaceEntry(workspace_root)
            if existing:
                Colored.PrintError(f"A workspace already exists at {existing.parent}")
                return 1

        # Générer le fichier .jenga
        entry_file = workspace_root / f"{workspace_name}.jenga"
        content = InitCommand._GenerateWorkspaceContent(
            name=workspace_name,
            configs=args.configs.split(','),
            oses=args.oses.split(','),
            archs=args.archs.split(','),
        )
        FileSystem.WriteFile(entry_file, content)
        Colored.PrintSuccess(f"Workspace '{workspace_name}' created at {entry_file}")
        return 0

    @staticmethod
    def _RunInteractive(args) -> int:
        """Création interactive (questions/réponses)."""
        Display.PrintBanner()
        Display.Section("Create a new Jenga workspace")

        # 1. Nom du workspace
        default_name = Path.cwd().name
        name = Display.Prompt("Workspace name", default=default_name)
        if not name:
            name = default_name

        # 2. Chemin
        default_path = "."
        path = Display.Prompt("Directory to create workspace", default=default_path)
        workspace_root = Path(path).resolve()

        # 3. Configurations
        all_configs = ["Debug", "Release", "Profile", "Distribution"]
        configs = Display.PromptMultiChoice(
            "Build configurations",
            choices=all_configs,
            defaults=["Debug", "Release"]
        )

        # 4. OS cibles
        all_oses = ["Windows", "Linux", "macOS", "Android", "iOS", "Web"]
        default_os = []
        import platform
        host = platform.system()
        if host == "Windows":
            default_os = ["Windows"]
        elif host == "Linux":
            default_os = ["Linux"]
        elif host == "Darwin":
            default_os = ["macOS"]
        oses = Display.PromptMultiChoice(
            "Target operating systems",
            choices=all_oses,
            defaults=default_os
        )

        # 5. Architectures
        all_archs = ["x86_64", "x86", "arm64", "arm", "wasm32"]
        archs = Display.PromptMultiChoice(
            "Target architectures",
            choices=all_archs,
            defaults=["x86_64"]
        )

        # 6. Compiler preference
        compilers = ["Auto-detect", "GCC", "Clang", "MSVC", "Zig"]
        compiler = Display.PromptChoice(
            "Preferred compiler",
            choices=compilers,
            default="Auto-detect"
        )

        # 7. C++ standard
        standards = ["C++17", "C++20", "C++23", "C11", "C17"]
        standard = Display.PromptChoice(
            "Language standard",
            choices=standards,
            default="C++17"
        )

        # 8. Create initial project?
        create_project = Display.PromptYesNo("Create an initial project in this workspace?", default=True)
        project_name = None
        project_kind = None
        if create_project:
            project_name = Display.Prompt("Project name", default=name)
            kind_choices = ["console", "windowed", "static", "shared"]
            project_kind = Display.PromptChoice(
                "Project type",
                choices=kind_choices,
                default="console"
            )

        # 9. Unit test framework
        use_tests = Display.PromptYesNo("Enable unit testing (Unitest)?", default=False)

        # Summary with structure preview
        Display.Section("Summary")
        print(f"  Workspace:    {Colored.Colorize(name, bold=True, color='cyan')}")
        print(f"  Path:         {workspace_root}")
        print(f"  Configs:      {', '.join(configs)}")
        print(f"  OSes:         {', '.join(oses)}")
        print(f"  Archs:        {', '.join(archs)}")
        print(f"  Compiler:     {compiler}")
        print(f"  Standard:     {standard}")
        if project_name:
            print(f"  Project:      {project_name} ({project_kind})")
        print(f"  Unit tests:   {'Yes' if use_tests else 'No'}")

        # Directory structure preview
        print(f"\n  Directory structure:")
        print(f"  {workspace_root.name}/")
        print(f"  +-- {name}.jenga")
        if project_name:
            print(f"  +-- src/")
            if standard.startswith("C++"):
                print(f"  |   +-- main.cpp")
            else:
                print(f"  |   +-- main.c")
            print(f"  +-- include/")
        if use_tests:
            print(f"  +-- tests/")

        print()
        if not Display.PromptYesNo("Create workspace?", default=True):
            Colored.PrintInfo("Cancelled.")
            return 0

        # Create workspace
        parsed = argparse.Namespace(
            name=name,
            path=str(workspace_root),
            configs=','.join(configs),
            oses=','.join(oses),
            archs=','.join(archs),
        )
        result = InitCommand._RunDirect(parsed)
        if result != 0:
            return result

        # Optionally add initial project
        if project_name:
            from .Create import CreateCommand
            proj_args = argparse.Namespace(
                name=project_name,
                kind=project_kind,
                lang="C++" if standard.startswith("C++") else "C",
                location=".",
                dialect=standard,
            )
            entry_file = workspace_root / f"{name}.jenga"
            CreateCommand._CreateProjectDirect(proj_args, entry_file)

        Display.Success(f"Workspace '{name}' is ready!")
        Display.Info(f"Next: cd {workspace_root} && Jenga build")
        return 0

    @staticmethod
    def _GenerateWorkspaceContent(name: str, configs: List[str], oses: List[str], archs: List[str]) -> str:
        """Génère le contenu du fichier .jenga."""
        # Convertir les noms d'OS en énumérations TargetOS
        os_mapping = {
            'Windows': 'TargetOS.WINDOWS',
            'Linux': 'TargetOS.LINUX',
            'macOS': 'TargetOS.MACOS',
            'Android': 'TargetOS.ANDROID',
            'iOS': 'TargetOS.IOS',
            'Web': 'TargetOS.WEB',
            'XboxOne': 'TargetOS.XBOX_ONE',
            'XboxSeries': 'TargetOS.XBOX_SERIES',
            'Switch': 'TargetOS.SWITCH',
        }
        os_list = [os_mapping.get(o, f'"{o}"') for o in oses]

        # Architectures
        arch_mapping = {
            'x86': 'TargetArch.X86',
            'x86_64': 'TargetArch.X86_64',
            'arm': 'TargetArch.ARM',
            'arm64': 'TargetArch.ARM64',
            'wasm32': 'TargetArch.WASM32',
        }
        arch_list = [arch_mapping.get(a, f'"{a}"') for a in archs]

        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# {name} – Jenga Workspace
# Generated by `jenga workspace` on {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

from Jenga import *

with workspace("{name}"):
    configurations({configs!r})
    targetoses([{', '.join(os_list)}])
    targetarchs([{', '.join(arch_list)}])
    
    # Default toolchain (auto-detected)
    # usetoolchain("host-gcc")
    
    # Uncomment to use Unitest testing framework
    # with unitest() as u:
    #     u.Precompiled()
    
    # Add your projects here
    # with project("MyApp"):
    #     consoleapp()
    #     language("C++")
    #     files(["src/**.cpp"])
'''
