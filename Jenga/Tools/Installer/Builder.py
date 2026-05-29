#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Builder — construit un installateur self-extracting Jenga.

Étapes :
  1. Compile le stub C (Jenga/Tools/Installer/Stub/Installer.c) en binaire natif.
  2. Construit le payload : manifeste (texte) + archive (entrées de fichiers).
  3. Concatène : [stub] + [payload] + [trailer 48 octets] -> installateur final.

Format détaillé : voir DESIGN.md. Aucune dépendance externe (stdlib seulement).

Nomenclature : fonctions/classes en PascalCase ; variables locales en snake_case
(convention Python de Jenga).
"""
from __future__ import annotations

import hashlib
import os
import shutil
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

MAGIC = b"JNGINST1"           # 8 octets
TRAILER_SIZE = 80            # 48 (entetes) + 32 (SHA-256 du payload)

# Une entrée de fichier à embarquer : (arcName, cheminAbsolu, modePosix)
FileEntry = Tuple[str, str, int]


class BuilderError(Exception):
    """Erreur de construction de l'installateur."""


# ─────────────────────────────────────────────────────────────────────────────
# Détection / compilation du stub C
# ─────────────────────────────────────────────────────────────────────────────
def DetectCCompiler() -> Optional[List[str]]:
    """Retourne la commande d'un compilateur C disponible, ou None.

    Ordre : cc, clang, gcc (drivers POSIX-like), puis cl (MSVC)."""
    for compiler in ("cc", "clang", "gcc"):
        if shutil.which(compiler):
            return [compiler]
    if shutil.which("cl"):
        return ["cl"]
    return None


def CompileStub(stub_src: Path, out_bin: Path, cc: Optional[List[str]] = None,
                verbose: bool = False) -> None:
    """Compile le stub C en binaire natif (optimisé, autonome)."""
    cc = cc or DetectCCompiler()
    if not cc:
        raise BuilderError(
            "Aucun compilateur C trouvé (cc/clang/gcc/cl). "
            "Installe un compilateur C pour générer l'installateur self-extracting."
        )
    out_bin.parent.mkdir(parents=True, exist_ok=True)
    is_cl = cc[0].lower() == "cl"
    on_windows = os.name == "nt"
    if is_cl:
        # MSVC : /O2 optimise, /Fe nomme l'exe ; objets dans un tmp.
        # Libs Windows : COM (.lnk via IShellLink), registre (Uninstall), shell.
        with tempfile.TemporaryDirectory() as td:
            cmd = cc + ["/nologo", "/O2", "/MT", str(stub_src),
                        f"/Fe:{out_bin}", f"/Fo:{Path(td) / 'stub.obj'}",
                        "/link", "ole32.lib", "uuid.lib", "shell32.lib", "advapi32.lib"]
            _Run(cmd, verbose, cwd=td)
    else:
        # gcc/clang/cc : -O2, -s (strip) pour un stub compact. Sur Windows,
        # lier ole32/uuid/shell32/advapi32 (raccourcis COM + registre).
        win_libs = ["-lole32", "-luuid", "-lshell32", "-ladvapi32"] if on_windows else []
        try:
            _Run(cc + ["-O2", "-s", str(stub_src), "-o", str(out_bin)] + win_libs, verbose)
        except BuilderError:
            # -s n'est pas supporté partout (ex: macOS ld) -> retenter sans.
            _Run(cc + ["-O2", str(stub_src), "-o", str(out_bin)] + win_libs, verbose)
    if not out_bin.exists():
        raise BuilderError(f"La compilation du stub n'a produit aucun binaire : {out_bin}")


def _Run(cmd: List[str], verbose: bool, cwd: Optional[str] = None) -> None:
    if verbose:
        print("  $", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=cwd, capture_output=not verbose, text=True)
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or "").strip() if not verbose else ""
        raise BuilderError(f"Échec compilation stub (code {proc.returncode}).\n{msg}")


# ─────────────────────────────────────────────────────────────────────────────
# Manifeste + payload
# ─────────────────────────────────────────────────────────────────────────────
def RenderManifest(manifest: Dict[str, str]) -> str:
    """Rend le manifeste au format `cle=valeur` (une paire par ligne).

    Les valeurs multi-lignes ne sont pas autorisées (une commande firewall tient
    sur une ligne). Les clés à valeur vide sont omises."""
    lines = []
    for key, value in manifest.items():
        if value is None:
            continue
        value = str(value).replace("\n", " ").replace("\r", " ")
        if value == "":
            continue
        lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"


def _BuildArchive(files: List[FileEntry]) -> Tuple[bytes, int]:
    """Construit l'archive binaire. Retourne (octets, nombre_d_entrees)."""
    buf = bytearray()
    count = 0
    for arc_name, abs_path, mode in files:
        path = Path(abs_path)
        if not path.is_file():
            raise BuilderError(f"Fichier introuvable pour l'archive : {abs_path}")
        data = path.read_bytes()
        name_bytes = arc_name.replace("\\", "/").encode("utf-8")
        buf += struct.pack("<I", len(name_bytes))
        buf += name_bytes
        buf += struct.pack("<I", int(mode) & 0xFFFFFFFF)
        buf += struct.pack("<Q", len(data))
        buf += data
        count += 1
    return bytes(buf), count


# ─────────────────────────────────────────────────────────────────────────────
# Construction de l'installateur
# ─────────────────────────────────────────────────────────────────────────────
def BuildInstaller(files: List[FileEntry],
                   manifest: Dict[str, str],
                   output: Path,
                   stub_src: Optional[Path] = None,
                   cc: Optional[List[str]] = None,
                   verbose: bool = False) -> Path:
    """
    Construit un installateur self-extracting.

    files    : liste de (arcName, cheminAbsolu, modePosix). `arcName` est le
               chemin relatif dans le dossier d'installation final.
    manifest : métadonnées (name, version, publisher, default_dir_*, exe,
               firewall_add/firewall_del, ...).
    output   : chemin de l'installateur à produire.
    Retourne le chemin de l'installateur.
    """
    output = Path(output)
    stub_src = Path(stub_src) if stub_src else (Path(__file__).parent / "Stub" / "Installer.c")
    if not stub_src.is_file():
        raise BuilderError(f"Source du stub introuvable : {stub_src}")

    # 1. Compiler le stub dans un emplacement temporaire.
    with tempfile.TemporaryDirectory() as td:
        stub_bin = Path(td) / ("stub.exe" if os.name == "nt" else "stub")
        CompileStub(stub_src, stub_bin, cc=cc, verbose=verbose)
        stub_bytes = stub_bin.read_bytes()

    # 2. Manifeste + archive.
    manifest_bytes = RenderManifest(manifest).encode("utf-8")
    archive_bytes, entry_count = _BuildArchive(files)

    # 3. Offsets ABSOLUS dans le fichier final (le payload suit le stub).
    manifest_off = len(stub_bytes)
    archive_off = manifest_off + len(manifest_bytes)
    payload = manifest_bytes + archive_bytes
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    # SHA-256 du payload : vérifié par le stub avant extraction (anti-tampering).
    sha256 = hashlib.sha256(payload).digest()    # 32 octets

    # 4. Trailer 80 octets : magic(8) + 4×u64 + crc(u32) + reserved(u32) + sha256(32).
    trailer = (MAGIC
               + struct.pack("<QQQQ", manifest_off, len(manifest_bytes), archive_off, entry_count)
               + struct.pack("<II", crc, 0)
               + sha256)
    assert len(trailer) == TRAILER_SIZE, f"trailer={len(trailer)}"

    # 5. Écriture : stub + payload + trailer.
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "wb") as f:
        f.write(stub_bytes)
        f.write(payload)
        f.write(trailer)

    # 6. Exécutable sur Unix.
    if os.name != "nt":
        import stat as _stat
        output.chmod(output.stat().st_mode | _stat.S_IEXEC | _stat.S_IXGRP | _stat.S_IXOTH)

    return output
