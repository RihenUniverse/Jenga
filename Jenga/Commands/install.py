#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Install Command
Install compilers and configure toolchains automatically
"""

import sys
import os
import platform
import subprocess
import urllib.request
import zipfile
import tarfile
import tempfile
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.display import Display
from utils.reporter import Reporter

# URLs pour les téléchargements
MSYS2_URL = "https://github.com/msys2/msys2-installer/releases/latest/download/msys2-x86_64-latest.sfx.exe"
LLVM_WINDOWS_URL = "https://github.com/llvm/llvm-project/releases/latest/download/LLVM-{version}-win64.exe"
ANDROID_NDK_URL = "https://dl.google.com/android/repository/android-ndk-{version}-{platform}.zip"
EMSDK_URL = "https://github.com/emscripten-core/emsdk/archive/refs/heads/main.zip"

class ToolManager:
    """Gestionnaire d'outils et de toolchains avec MSYS2 par défaut sur Windows"""
    
    def __init__(self):
        self.system = platform.system()
        self.is_windows = self.system == "Windows"
        self.is_linux = self.system == "Linux"
        self.is_macos = self.system == "Darwin"
        self.tools_dir = self._get_tools_dir()
        
    def _get_tools_dir(self) -> Path:
        """Obtenir le répertoire des outils installés"""
        tools_dir = Path.home() / ".nken" / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)
        return tools_dir
    
    def install_and_configure(self, tools: List[str]) -> Dict[str, bool]:
        """Installer des outils et configurer les toolchains"""
        results = {}
        
        for tool in tools:
            Display.info(f"Installation et configuration de {tool}...")
            
            if tool == "msys2":
                results[tool] = self._install_msys2()
            elif tool == "mingw64":
                results[tool] = self._install_mingw64()
            elif tool == "ucrt64":
                results[tool] = self._install_ucrt64()
            elif tool == "clang64":
                results[tool] = self._install_clang64()
            elif tool == "llvm":
                results[tool] = self._install_llvm()
            elif tool == "gcc":
                results[tool] = self._install_gcc()
            elif tool == "clang":
                results[tool] = self._install_clang()
            elif tool == "android-ndk":
                results[tool] = self._install_android_ndk()
            elif tool == "emscripten":
                results[tool] = self._install_emscripten()
            elif tool == "visualstudio":
                results[tool] = self._install_visual_studio()
            elif tool == "xcode":
                results[tool] = self._install_xcode()
            else:
                Display.warning(f"Outil non supporté: {tool}")
                results[tool] = False
        
        return results
    
    def _install_msys2(self) -> bool:
        """Installer MSYS2 sur Windows"""
        if not self.is_windows:
            Display.warning("MSYS2 n'est disponible que sur Windows")
            return False
        
        try:
            Display.info("Téléchargement de MSYS2...")
            
            # Télécharger l'installateur
            temp_dir = tempfile.mkdtemp()
            installer_path = Path(temp_dir) / "msys2.exe"
            
            urllib.request.urlretrieve(MSYS2_URL, installer_path)
            
            # Déterminer le répertoire d'installation
            install_dir = Path("C:/msys64")
            if install_dir.exists():
                Display.info(f"MSYS2 déjà installé dans: {install_dir}")
            else:
                Display.info("Installation de MSYS2...")
                Display.info("Lancez l'installateur et suivez les instructions.")
                Display.info(f"Répertoire d'installation recommandé: {install_dir}")
                
                # Lancer l'installateur
                subprocess.run([str(installer_path)], shell=True)
                
                # Attendre que l'installation soit terminée
                import time
                for i in range(30):  # Attendre jusqu'à 30 secondes
                    if install_dir.exists():
                        break
                    time.sleep(1)
            
            if not install_dir.exists():
                Display.error("MSYS2 n'a pas été installé correctement")
                return False
            
            # Configurer les toolchains MSYS2
            self._configure_msys2_toolchains(str(install_dir))
            
            # Ajouter au PATH
            self._add_msys2_to_path(str(install_dir))
            
            Display.success(f"MSYS2 installé dans: {install_dir}")
            
            # Proposer d'installer les compilateurs
            Display.info("\nPour installer les compilateurs, ouvrez MSYS2 et exécutez:")
            Display.info("1. Mise à jour: pacman -Syu")
            Display.info("2. Installer UCRT64 (recommandé): pacman -S mingw-w64-ucrt-x86_64-gcc")
            Display.info("3. Installer MINGW64: pacman -S mingw-w64-x86_64-gcc")
            Display.info("4. Installer Clang64: pacman -S mingw-w64-clang-x86_64-gcc")
            
            return True
            
        except Exception as e:
            Display.error(f"Erreur lors de l'installation de MSYS2: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _install_ucrt64(self) -> bool:
        """Installer UCRT64 via MSYS2"""
        if not self.is_windows:
            Display.warning("UCRT64 n'est disponible que sur Windows")
            return False
        
        # Vérifier si MSYS2 est installé
        msys2_dirs = ["C:/msys64", "C:/msys32"]
        msys2_dir = None
        
        for dir_path in msys2_dirs:
            if Path(dir_path).exists():
                msys2_dir = Path(dir_path)
                break
        
        if not msys2_dir:
            Display.error("MSYS2 n'est pas installé. Installez d'abord MSYS2:")
            Display.info("  jenga install msys2")
            return False
        
        Display.info("Installation de UCRT64 via MSYS2...")
        
        try:
            # Essayer d'installer via pacman
            pacman_path = msys2_dir / "usr" / "bin" / "pacman.exe"
            
            if pacman_path.exists():
                # Mise à jour
                Display.info("Mise à jour des paquets...")
                update_cmd = [str(pacman_path), "-Syu", "--noconfirm"]
                subprocess.run(update_cmd, capture_output=True, text=True)
                
                # Installer UCRT64
                Display.info("Installation de mingw-w64-ucrt-x86_64-gcc...")
                install_cmd = [
                    str(pacman_path), "-S", 
                    "--noconfirm",
                    "mingw-w64-ucrt-x86_64-gcc",
                    "mingw-w64-ucrt-x86_64-gdb",
                    "mingw-w64-ucrt-x86_64-make"
                ]
                
                result = subprocess.run(
                    install_cmd,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    # Configurer la toolchain UCRT64
                    self._configure_ucrt64_toolchain(str(msys2_dir))
                    
                    Display.success("UCRT64 installé avec succès")
                    return True
                else:
                    Display.error("Échec de l'installation de UCRT64")
                    return False
            else:
                Display.error("Pacman non trouvé dans MSYS2")
                return False
                
        except Exception as e:
            Display.error(f"Erreur lors de l'installation de UCRT64: {e}")
            return False
    
    def _install_mingw64(self) -> bool:
        """Installer MINGW64 via MSYS2"""
        if not self.is_windows:
            Display.warning("MINGW64 n'est disponible que sur Windows")
            return False
        
        # Vérifier si MSYS2 est installé
        msys2_dirs = ["C:/msys64", "C:/msys32"]
        msys2_dir = None
        
        for dir_path in msys2_dirs:
            if Path(dir_path).exists():
                msys2_dir = Path(dir_path)
                break
        
        if not msys2_dir:
            Display.error("MSYS2 n'est pas installé. Installez d'abord MSYS2:")
            Display.info("  jenga install msys2")
            return False
        
        Display.info("Installation de MINGW64 via MSYS2...")
        
        try:
            pacman_path = msys2_dir / "usr" / "bin" / "pacman.exe"
            
            if pacman_path.exists():
                # Installer MINGW64
                install_cmd = [
                    str(pacman_path), "-S", 
                    "--noconfirm",
                    "mingw-w64-x86_64-gcc",
                    "mingw-w64-x86_64-gdb",
                    "mingw-w64-x86_64-make"
                ]
                
                result = subprocess.run(
                    install_cmd,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    # Configurer la toolchain MINGW64
                    self._configure_mingw64_toolchain(str(msys2_dir))
                    
                    Display.success("MINGW64 installé avec succès")
                    return True
                else:
                    Display.error("Échec de l'installation de MINGW64")
                    return False
            else:
                Display.error("Pacman non trouvé dans MSYS2")
                return False
                
        except Exception as e:
            Display.error(f"Erreur lors de l'installation de MINGW64: {e}")
            return False
    
    def _install_clang64(self) -> bool:
        """Installer Clang64 via MSYS2"""
        if not self.is_windows:
            Display.warning("Clang64 n'est disponible que sur Windows")
            return False
        
        # Vérifier si MSYS2 est installé
        msys2_dirs = ["C:/msys64", "C:/msys32"]
        msys2_dir = None
        
        for dir_path in msys2_dirs:
            if Path(dir_path).exists():
                msys2_dir = Path(dir_path)
                break
        
        if not msys2_dir:
            Display.error("MSYS2 n'est pas installé. Installez d'abord MSYS2:")
            Display.info("  jenga install msys2")
            return False
        
        Display.info("Installation de Clang64 via MSYS2...")
        
        try:
            pacman_path = msys2_dir / "usr" / "bin" / "pacman.exe"
            
            if pacman_path.exists():
                # Installer Clang64
                install_cmd = [
                    str(pacman_path), "-S", 
                    "--noconfirm",
                    "mingw-w64-clang-x86_64-gcc",
                    "mingw-w64-clang-x86_64-clang",
                    "mingw-w64-clang-x86_64-clang-tools-extra"
                ]
                
                result = subprocess.run(
                    install_cmd,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    # Configurer la toolchain Clang64
                    self._configure_clang64_toolchain(str(msys2_dir))
                    
                    Display.success("Clang64 installé avec succès")
                    return True
                else:
                    Display.error("Échec de l'installation de Clang64")
                    return False
            else:
                Display.error("Pacman non trouvé dans MSYS2")
                return False
                
        except Exception as e:
            Display.error(f"Erreur lors de l'installation de Clang64: {e}")
            return False
    
    def _install_llvm(self) -> bool:
        """Installer LLVM (Clang) - version standalone"""
        if self.is_windows:
            return self._install_llvm_windows()
        else:
            return self._install_clang()  # Sur Linux/macOS, installer Clang via package manager
    
    def _install_llvm_windows(self) -> bool:
        """Installer LLVM standalone sur Windows"""
        try:
            Display.info("Installation de LLVM (version standalone)...")
            
            # Version spécifique
            version = "18.1.8"
            download_url = LLVM_WINDOWS_URL.format(version=version)
            
            temp_dir = tempfile.mkdtemp()
            installer_path = Path(temp_dir) / "llvm-installer.exe"
            
            # Télécharger
            urllib.request.urlretrieve(download_url, installer_path)
            
            # Installer dans le répertoire des outils
            llvm_dir = self.tools_dir / "llvm"
            llvm_dir.mkdir(parents=True, exist_ok=True)
            
            Display.info("Exécution de l'installateur LLVM...")
            
            # Commande d'installation silencieuse
            cmd = [
                str(installer_path),
                "/S",  # Mode silencieux
                f"/D={llvm_dir}"  # Répertoire de destination
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                Display.error("Installation LLVM échouée")
                return False
            
            # Ajouter au PATH
            bin_path = llvm_dir / "bin"
            self._add_to_path(str(bin_path))
            
            # Configurer la toolchain
            self._configure_llvm_toolchain(str(llvm_dir))
            
            Display.success(f"LLVM installé dans: {llvm_dir}")
            
            # Vérifier l'installation
            if self._find_compiler("clang++", str(bin_path)):
                Display.info(f"  Clang++: {self._find_compiler('clang++', str(bin_path))}")
            if self._find_compiler("clang", str(bin_path)):
                Display.info(f"  Clang: {self._find_compiler('clang', str(bin_path))}")
            
            return True
            
        except Exception as e:
            Display.error(f"Erreur lors de l'installation de LLVM: {e}")
            return False
    
    def _install_gcc(self) -> bool:
        """Installer GCC (Linux/macOS)"""
        if self.is_windows:
            # Sur Windows, utiliser MSYS2
            Display.info("Sur Windows, utilisez 'ucrt64', 'mingw64' ou 'clang64' via MSYS2")
            return self._install_ucrt64()  # UCRT64 par défaut
        elif self.is_linux:
            return self._install_gcc_linux()
        elif self.is_macos:
            return self._install_gcc_macos()
        return False
    
    def _install_gcc_linux(self) -> bool:
        """Installer GCC sur Linux"""
        try:
            Display.info("Installation de GCC via le gestionnaire de paquets...")
            
            # Détecter le gestionnaire de paquets
            package_manager = self._detect_package_manager()
            
            if package_manager == "apt":
                cmd = ["sudo", "apt-get", "update"]
                subprocess.run(cmd, check=True)
                cmd = ["sudo", "apt-get", "install", "-y", "gcc", "g++", "build-essential"]
            elif package_manager == "dnf":
                cmd = ["sudo", "dnf", "install", "-y", "gcc", "gcc-c++"]
            elif package_manager == "yum":
                cmd = ["sudo", "yum", "install", "-y", "gcc", "gcc-c++"]
            elif package_manager == "zypper":
                cmd = ["sudo", "zypper", "install", "-y", "gcc", "gcc-c++"]
            elif package_manager == "pacman":
                cmd = ["sudo", "pacman", "-S", "--noconfirm", "gcc"]
            else:
                Display.error("Gestionnaire de paquets non supporté")
                return False
            
            subprocess.run(cmd, check=True)
            
            # Configurer la toolchain
            self._configure_gcc_toolchain()
            
            Display.success("GCC installé avec succès")
            return True
            
        except Exception as e:
            Display.error(f"Erreur d'installation de GCC: {e}")
            return False
    
    def _install_gcc_macos(self) -> bool:
        """Installer GCC sur macOS"""
        try:
            Display.info("Installation de GCC via Homebrew...")
            
            # Vérifier si Homebrew est installé
            if not shutil.which("brew"):
                Display.info("Installation de Homebrew...")
                install_script = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
                subprocess.run(install_script, shell=True, check=True)
            
            # Installer GCC
            subprocess.run(["brew", "install", "gcc"], check=True)
            
            # Configurer la toolchain
            self._configure_gcc_toolchain()
            
            Display.success("GCC installé avec succès")
            return True
            
        except Exception as e:
            Display.error(f"Erreur d'installation de GCC: {e}")
            return False
    
    def _install_clang(self) -> bool:
        """Installer Clang"""
        if self.is_windows:
            # Sur Windows, préférer Clang64 via MSYS2
            Display.info("Sur Windows, utilisez 'clang64' via MSYS2 pour une meilleure intégration")
            return self._install_clang64()
        elif self.is_linux:
            return self._install_clang_linux()
        elif self.is_macos:
            return self._install_clang_macos()
        return False
    
    def _install_clang_linux(self) -> bool:
        """Installer Clang sur Linux"""
        try:
            Display.info("Installation de Clang via le gestionnaire de paquets...")
            
            package_manager = self._detect_package_manager()
            
            if package_manager == "apt":
                cmd = ["sudo", "apt-get", "update"]
                subprocess.run(cmd, check=True)
                cmd = ["sudo", "apt-get", "install", "-y", "clang", "lld"]
            elif package_manager == "dnf":
                cmd = ["sudo", "dnf", "install", "-y", "clang", "lld"]
            elif package_manager == "yum":
                cmd = ["sudo", "yum", "install", "-y", "clang", "lld"]
            elif package_manager == "zypper":
                cmd = ["sudo", "zypper", "install", "-y", "clang", "lld"]
            elif package_manager == "pacman":
                cmd = ["sudo", "pacman", "-S", "--noconfirm", "clang", "lld"]
            else:
                Display.error("Gestionnaire de paquets non supporté")
                return False
            
            subprocess.run(cmd, check=True)
            
            # Configurer la toolchain
            self._configure_clang_toolchain()
            
            Display.success("Clang installé avec succès")
            return True
            
        except Exception as e:
            Display.error(f"Erreur d'installation de Clang: {e}")
            return False
    
    def _install_clang_macos(self) -> bool:
        """Installer Clang sur macOS"""
        Display.info("Clang est inclus avec Xcode Command Line Tools")
        
        try:
            # Vérifier si Command Line Tools sont installés
            result = subprocess.run(["xcode-select", "-p"], capture_output=True, text=True)
            
            if result.returncode != 0:
                Display.info("Installation de Xcode Command Line Tools...")
                subprocess.run(["xcode-select", "--install"], check=True)
                Display.info("Veuillez accepter la licence dans la fenêtre qui s'ouvre")
            
            # Accepter la licence
            subprocess.run(["sudo", "xcodebuild", "-license", "accept"], check=True)
            
            # Configurer la toolchain
            self._configure_clang_toolchain()
            
            Display.success("Clang installé avec succès")
            return True
            
        except Exception as e:
            Display.error(f"Erreur d'installation: {e}")
            return False
    
    def _install_android_ndk(self) -> bool:
        """Installer Android NDK"""
        try:
            Display.info("Installation d'Android NDK...")
            
            # Déterminer la plateforme
            if self.is_windows:
                plat = "windows"
                ext = "zip"
            elif self.is_linux:
                plat = "linux"
                ext = "zip"
            elif self.is_macos:
                plat = "darwin"
                ext = "zip"
            else:
                Display.error("Plateforme non supportée pour Android NDK")
                return False
            
            # Version
            version = "r26d"
            download_url = ANDROID_NDK_URL.format(version=version, platform=plat)
            
            temp_dir = tempfile.mkdtemp()
            archive_path = Path(temp_dir) / f"android-ndk.{ext}"
            
            # Télécharger
            Display.info(f"Téléchargement depuis: {download_url}")
            urllib.request.urlretrieve(download_url, archive_path)
            
            # Extraire dans le répertoire des outils
            ndk_dir = self.tools_dir / "android-ndk"
            ndk_dir.mkdir(parents=True, exist_ok=True)
            
            Display.info(f"Extraction vers: {ndk_dir}")
            
            if ext == "zip":
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(ndk_dir)
            else:
                with tarfile.open(archive_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(ndk_dir)
            
            # Trouver le répertoire NDK
            ndk_path = next(ndk_dir.glob("android-ndk-*"))
            
            # Ajouter au PATH
            self._add_to_path(str(ndk_path))
            
            # Configurer la toolchain Android
            self._configure_android_toolchain(str(ndk_path))
            
            Display.success(f"Android NDK installé dans: {ndk_path}")
            return True
            
        except Exception as e:
            Display.error(f"Erreur lors de l'installation d'Android NDK: {e}")
            return False
    
    def _install_emscripten(self) -> bool:
        """Installer Emscripten"""
        try:
            Display.info("Installation d'Emscripten...")
            
            # Créer le répertoire
            emsdk_dir = self.tools_dir / "emsdk"
            emsdk_dir.mkdir(parents=True, exist_ok=True)
            
            # Cloner ou télécharger Emscripten
            if (emsdk_dir / "emsdk.py").exists():
                Display.info("Emscripten déjà installé, mise à jour...")
            else:
                Display.info("Téléchargement d'Emscripten...")
                
                # Méthode 1: Git clone (préféré)
                if shutil.which("git"):
                    subprocess.run(
                        ["git", "clone", "https://github.com/emscripten-core/emsdk.git", str(emsdk_dir)],
                        check=True
                    )
                else:
                    # Méthode 2: Téléchargement ZIP
                    temp_dir = tempfile.mkdtemp()
                    archive_path = Path(temp_dir) / "emsdk.zip"
                    
                    urllib.request.urlretrieve(EMSDK_URL, archive_path)
                    
                    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                        zip_ref.extractall(emsdk_dir)
            
            # Installer et activer
            Display.info("Configuration d'Emscripten...")
            
            if self.is_windows:
                emsdk_script = emsdk_dir / "emsdk.bat"
                activate_cmd = f'call "{emsdk_script}" install latest && call "{emsdk_script}" activate latest'
                
                result = subprocess.run(
                    activate_cmd,
                    shell=True,
                    cwd=str(emsdk_dir),
                    capture_output=True,
                    text=True
                )
            else:
                emsdk_script = emsdk_dir / "emsdk"
                emsdk_script.chmod(0o755)
                
                result = subprocess.run(
                    [str(emsdk_script), "install", "latest"],
                    cwd=str(emsdk_dir),
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    result = subprocess.run(
                        [str(emsdk_script), "activate", "latest"],
                        cwd=str(emsdk_dir),
                        capture_output=True,
                        text=True
                    )
            
            if result.returncode != 0:
                Display.error("Installation Emscripten échouée")
                return False
            
            # Ajouter au PATH
            emscripten_path = emsdk_dir / "upstream" / "emscripten"
            self._add_to_path(str(emscripten_path))
            
            # Configurer la toolchain
            self._configure_emscripten_toolchain(str(emsdk_dir))
            
            Display.success(f"Emscripten installé dans: {emsdk_dir}")
            return True
            
        except Exception as e:
            Display.error(f"Erreur lors de l'installation d'Emscripten: {e}")
            return False
    
    def _install_visual_studio(self) -> bool:
        """Installer Visual Studio Build Tools (Windows uniquement)"""
        if not self.is_windows:
            Display.warning("Visual Studio n'est disponible que sur Windows")
            return False
        
        Display.info("Installation de Visual Studio Build Tools...")
        Display.info("Téléchargez depuis:")
        Display.info("  https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022")
        Display.info("Sélectionnez 'Desktop development with C++'")
        
        # Configurer la toolchain MSVC
        self._configure_msvc_toolchain()
        
        return True
    
    def _install_xcode(self) -> bool:
        """Installer Xcode (macOS uniquement)"""
        if not self.is_macos:
            Display.warning("Xcode n'est disponible que sur macOS")
            return False
        
        Display.info("Installation de Xcode...")
        Display.info("1. Ouvrez l'App Store")
        Display.info("2. Recherchez 'Xcode'")
        Display.info("3. Téléchargez et installez")
        Display.info("4. Après installation, exécutez: sudo xcodebuild -license accept")
        
        # Configurer la toolchain Xcode
        self._configure_xcode_toolchain()
        
        return True
    
    def _configure_msys2_toolchains(self, msys2_dir: str):
        """Configurer toutes les toolchains MSYS2"""
        msys2_path = Path(msys2_dir)
        
        # Configurer UCRT64 (recommandé)
        if (msys2_path / "ucrt64" / "bin").exists():
            self._configure_ucrt64_toolchain(msys2_dir)
        
        # Configurer MINGW64
        if (msys2_path / "mingw64" / "bin").exists():
            self._configure_mingw64_toolchain(msys2_dir)
        
        # Configurer Clang64
        if (msys2_path / "clang64" / "bin").exists():
            self._configure_clang64_toolchain(msys2_dir)
    
    def _configure_ucrt64_toolchain(self, msys2_dir: str):
        """Configurer une toolchain UCRT64"""
        toolchain_config = {
            "name": "ucrt64",
            "compiler": "g++",
            "ccompiler": "gcc",
            "cppcompiler": "g++",
            "archiver": "ar",
            "toolchain_dir": msys2_dir,
            "bin_dir": f"{msys2_dir}/ucrt64/bin",
            "defines": ["MINGW", "__MINGW32__", "__MINGW64__", "__UCRT__"],
            "cflags": ["-m64", "-march=x86-64"],
            "cxxflags": ["-std=c++17", "-m64", "-march=x86-64"],
            "ldflags": ["-static-libgcc", "-static-libstdc++"]
        }
        
        self._save_toolchain_config(toolchain_config)
        Display.info("Toolchain UCRT64 configurée")
    
    def _configure_mingw64_toolchain(self, msys2_dir: str):
        """Configurer une toolchain MINGW64"""
        toolchain_config = {
            "name": "mingw64",
            "compiler": "g++",
            "ccompiler": "gcc",
            "cppcompiler": "g++",
            "archiver": "ar",
            "toolchain_dir": msys2_dir,
            "bin_dir": f"{msys2_dir}/mingw64/bin",
            "defines": ["MINGW", "__MINGW32__", "__MINGW64__"],
            "cflags": ["-m64", "-march=x86-64"],
            "cxxflags": ["-std=c++17", "-m64", "-march=x86-64"],
            "ldflags": ["-static-libgcc", "-static-libstdc++"]
        }
        
        self._save_toolchain_config(toolchain_config)
        Display.info("Toolchain MINGW64 configurée")
    
    def _configure_clang64_toolchain(self, msys2_dir: str):
        """Configurer une toolchain Clang64"""
        toolchain_config = {
            "name": "clang64",
            "compiler": "clang++",
            "ccompiler": "clang",
            "cppcompiler": "clang++",
            "archiver": "ar",
            "toolchain_dir": msys2_dir,
            "bin_dir": f"{msys2_dir}/clang64/bin",
            "defines": ["MINGW", "__MINGW32__", "__MINGW64__", "__clang__"],
            "cflags": ["-m64", "-march=x86-64"],
            "cxxflags": ["-std=c++17", "-m64", "-march=x86-64"],
            "ldflags": []
        }
        
        self._save_toolchain_config(toolchain_config)
        Display.info("Toolchain Clang64 configurée")
    
    def _configure_llvm_toolchain(self, llvm_dir: str):
        """Configurer une toolchain LLVM standalone"""
        toolchain_config = {
            "name": "llvm",
            "compiler": "clang++",
            "ccompiler": "clang",
            "cppcompiler": "clang++",
            "archiver": "llvm-ar",
            "toolchain_dir": llvm_dir,
            "defines": ["__clang__", "__LLVM__"],
            "cflags": ["-m64"],
            "cxxflags": ["-std=c++17", "-m64"],
            "ldflags": ["-fuse-ld=lld"]
        }
        
        self._save_toolchain_config(toolchain_config)
        Display.info("Toolchain LLVM (standalone) configurée")
    
    def _configure_gcc_toolchain(self):
        """Configurer une toolchain GCC (Linux/macOS)"""
        toolchain_config = {
            "name": "gcc",
            "compiler": "g++",
            "ccompiler": "gcc",
            "cppcompiler": "g++",
            "archiver": "ar",
            "defines": ["__GNUC__", "__GNUG__"],
            "cflags": [],
            "cxxflags": ["-std=c++17"],
            "ldflags": []
        }
        
        self._save_toolchain_config(toolchain_config)
        Display.info("Toolchain GCC configurée")
    
    def _configure_clang_toolchain(self):
        """Configurer une toolchain Clang (système)"""
        toolchain_config = {
            "name": "clang",
            "compiler": "clang++",
            "ccompiler": "clang",
            "cppcompiler": "clang++",
            "archiver": "ar",
            "defines": ["__clang__"],
            "cflags": [],
            "cxxflags": ["-std=c++17"],
            "ldflags": []
        }
        
        self._save_toolchain_config(toolchain_config)
        Display.info("Toolchain Clang configurée")
    
    def _configure_msvc_toolchain(self):
        """Configurer une toolchain MSVC"""
        toolchain_config = {
            "name": "msvc",
            "compiler": "cl.exe",
            "ccompiler": "cl.exe",
            "cppcompiler": "cl.exe",
            "linker": "link.exe",
            "archiver": "lib.exe",
            "defines": ["_MSC_VER", "_WIN32", "_WIN64"],
            "cflags": ["/nologo", "/EHsc", "/W4", "/MT"],
            "cxxflags": ["/std:c++17", "/nologo", "/EHsc", "/W4", "/MT"],
            "ldflags": ["/nologo"]
        }
        
        self._save_toolchain_config(toolchain_config)
        Display.info("Toolchain MSVC configurée")
    
    def _configure_xcode_toolchain(self):
        """Configurer une toolchain Xcode"""
        toolchain_config = {
            "name": "xcode",
            "compiler": "clang++",
            "ccompiler": "clang",
            "cppcompiler": "clang++",
            "archiver": "ar",
            "defines": ["__APPLE__", "__MACH__", "__clang__"],
            "cflags": [],
            "cxxflags": ["-std=c++17"],
            "ldflags": ["-framework Cocoa", "-framework Foundation"]
        }
        
        self._save_toolchain_config(toolchain_config)
        Display.info("Toolchain Xcode configurée")
    
    def _configure_android_toolchain(self, ndk_path: str):
        """Configurer une toolchain Android"""
        toolchain_config = {
            "name": "android",
            "compiler": "clang++",
            "ccompiler": "clang",
            "cppcompiler": "clang++",
            "defines": ["ANDROID", "__ANDROID__"],
            "cflags": ["-fPIC"],
            "cxxflags": ["-std=c++17", "-fPIC"],
            "ldflags": ["-llog", "-landroid"],
            "toolchain_dir": ndk_path
        }
        
        self._save_toolchain_config(toolchain_config)
        Display.info("Toolchain Android configurée")
    
    def _configure_emscripten_toolchain(self, emsdk_dir: str):
        """Configurer une toolchain Emscripten"""
        toolchain_config = {
            "name": "emscripten",
            "compiler": "em++",
            "ccompiler": "emcc",
            "cppcompiler": "em++",
            "archiver": "emar",
            "defines": ["EMSCRIPTEN", "__EMSCRIPTEN__"],
            "cflags": ["-s", "WASM=1"],
            "cxxflags": ["-std=c++17", "-s", "WASM=1"],
            "ldflags": ["-s", "WASM=1", "-s", "ALLOW_MEMORY_GROWTH=1"],
            "toolchain_dir": emsdk_dir
        }
        
        self._save_toolchain_config(toolchain_config)
        Display.info("Toolchain Emscripten configurée")
    
    def _add_msys2_to_path(self, msys2_dir: str):
        """Ajouter MSYS2 au PATH Windows"""
        if not self.is_windows:
            return
        
        paths_to_add = [
            f"{msys2_dir}/ucrt64/bin",  # UCRT64 en premier (recommandé)
            f"{msys2_dir}/mingw64/bin",
            f"{msys2_dir}/clang64/bin",
            f"{msys2_dir}/usr/bin"
        ]
        
        for path in paths_to_add:
            if Path(path).exists():
                self._add_to_path_windows(path)
                Display.info(f"Ajouté au PATH: {path}")
    
    def _detect_package_manager(self) -> str:
        """Détecter le gestionnaire de paquets"""
        if shutil.which("apt"):
            return "apt"
        elif shutil.which("dnf"):
            return "dnf"
        elif shutil.which("yum"):
            return "yum"
        elif shutil.which("zypper"):
            return "zypper"
        elif shutil.which("pacman"):
            return "pacman"
        return "unknown"
    
    def _find_compiler(self, compiler_name: str, search_path: str = None) -> Optional[str]:
        """Trouver un compilateur dans le PATH ou un répertoire spécifique"""
        if search_path:
            # Chercher dans le répertoire spécifié
            compiler_path = Path(search_path) / compiler_name
            if self.is_windows:
                compiler_path = compiler_path.with_suffix(".exe")
            
            if compiler_path.exists():
                return str(compiler_path)
        
        # Chercher dans le PATH
        return shutil.which(compiler_name)
    
    def _add_to_path(self, path: str):
        """Ajouter un chemin au PATH"""
        if self.is_windows:
            self._add_to_path_windows(path)
        else:
            self._add_to_path_unix(path)
    
    def _add_to_path_windows(self, path: str):
        """Ajouter un chemin au PATH Windows"""
        try:
            import winreg
            
            # Ouvrir la clé PATH utilisateur
            reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(reg, r"Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE)
            
            # Lire la valeur actuelle
            try:
                current_path, _ = winreg.QueryValueEx(key, "Path")
            except WindowsError:
                current_path = ""
            
            # Ajouter le chemin s'il n'est pas déjà présent
            if path not in current_path:
                new_path = current_path + ";" + path if current_path else path
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                
                Display.info(f"Ajouté au PATH: {path}")
                Display.warning("Redémarrez votre terminal pour que les changements prennent effet")
            
            winreg.CloseKey(key)
            
        except Exception as e:
            Display.warning(f"Impossible d'ajouter au PATH automatiquement: {e}")
            Display.info(f"Veuillez ajouter manuellement au PATH: {path}")
    
    def _add_to_path_unix(self, path: str):
        """Ajouter un chemin au PATH Unix/Linux/macOS"""
        shell_configs = [
            Path.home() / ".bashrc",
            Path.home() / ".bash_profile",
            Path.home() / ".zshrc",
            Path.home() / ".profile"
        ]
        
        export_line = f'\nexport PATH="$PATH:{path}"\n'
        
        for config_file in shell_configs:
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()
                    
                    if path not in content and export_line.strip() not in content:
                        with open(config_file, 'a') as f:
                            f.write(export_line)
                        Display.info(f"Ajouté au PATH dans {config_file.name}")
                except Exception as e:
                    Display.warning(f"Impossible de modifier {config_file}: {e}")
        
        Display.warning("Exécutez 'source ~/.bashrc' ou redémarrez votre terminal")
    
    def _save_toolchain_config(self, config: Dict):
        """Sauvegarder la configuration d'une toolchain"""
        configs_dir = self.tools_dir / "toolchains"
        configs_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = configs_dir / f"{config['name']}.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_toolchain_configs(self) -> Dict[str, Dict]:
        """Charger toutes les configurations de toolchains"""
        configs = {}
        configs_dir = self.tools_dir / "toolchains"
        
        if configs_dir.exists():
            for config_file in configs_dir.glob("*.json"):
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    configs[config['name']] = config
                except Exception as e:
                    Display.warning(f"Erreur de chargement de {config_file}: {e}")
        
        return configs
    
    def detect_installed_tools(self) -> Dict[str, Dict]:
        """Détecter les outils déjà installés"""
        Display.info("Recherche des outils installés...")
        
        tools = {}
        
        # Compilateurs C/C++
        compilers = {
            "g++": "GNU C++ Compiler",
            "clang++": "Clang C++ Compiler",
            "cl.exe": "Microsoft C++ Compiler",
            "em++": "Emscripten C++ Compiler"
        }
        
        for compiler, description in compilers.items():
            path = self._find_compiler(compiler)
            if path:
                tools[compiler] = {
                    "path": path,
                    "description": description,
                    "version": self._get_compiler_version(compiler, path)
                }
        
        # Détecter MSYS2
        msys2_dirs = ["C:/msys64", "C:/msys32"]
        for dir_path in msys2_dirs:
            if Path(dir_path).exists():
                tools["msys2"] = {
                    "path": dir_path,
                    "description": "MSYS2 Environment",
                    "environments": []
                }
                
                # Détecter les environnements MSYS2
                msys2_path = Path(dir_path)
                for env in ["ucrt64", "mingw64", "clang64"]:
                    if (msys2_path / env / "bin").exists():
                        tools["msys2"]["environments"].append(env)
        
        # Outils de build
        build_tools = {
            "cmake": "CMake Build System",
            "ninja": "Ninja Build System",
            "make": "GNU Make",
            "gradle": "Gradle Build System",
            "ndk-build": "Android NDK Build"
        }
        
        for tool, description in build_tools.items():
            path = shutil.which(tool)
            if path:
                tools[tool] = {
                    "path": path,
                    "description": description
                }
        
        return tools
    
    def _get_compiler_version(self, compiler: str, path: str) -> str:
        """Obtenir la version d'un compilateur"""
        try:
            if compiler == "cl.exe":
                # MSVC
                result = subprocess.run([path, "/?"], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if "Compiler Version" in line:
                        return line.strip()
            else:
                # GCC/Clang/others
                result = subprocess.run([path, "--version"], capture_output=True, text=True)
                return result.stdout.split('\n')[0].strip()
        except:
            pass
        
        return "Version inconnue"
    
    def generate_nken_file(self, workspace_dir: Path):
        """Générer un fichier .nken avec les toolchains détectées"""
        toolchains = self.load_toolchain_configs()
        
        if not toolchains:
            Display.warning("Aucune toolchain configurée")
            return
        
        nken_content = "# Toolchains auto-générées par la commande 'jenga install'\n"
        nken_content += "# UCRT64 est recommandé pour Windows (Modern C Runtime)\n\n"
        
        # Toolchain UCRT64 en premier si disponible (recommandée)
        if "ucrt64" in toolchains:
            config = toolchains["ucrt64"]
            nken_content += self._format_toolchain_config("ucrt64", config, is_recommended=True)
        
        # Autres toolchains
        for name, config in toolchains.items():
            if name != "ucrt64":
                nken_content += self._format_toolchain_config(name, config)
        
        # Ajouter un workspace exemple
        nken_content += "\n# Exemple de workspace avec toolchain UCRT64 par défaut\n"
        nken_content += "with workspace(\"MyProject\"):\n"
        nken_content += "    configurations([\"Debug\", \"Release\"])\n"
        nken_content += "    platforms([\"Windows\", \"Linux\", \"MacOS\"])\n"
        nken_content += "    \n"
        nken_content += "    # Utiliser UCRT64 par défaut (recommandé pour Windows)\n"
        if "ucrt64" in toolchains:
            nken_content += "    usetoolchain(\"ucrt64\")  # Modern C Runtime\n"
        elif "mingw64" in toolchains:
            nken_content += "    usetoolchain(\"mingw64\")  # Legacy MSVCRT\n"
        nken_content += "    \n"
        nken_content += "    with project(\"MyApp\"):\n"
        nken_content += "        consoleapp()\n"
        nken_content += "        language(\"C++\")\n"
        nken_content += "        cppdialect(\"C++17\")\n"
        nken_content += "        files([\"src/**.cpp\"])\n"
        nken_content += "        \n"
        nken_content += "        # Vous pouvez changer de toolchain pour ce projet\n"
        nken_content += "        # usetoolchain(\"clang64\")  # Utiliser Clang64 pour ce projet\n"
        nken_content += "        # usetoolchain(\"llvm\")    # Utiliser LLVM standalone\n"
        
        nken_file = workspace_dir / "toolchains.nken"
        with open(nken_file, 'w') as f:
            f.write(nken_content)
        
        Display.success(f"Fichier de toolchains généré: {nken_file}")
        Display.info(f"  Incluez-le dans votre jenga.nken avec: include(\"toolchains.nken\")")
    
    def _format_toolchain_config(self, name: str, config: Dict, is_recommended: bool = False) -> str:
        """Formatter une configuration de toolchain pour le fichier .nken"""
        content = ""
        
        if is_recommended:
            content += f"# Toolchain: {name} (RECOMMANDÉ)\n"
        else:
            content += f"# Toolchain: {name}\n"
        
        if name == "ucrt64":
            content += "# Modern C Runtime - Meilleure compatibilité Windows 10/11\n"
        elif name == "mingw64":
            content += "# Legacy MSVCRT - Compatibilité descendante\n"
        elif name == "clang64":
            content += "# Clang avec MSYS2 - Optimisations modernes\n"
        
        content += f"with toolchain(\"{name}\", \"{config.get('compiler', 'g++')}\"):\n"
        
        if config.get('ccompiler'):
            content += f"    ccompiler(\"{config['ccompiler']}\")\n"
        if config.get('cppcompiler'):
            content += f"    cppcompiler(\"{config['cppcompiler']}\")\n"
        if config.get('linker'):
            content += f"    linker(\"{config['linker']}\")\n"
        if config.get('archiver'):
            content += f"    archiver(\"{config['archiver']}\")\n"
        
        if config.get('defines'):
            defines_str = ', '.join(f'"{d}"' for d in config['defines'])
            content += f"    defines([{defines_str}])\n"
        
        if config.get('cflags'):
            cflags_str = ', '.join(f'"{f}"' for f in config['cflags'])
            content += f"    cflags([{cflags_str}])\n"
        
        if config.get('cxxflags'):
            cxxflags_str = ', '.join(f'"{f}"' for f in config['cxxflags'])
            content += f"    cxxflags([{cxxflags_str}])\n"
        
        if config.get('ldflags'):
            ldflags_str = ', '.join(f'"{f}"' for f in config['ldflags'])
            content += f"    ldflags([{ldflags_str}])\n"
        
        if config.get('toolchain_dir'):
            content += f"    toolchaindir(\"{config['toolchain_dir']}\")\n"
        
        if config.get('bin_dir'):
            content += f"    # Chemin des binaires: {config['bin_dir']}\n"
        
        content += "\n"
        return content


def print_help():
    """Afficher l'aide de la commande install"""
    help_text = """
Usage: jenga install [tool...] [options]

Installation de compilateurs et configuration automatique des toolchains.
Sur Windows, MSYS2 est recommandé avec UCRT64 comme environnement par défaut.

Outils disponibles:
  msys2         - Installer MSYS2 (base pour tous les environnements Windows)
  ucrt64        - Installer UCRT64 via MSYS2 (RECOMMANDÉ - Modern C Runtime)
  mingw64       - Installer MINGW64 via MSYS2 (Legacy MSVCRT)
  clang64       - Installer Clang64 via MSYS2 (Clang avec MSYS2)
  llvm          - Installer LLVM/Clang standalone
  gcc           - Installer GCC (Linux/macOS) ou via MSYS2 (Windows)
  clang         - Installer Clang (Linux/macOS) ou via MSYS2 (Windows)
  android-ndk   - Installer Android NDK et configurer la toolchain
  emscripten    - Installer Emscripten et configurer la toolchain
  visualstudio  - Installer Visual Studio Build Tools et configurer MSVC toolchain
  xcode         - Installer Xcode et configurer la toolchain (macOS)
  
  all           - Installer les outils recommandés pour la plateforme
                  Windows: msys2 + ucrt64
                  Linux: gcc + clang
                  macOS: clang

Options:
  --detect      - Détecter les outils déjà installés
  --generate    - Générer un fichier .nken avec les toolchains configurées
  --help, -h    - Afficher cette aide

Exemples:
  # Détecter les outils installés
  jenga install --detect
  
  # Installation Windows recommandée
  jenga install msys2 ucrt64
  
  # Installation complète Windows
  jenga install msys2 ucrt64 mingw64 clang64
  
  # Installer les outils recommandés pour la plateforme
  jenga install all
  
  # Générer un fichier de toolchains
  jenga install --generate
  
  # Installer des outils cross-platform
  jenga install android-ndk emscripten

Notes:
  - UCRT64 (Modern C Runtime) est recommandé pour Windows 10/11
  - MINGW64 utilise l'ancien MSVCRT pour la compatibilité descendante
  - Clang64 offre les meilleures optimisations modernes
"""
    print(help_text)


def execute(options: dict) -> bool:
    """Exécuter la commande install"""
    
    # Vérifier les options
    if options.get("detect", False):
        manager = ToolManager()
        tools = manager.detect_installed_tools()
        
        if not tools:
            Display.info("Aucun outil détecté")
        else:
            Display.info("Outils détectés:")
            for tool, info in tools.items():
                if tool == "msys2":
                    path = info.get('path', 'Non trouvé')
                    envs = info.get('environments', [])
                    Display.success(f"  ✓ MSYS2: {path}")
                    if envs:
                        Display.info(f"     Environnements: {', '.join(envs)}")
                else:
                    path = info.get('path', 'Non trouvé')
                    desc = info.get('description', '')
                    version = info.get('version', '')
                    
                    if version:
                        Display.success(f"  ✓ {tool}: {desc} ({version})")
                        Display.info(f"     Path: {path}")
                    else:
                        Display.success(f"  ✓ {tool}: {desc}")
                        Display.info(f"     Path: {path}")
        
        # Charger les toolchains configurées
        toolchains = manager.load_toolchain_configs()
        if toolchains:
            Display.info("\nToolchains configurées:")
            for name, config in toolchains.items():
                compiler = config.get('compiler', 'N/A')
                if name == "ucrt64":
                    Display.info(f"  • {name}: {compiler} (RECOMMANDÉ)")
                else:
                    Display.info(f"  • {name}: {compiler}")
        
        return True
    
    if options.get("generate", False):
        manager = ToolManager()
        # Générer dans le répertoire courant
        manager.generate_nken_file(Path.cwd())
        return True
    
    # Récupérer les outils à installer
    tools = options.get("tools", [])
    
    if not tools:
        print_help()
        return False
    
    # Si "all" est spécifié, installer tous les outils recommandés
    if "all" in tools:
        current_platform = platform.system()
        if current_platform == "Windows":
            Display.info("Installation recommandée pour Windows: MSYS2 + UCRT64")
            tools = ["msys2", "ucrt64"]
        elif current_platform == "Linux":
            tools = ["gcc", "clang"]
        elif current_platform == "Darwin":
            tools = ["clang"]
        else:
            tools = ["gcc"]
    
    # Installer les outils
    manager = ToolManager()
    results = manager.install_and_configure(tools)
    
    # Afficher le résumé
    Display.info("\nRésumé de l'installation:")
    all_success = True
    for tool, success in results.items():
        if success:
            Display.success(f"  ✓ {tool}")
        else:
            Display.error(f"  ✗ {tool}")
            all_success = False
    
    # Détecter les outils après installation
    Display.info("\nOutils détectés après installation:")
    installed_tools = manager.detect_installed_tools()
    if installed_tools:
        for tool, info in installed_tools.items():
            if tool == "msys2":
                envs = info.get('environments', [])
                if envs:
                    Display.success(f"  ✓ MSYS2 avec environnements: {', '.join(envs)}")
            else:
                desc = info.get('description', '')
                Display.success(f"  ✓ {tool}: {desc}")
    
    # Charger les toolchains configurées
    toolchains = manager.load_toolchain_configs()
    if toolchains:
        Display.info("\nToolchains configurées:")
        for name, config in toolchains.items():
            compiler = config.get('compiler', 'N/A')
            if name == "ucrt64":
                Display.info(f"  • {name}: {compiler} (RECOMMANDÉ pour Windows)")
            else:
                Display.info(f"  • {name}: {compiler}")
        
        # Proposer de générer un fichier de toolchains
        Display.info("\nPour utiliser ces toolchains, générez un fichier de configuration:")
        Display.info("  jenga install --generate")
        Display.info("\nPuis incluez-le dans votre jenga.nken avec:")
        Display.info("  include(\"toolchains.nken\")")
    
    return all_success


if __name__ == "__main__":
    # Pour les tests
    execute({"tools": ["msys2"]})