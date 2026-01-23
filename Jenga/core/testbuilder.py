#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Build System - Test Builder
Automatically generates test main files and configures test projects
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from .api import Project, Workspace, get_current_workspace
from .variables import VariableExpander


class TestBuilder:
    """Handles automatic test project configuration"""
    
    @staticmethod
    def configure_test_project(test_project: Project, parent_project: Project, 
                              config: str, platform: str):
        """Configure a test project automatically"""
        
        if not test_project.is_test or not test_project.parent_project:
            return
        
        # Create variable expander
        workspace = get_current_workspace()
        if not workspace:
            return
            
        expander = VariableExpander(workspace, test_project, config, platform)
        
        # Set target directory for tests
        if not test_project.targetdir:
            test_project.targetdir = f"{parent_project.targetdir}/tests"
        
        # Set target name for tests
        if not test_project.targetname:
            test_project.targetname = f"{parent_project.targetname}_Tests"
        
        # Inherit parent's includedirs
        test_project.includedirs.extend(parent_project.includedirs)
        
        # Inherit parent's language settings
        test_project.language = parent_project.language
        test_project.cppdialect = parent_project.cppdialect
        test_project.cdialect = parent_project.cdialect
        
        # Inherit parent's toolchain
        if parent_project.toolchain and not test_project.toolchain:
            test_project.toolchain = parent_project.toolchain
        
        # Auto-resolve test source files
        if test_project.testfiles:
            # Resolve wildcards relative to parent project location
            base_dir = parent_project.location or workspace.location
            from .variables import resolve_file_list
            
            resolved_files = resolve_file_list(test_project.testfiles, base_dir, expander)
            
            # Filter to keep only source files
            source_extensions = {'.c', '.cpp', '.cc', '.cxx', '.m', '.mm'}
            source_files = [f for f in resolved_files 
                          if Path(f).suffix.lower() in source_extensions]
            
            # Add to project files
            test_project.files.extend(source_files)
            
            # Auto-exclude the parent's main file if specified
            if test_project.testmainfile and test_project.testmainfile not in test_project.excludemainfiles:
                test_project.excludemainfiles.append(test_project.testmainfile)
        
        # Generate test main file if needed
        TestBuilder._generate_test_main(test_project, parent_project, workspace.location)
    
    @staticmethod
    def _generate_test_main(test_project: Project, parent_project: Project, workspace_dir: str):
        """Generate a test main file automatically"""
        
        # Check if we need a test main
        # If test files already include a main function, don't generate one
        if TestBuilder._has_main_function(test_project, workspace_dir):
            return
        
        # Determine template to use
        template_path = test_project.testmaintemplate
        if not template_path:
            # Use default template
            default_template = Path(__file__).parent.parent / "templates" / "Entry.cpp"
            if default_template.exists():
                template_path = str(default_template)
            else:
                # Create minimal template
                template_path = None
        
        # Generate main file
        main_file = Path(test_project.location) / "generated_test_main.cpp"
        
        if template_path and Path(template_path).exists():
            # Copy template
            shutil.copy2(template_path, main_file)
        else:
            # Generate minimal test main
            with open(main_file, 'w') as f:
                f.write("""#include <iostream>
#define CATCH_CONFIG_MAIN
#include "catch.hpp"

// Auto-generated test main
// All test files should include catch.hpp""")
        
        # Add generated main to project files
        if str(main_file) not in test_project.files:
            test_project.files.append(str(main_file))
    
    @staticmethod
    def _has_main_function(project: Project, workspace_dir: str) -> bool:
        """Check if any source file contains a main function"""
        import re
        
        for file_pattern in project.files:
            file_path = Path(file_pattern)
            if not file_path.is_absolute():
                file_path = Path(workspace_dir) / file_path
            
            if file_path.exists() and file_path.is_file():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        # Simple regex to find main function
                        # This could be more sophisticated
                        if re.search(r'\bmain\s*\(', content):
                            return True
                except:
                    continue
        
        return False