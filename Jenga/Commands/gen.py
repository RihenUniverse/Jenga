#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gen command – Génère des fichiers projet pour différents outils de build.
Support : CMake (CMakeLists.txt), Makefile, Visual Studio 2022, Xcode (partiel).
"""

import argparse
import sys
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List

from ..Core.Loader import Loader
from ..Core.Cache import Cache
from ..Core.Builder import Builder
from ..Core.Platform import Platform
from ..Utils import FileSystem, Colored, Display
from ..Core import Api


class GenCommand:
    """jenga gen [--cmake] [--makefile] [--vs2022] [--xcode] [--output DIR] [--no-cache]"""

    @staticmethod
    def Execute(args: List[str]) -> int:
        parser = argparse.ArgumentParser(prog="jenga gen", description="Generate IDE project files.")
        parser.add_argument("--cmake", action="store_true", help="Generate CMakeLists.txt")
        parser.add_argument("--makefile", action="store_true", help="Generate Makefile")
        parser.add_argument("--vs2022", action="store_true", help="Generate Visual Studio 2022 solution")
        parser.add_argument("--xcode", action="store_true", help="Generate Xcode project (experimental)")
        parser.add_argument("--output", "-o", default=".", help="Output directory")
        parser.add_argument("--no-cache", action="store_true", help="Reload workspace without cache")
        parser.add_argument("--jenga-file", help="Path to the workspace .jenga file (default: auto-detected)")
        parsed = parser.parse_args(args)

        if not (parsed.cmake or parsed.makefile or parsed.vs2022 or parsed.xcode):
            Colored.PrintError("No generator specified. Use --cmake, --makefile, --vs2022 or --xcode.")
            return 1

        # Déterminer le répertoire de travail (workspace root)
        workspace_root = Path.cwd()
        if parsed.jenga_file:
            entry_file = Path(parsed.jenga_file).resolve()
            if not entry_file.exists():
                Colored.PrintError(f"Jenga file not found: {entry_file}")
                return 1
        else:
            entry_file = FileSystem.FindWorkspaceEntry(workspace_root)
            if not entry_file:
                Colored.PrintError("No .jenga workspace file found.")
                return 1
        workspace_root = entry_file.parent

        # Charger le workspace
        loader = Loader(verbose=False)
        cache = Cache(workspace_root)
        if parsed.no_cache:
            workspace = loader.LoadWorkspace(str(entry_file))
        else:
            workspace = cache.LoadWorkspace(entry_file, loader)
            if workspace is None:
                workspace = loader.LoadWorkspace(str(entry_file))

        if workspace is None:
            Colored.PrintError("Failed to load workspace.")
            return 1

        output_dir = Path(parsed.output).resolve()
        FileSystem.MakeDirectory(output_dir)

        if parsed.cmake:
            GenCommand._GenerateCMake(workspace, output_dir)
        if parsed.makefile:
            GenCommand._GenerateMakefile(workspace, output_dir)
        if parsed.vs2022:
            GenCommand._GenerateVS2022(workspace, output_dir)
        if parsed.xcode:
            GenCommand._GenerateXcode(workspace, output_dir)

        return 0

    # -----------------------------------------------------------------------
    # Générateur CMake
    # -----------------------------------------------------------------------

    @staticmethod
    def _GenerateCMake(workspace, output_dir: Path):
        """Génère un CMakeLists.txt à la racine du workspace."""
        cmake_path = output_dir / "CMakeLists.txt"
        with open(cmake_path, 'w', encoding='utf-8') as f:
            f.write(f"cmake_minimum_required(VERSION 3.15)\n")
            f.write(f"project({workspace.name} LANGUAGES C CXX ASM OBJC OBJCXX)\n\n")

            # Options de configuration
            f.write("# Build configurations\n")
            for cfg in workspace.configurations:
                f.write(f"set(CMAKE_CONFIGURATION_TYPES \"{' '.join(workspace.configurations)}\" CACHE STRING \"\" FORCE)\n")
            f.write("\n")

            # Définir les répertoires de sortie par défaut (peuvent être surchargés)
            f.write("# Output directories\n")
            f.write(f"set(JENGA_OUTPUT_BIN \"${{CMAKE_BINARY_DIR}}/Bin/${{CMAKE_BUILD_TYPE}}\")\n")
            f.write(f"set(JENGA_OUTPUT_LIB \"${{CMAKE_BINARY_DIR}}/Lib/${{CMAKE_BUILD_TYPE}}\")\n")
            f.write(f"set(JENGA_OUTPUT_OBJ \"${{CMAKE_BINARY_DIR}}/Obj/${{CMAKE_BUILD_TYPE}}\")\n\n")

            # Ajouter tous les projets
            for proj_name, proj in workspace.projects.items():
                if proj_name.startswith('__'):
                    continue
                GenCommand._WriteCMakeProject(f, proj_name, proj, workspace)

        Colored.PrintSuccess(f"CMakeLists.txt generated: {cmake_path}")

    @staticmethod
    def _WriteCMakeProject(f, name: str, proj, workspace):
        """Écrit un projet CMake (add_executable ou add_library)."""
        # Déterminer le type
        if proj.kind in (Api.ProjectKind.CONSOLE_APP, Api.ProjectKind.WINDOWED_APP, Api.ProjectKind.TEST_SUITE):
            cmd = "add_executable"
        elif proj.kind == Api.ProjectKind.STATIC_LIB:
            cmd = "add_library"
        elif proj.kind == Api.ProjectKind.SHARED_LIB:
            cmd = "add_library"
        else:
            return

        f.write(f"\n# Project: {name}\n")
        # Collecter les fichiers sources
        src_exts = Builder.GetSourceFileExtensions(proj.language)
        hdr_exts = Builder.GetHeaderFileExtensions()
        src_files = []
        hdr_files = []
        base_dir = Path(proj.location) if proj.location else Path.cwd()

        for pattern in proj.files:
            matched = FileSystem.ListFiles(base_dir, pattern, recursive=True, fullPath=True)
            for m in matched:
                p = Path(m)
                ext = p.suffix.lower()
                if ext in src_exts:
                    src_files.append(str(p.relative_to(base_dir)))
                elif ext in hdr_exts:
                    hdr_files.append(str(p.relative_to(base_dir)))

        # Écrire la commande
        f.write(f"{cmd}({name}\n")
        for sf in src_files:
            f.write(f"    {sf}\n")
        f.write(")\n")

        # Headers (pour IDE)
        if hdr_files:
            f.write(f"target_sources({name} PRIVATE\n")
            for hf in hdr_files:
                f.write(f"    {hf}\n")
            f.write(")\n")

        # Includes
        if proj.includeDirs:
            f.write(f"target_include_directories({name} PRIVATE\n")
            for inc in proj.includeDirs:
                f.write(f"    {inc}\n")
            f.write(")\n")

        # Définitions
        if proj.defines:
            f.write(f"target_compile_definitions({name} PRIVATE\n")
            for d in proj.defines:
                f.write(f"    {d}\n")
            f.write(")\n")

        # Librairies
        if proj.links:
            f.write(f"target_link_libraries({name} PRIVATE\n")
            for lib in proj.links:
                f.write(f"    {lib}\n")
            f.write(")\n")

        # Propriétés spécifiques
        if proj.kind == Api.ProjectKind.SHARED_LIB:
            f.write(f"set_target_properties({name} PROPERTIES PREFIX \"\")\n")  # évite lib en préfixe sur Windows

        # Langage et standard
        std_flag = ""
        if proj.language == Api.Language.CPP:
            std_flag = f"set_property(TARGET {name} PROPERTY CXX_STANDARD {proj.cppdialect.replace('C++', '')})\n"
        elif proj.language == Api.Language.C:
            std_flag = f"set_property(TARGET {name} PROPERTY C_STANDARD {proj.cdialect.replace('C', '')})\n"
        f.write(std_flag)

        # Répertoires de sortie
        if proj.kind in (Api.ProjectKind.CONSOLE_APP, Api.ProjectKind.WINDOWED_APP, Api.ProjectKind.TEST_SUITE):
            f.write(f"set_target_properties({name} PROPERTIES RUNTIME_OUTPUT_DIRECTORY \"${{JENGA_OUTPUT_BIN}}/{name}\")\n")
        elif proj.kind == Api.ProjectKind.SHARED_LIB:
            f.write(f"set_target_properties({name} PROPERTIES LIBRARY_OUTPUT_DIRECTORY \"${{JENGA_OUTPUT_LIB}}/{name}\")\n")
            f.write(f"set_target_properties({name} PROPERTIES RUNTIME_OUTPUT_DIRECTORY \"${{JENGA_OUTPUT_BIN}}/{name}\")\n")  # DLL sur Windows
        elif proj.kind == Api.ProjectKind.STATIC_LIB:
            f.write(f"set_target_properties({name} PROPERTIES ARCHIVE_OUTPUT_DIRECTORY \"${{JENGA_OUTPUT_LIB}}/{name}\")\n")

        f.write("\n")

    # -----------------------------------------------------------------------
    # Générateur Makefile (simple)
    # -----------------------------------------------------------------------

    @staticmethod
    def _GenerateMakefile(workspace, output_dir: Path):
        """Génère un Makefile basique pour le workspace."""
        make_path = output_dir / "Makefile"
        with open(make_path, 'w', encoding='utf-8') as f:
            f.write("# Makefile generated by Jenga\n\n")
            f.write(f"WORKSPACE = {workspace.name}\n")
            f.write("CONFIG ?= Debug\n")
            f.write("PLATFORM ?= $(shell uname -s)\n\n")

            f.write("all: $(WORKSPACE)\n\n")
            f.write(f"$(WORKSPACE):\n")
            f.write("\t@echo \"Building workspace $(WORKSPACE) with config=$(CONFIG), platform=$(PLATFORM)\"\n")
            f.write("\t@jenga build --config $(CONFIG) --platform $(PLATFORM)\n\n")

            f.write("clean:\n")
            f.write("\t@jenga clean --config $(CONFIG) --platform $(PLATFORM)\n\n")

            f.write("rebuild: clean all\n\n")
            f.write("run:\n")
            f.write("\t@jenga run --config $(CONFIG) --platform $(PLATFORM)\n\n")

            f.write("test:\n")
            f.write("\t@jenga test --config $(CONFIG) --platform $(PLATFORM)\n\n")

            f.write(".PHONY: all clean rebuild run test\n")

        Colored.PrintSuccess(f"Makefile generated: {make_path}")

    # -----------------------------------------------------------------------
    # Générateur Visual Studio 2022 (amélioré)
    # -----------------------------------------------------------------------

    @staticmethod
    def _GenerateVS2022(workspace, output_dir: Path):
        """Génère une solution Visual Studio 2022 avec tous les projets."""
        sln_path = output_dir / f"{workspace.name}.sln"
        vs_version = "17.0"

        # Générer un GUID unique pour la solution
        sln_guid = "{" + str(uuid.uuid4()).upper() + "}"

        with open(sln_path, 'w') as f:
            f.write("\n")
            f.write("Microsoft Visual Studio Solution File, Format Version 12.00\n")
            f.write(f"# Visual Studio Version {vs_version}\n")
            f.write("VisualStudioVersion = 17.0.31903.59\n")
            f.write("MinimumVisualStudioVersion = 10.0.40219.1\n")

            # Projets
            project_guids = {}
            for proj_name, proj in workspace.projects.items():
                if proj_name.startswith('__'):
                    continue
                proj_guid = "{" + str(uuid.uuid4()).upper() + "}"
                project_guids[proj_name] = proj_guid
                proj_path = f"{proj_name}.vcxproj"
                f.write(f'Project("{{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}}") = "{proj_name}", "{proj_path}", "{proj_guid}"\n')
                f.write("EndProject\n")

            # Global
            f.write("Global\n")
            f.write("\tGlobalSection(SolutionConfigurationPlatforms) = preSolution\n")
            for config in workspace.configurations:
                f.write(f"\t\t{config}|x64 = {config}|x64\n")
                f.write(f"\t\t{config}|Win32 = {config}|Win32\n")
                f.write(f"\t\t{config}|ARM64 = {config}|ARM64\n")
            f.write("\tEndGlobalSection\n")

            f.write("\tGlobalSection(ProjectConfigurationPlatforms) = postSolution\n")
            for proj_name, proj_guid in project_guids.items():
                for config in workspace.configurations:
                    for plat in ["x64", "Win32", "ARM64"]:
                        f.write(f"\t\t{proj_guid}.{config}|{plat}.ActiveCfg = {config}|{plat}\n")
                        f.write(f"\t\t{proj_guid}.{config}|{plat}.Build.0 = {config}|{plat}\n")
            f.write("\tEndGlobalSection\n")
            f.write("EndGlobal\n")

        # Générer les .vcxproj
        for proj_name, proj in workspace.projects.items():
            if proj_name.startswith('__'):
                continue
            GenCommand._GenerateVCXProj(proj, output_dir / f"{proj_name}.vcxproj", workspace)

        Colored.PrintSuccess(f"Visual Studio 2022 solution generated: {sln_path}")

    @staticmethod
    def _GenerateVCXProj(project, proj_path: Path, workspace):
        """Génère un fichier .vcxproj complet."""
        from xml.etree.ElementTree import Element, SubElement, tostring
        import xml.dom.minidom

        root = Element("Project", DefaultTargets="Build", xmlns="http://schemas.microsoft.com/developer/msbuild/2003")

        # Configurations
        ig = SubElement(root, "ItemGroup", Label="ProjectConfigurations")
        for config in workspace.configurations:
            for plat in ["x64", "Win32", "ARM64"]:
                pc = SubElement(ig, "ProjectConfiguration", Include=f"{config}|{plat}")
                SubElement(pc, "Configuration").text = config
                SubElement(pc, "Platform").text = plat

        # Globals
        pg = SubElement(root, "PropertyGroup", Label="Globals")
        SubElement(pg, "ProjectGuid").text = "{" + str(uuid.uuid4()).upper() + "}"
        SubElement(pg, "Keyword").text = "Win32Proj"
        SubElement(pg, "RootNamespace").text = project.name
        SubElement(pg, "WindowsTargetPlatformVersion").text = "10.0"

        # Default properties
        SubElement(root, "Import", Project="$(VCTargetsPath)\\Microsoft.Cpp.Default.props")

        # Configuration groups
        for config in workspace.configurations:
            for plat in ["x64", "Win32", "ARM64"]:
                pg = SubElement(root, "PropertyGroup", Condition=f"'$(Configuration)|$(Platform)'=='{config}|{plat}'", Label="Configuration")
                SubElement(pg, "ConfigurationType").text = GenCommand._GetVSConfigurationType(project.kind)
                SubElement(pg, "UseDebugLibraries").text = "true" if config == "Debug" else "false"
                SubElement(pg, "PlatformToolset").text = "v143"
                if project.kind == Api.ProjectKind.SHARED_LIB:
                    SubElement(pg, "LinkIncremental").text = "false"

        SubElement(root, "Import", Project="$(VCTargetsPath)\\Microsoft.Cpp.props")

        # Include paths
        ig_inc = SubElement(root, "ItemDefinitionGroup")
        cl = SubElement(ig_inc, "ClCompile")
        inc_paths = SubElement(cl, "AdditionalIncludeDirectories")
        all_includes = project.includeDirs[:]
        all_includes.append("%(AdditionalIncludeDirectories)")
        inc_paths.text = ";".join(all_includes)

        # Définitions
        if project.defines:
            defs = SubElement(cl, "PreprocessorDefinitions")
            defs.text = ";".join(project.defines + ["%(PreprocessorDefinitions)"])

        # Standard
        if project.language == Api.Language.CPP:
            SubElement(cl, "LanguageStandard").text = "stdcpp" + project.cppdialect.replace("C++", "")
        elif project.language == Api.Language.C:
            SubElement(cl, "LanguageStandard_C").text = "stdc" + project.cdialect.replace("C", "")

        # Optimisation
        opt = project.optimize.value if hasattr(project.optimize, 'value') else project.optimize
        if opt == "Off":
            SubElement(cl, "Optimization").text = "Disabled"
        elif opt == "Size":
            SubElement(cl, "Optimization").text = "MinSpace"
        elif opt == "Speed":
            SubElement(cl, "Optimization").text = "MaxSpeed"
        elif opt == "Full":
            SubElement(cl, "Optimization").text = "Full"

        # Fichiers sources
        src_exts = Builder.GetSourceFileExtensions(project.language)
        hdr_exts = Builder.GetHeaderFileExtensions()

        base_dir = Path(project.location) if project.location else Path.cwd()
        for pattern in project.files:
            matched = FileSystem.ListFiles(base_dir, pattern, recursive=True, fullPath=True)
            for f in matched:
                rel = Path(f).relative_to(base_dir)
                ext = Path(f).suffix.lower()
                if ext in src_exts:
                    ig_src = SubElement(root, "ItemGroup")
                    SubElement(ig_src, "ClCompile", Include=str(rel))
                elif ext in hdr_exts:
                    ig_hdr = SubElement(root, "ItemGroup")
                    SubElement(ig_hdr, "ClInclude", Include=str(rel))

        # Link
        if project.links:
            ig_link = SubElement(root, "ItemDefinitionGroup")
            link = SubElement(ig_link, "Link")
            deps = SubElement(link, "AdditionalDependencies")
            deps.text = ";".join([f"{lib}.lib" for lib in project.links] + ["%(AdditionalDependencies)"])

        SubElement(root, "Import", Project="$(VCTargetsPath)\\Microsoft.Cpp.targets")

        # Pretty print
        xml_str = tostring(root, encoding='utf-8')
        dom = xml.dom.minidom.parseString(xml_str)
        pretty = dom.toprettyxml(indent="  ")
        proj_path.write_text(pretty, encoding='utf-8')

    @staticmethod
    def _GetVSConfigurationType(kind) -> str:
        """Convertit ProjectKind en type Visual Studio."""
        from ..Core.Api import ProjectKind
        if kind in (ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP, ProjectKind.TEST_SUITE):
            return "Application"
        elif kind == ProjectKind.STATIC_LIB:
            return "StaticLibrary"
        elif kind == ProjectKind.SHARED_LIB:
            return "DynamicLibrary"
        else:
            return "Application"

    @staticmethod
    def _GenerateXcode(workspace, output_dir: Path):
        """Génère un projet Xcode (placeholder)."""
        Colored.PrintWarning("Xcode generator is not yet implemented.")
