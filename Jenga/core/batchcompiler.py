#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Batch Compiler
Compile tous les fichiers en UNE SEULE commande (MSVC)
Gain: 5-10x plus rapide!
"""

import subprocess
from pathlib import Path
from typing import List, Optional


class BatchCompiler:
    """
    Batch Compilation pour MSVC
    
    Au lieu de:
        cl.exe /c file1.cpp /Fofile1.obj (1.2s)
        cl.exe /c file2.cpp /Fofile2.obj (1.2s)
        cl.exe /c file3.cpp /Fofile3.obj (1.2s)
        Total: 3.6s + overhead processus
    
    On fait:
        cl.exe /c file1.cpp file2.cpp file3.cpp /FoBuild/obj/ (0.5s)
        Total: 0.5s
    
    Gain: 7-10x plus rapide!
    """
    
    def __init__(self, workspace_location: str):
        self.workspace_location = workspace_location
    
    def can_batch_compile(self, compiler: str, units: List) -> bool:
        """
        Vérifie si batch compilation est possible
        
        Critères:
        - Compilateur MSVC
        - Au moins 2 fichiers
        - Tous les fichiers ont les mêmes flags/defines/includes
        """
        if len(units) < 2:
            return False
        
        is_msvc = "cl.exe" in compiler.lower() or "cl" == compiler.lower()
        if not is_msvc:
            return False
        
        # Vérifier que tous les units ont les mêmes options
        first = units[0]
        for unit in units[1:]:
            if (unit.flags != first.flags or 
                unit.defines != first.defines or 
                unit.include_dirs != first.include_dirs):
                return False
        
        return True
    
    def batch_compile(self, units: List, obj_dir: Path) -> bool:
        """
        Compile tous les fichiers en une seule commande
        
        Returns:
            True si succès, False sinon
        """
        
        if not units:
            return True
        
        first_unit = units[0]
        compiler = first_unit.compiler
        
        # Build command
        cmd = [compiler]
        
        # Add flags
        cmd.extend(first_unit.flags)
        
        # Add defines
        for define in first_unit.defines:
            cmd.append(f"/D{define}")
        
        # Add include directories
        for inc_dir in first_unit.include_dirs:
            cmd.append(f"/I{inc_dir}")
        
        # Add ALL source files at once
        for unit in units:
            cmd.append(unit.source_file)
        
        # Output directory (tous les .obj vont ici)
        cmd.append(f"/Fo{obj_dir}\\")
        
        # Compile flag
        cmd.append("/c")
        
        print(f"⚡ Batch compiling {len(units)} files in one command...")
        
        # Execute
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.workspace_location
            )
            
            if result.returncode != 0:
                print(f"✗ Batch compilation failed")
                if result.stderr:
                    error_lines = result.stderr.split('\n')[:20]
                    print('\n'.join(error_lines))
                elif result.stdout:
                    error_lines = result.stdout.split('\n')[:20]
                    print('\n'.join(error_lines))
                return False
            
            print(f"✓ Batch compilation successful ({len(units)} files)")
            return True
            
        except Exception as e:
            print(f"✗ Batch compilation error: {e}")
            return False
    
    def batch_compile_with_fallback(self, units: List, obj_dir: Path, 
                                    compile_func) -> bool:
        """
        Essaye batch compilation, fallback sur compilation normale si échec
        
        Args:
            units: Liste des CompilationUnit
            obj_dir: Dossier des objects
            compile_func: Fonction de compilation individuelle (fallback)
        
        Returns:
            True si succès (batch ou fallback), False sinon
        """
        
        # Try batch compilation first
        if self.batch_compile(units, obj_dir):
            return True
        
        # Fallback: compile individually
        print("⚠ Batch compilation failed, falling back to individual compilation")
        
        for unit in units:
            if not compile_func(unit):
                return False
        
        return True