#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IDEConfigurator.py
==================
Configuration automatique des editeurs de code pour les projets jenga.

Probleme adresse : les fichiers `*.jenga` sont du Python (au sens runtime),
mais l'IDE ne le sait pas par defaut. Sans configuration :
  - Pas de coloration syntaxique sur les .jenga
  - Pas d'autocomplete sur les fonctions DSL (appicon, project, files, ...)
  - Warnings 'undefined' sur tous les symboles importes via `from Jenga import *`

Ce module configure automatiquement l'IDE de l'utilisateur en :
  1. Associant .jenga -> Python (coloration syntaxique)
  2. Ajoutant le module Jenga aux extraPaths (pyright/pylance resoud les
     symboles)
  3. Desactivant les warnings de wildcard import (faux positifs sur .jenga)

Strategie : MERGE NON-DESTRUCTIF.
  - Si une cle jenga existe deja dans la config user, on la met a jour SANS
    toucher aux autres prefs.
  - Si la config user n'existe pas, on la cree.
  - Idempotent : un marker (fingerprint de la config jenga) evite de
    re-ecrire si la config est deja a jour.

Editeurs supportes en E0 :
  - VSCode/Cursor/Windsurf  : .vscode/settings.json (merge JSONC)
  - LSP universel (Neovim+pyright, Emacs+lsp-mode, Helix, Sublime+LSP,
    Zed, ...) : pyrightconfig.json (commun a tous les clients LSP utilisant
    pyright comme backend Python)

Auto-trigger :
  - IDEConfigurator.AutoConfigure() est appelee silencieusement au debut de
    `jenga build`. Le marker assure qu'on ne re-ecrit pas si rien n'a change.

Auteur : Jenga Team
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import json
import os
import re
import hashlib


# Version du schema de config jenga IDE. Bumper si on change les cles ecrites
# (force une regeneration au prochain build).
_CONFIG_SCHEMA_VERSION = "1.0"


# ─────────────────────────────────────────────────────────────────────────────
# Auto-resolution du chemin Jenga (le user n'a jamais a le hardcoder)
# ─────────────────────────────────────────────────────────────────────────────
def GetJengaHome() -> Optional[str]:
    """
    Retourne le chemin PARENT du package Jenga (= ce qui doit etre dans
    extraPaths pour que `import Jenga` resolve correctement).

    Exemple : si Jenga est installe a `/usr/lib/python3.10/site-packages/Jenga/`,
    retourne `/usr/lib/python3.10/site-packages` (le dossier qui CONTIENT Jenga).
    """
    try:
        import Jenga as _j
        jenga_pkg = Path(_j.__file__).resolve().parent  # .../Jenga/
        return str(jenga_pkg.parent).replace("\\", "/")
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# JSONC support (JSON with Comments) — VSCode autorise // et /* */ dans
# settings.json. On strip les commentaires avant `json.loads` pour eviter
# le crash sur configs existantes. ATTENTION : ce strip simple ne preserve
# pas les commentaires en re-ecriture (on accepte ce trade-off).
# ─────────────────────────────────────────────────────────────────────────────
_JSONC_LINE_COMMENT = re.compile(r"//.*?$",       re.MULTILINE)
_JSONC_BLOCK_COMMENT = re.compile(r"/\*.*?\*/",   re.DOTALL)
_JSONC_TRAILING_COMMA = re.compile(r",(\s*[}\]])")


def _ParseJsonc(text: str) -> Any:
    """Parse JSON avec support des commentaires // et /* */ + trailing commas."""
    cleaned = _JSONC_LINE_COMMENT.sub("", text)
    cleaned = _JSONC_BLOCK_COMMENT.sub("", cleaned)
    cleaned = _JSONC_TRAILING_COMMA.sub(r"\1", cleaned)
    return json.loads(cleaned)


def _LoadJsonFile(path: Path) -> Optional[Dict[str, Any]]:
    """
    Charge un fichier JSON/JSONC. Retourne dict ou None si le fichier
    n'existe pas / est invalide. Jamais lever : on logue silencieusement.
    """
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    if not text.strip():
        return {}
    try:
        return _ParseJsonc(text)
    except Exception:
        return None


def _WriteJsonFile(path: Path, data: Dict[str, Any]) -> bool:
    """Ecrit un dict en JSON pretty (indent=4). Cree le parent si besoin."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # ensure_ascii=False pour preserver les accents francais dans les chaines.
        text = json.dumps(data, indent=4, ensure_ascii=False, sort_keys=False)
        path.write_text(text + "\n", encoding="utf-8")
        return True
    except Exception:
        return False


def _Fingerprint(data: Dict[str, Any]) -> str:
    """Hash stable des cles jenga pour le marker d'idempotence."""
    payload = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


# ─────────────────────────────────────────────────────────────────────────────
# Editeur : VSCode (et compatibles Cursor / Windsurf qui lisent .vscode/)
# ─────────────────────────────────────────────────────────────────────────────
def _GetVSCodeJengaConfig(jenga_home: Optional[str]) -> Dict[str, Any]:
    """
    Construit le dict des cles jenga a injecter dans .vscode/settings.json.
    Ce dict represente UNIQUEMENT les cles que jenga gere — le reste de la
    config user est preserve.
    """
    cfg: Dict[str, Any] = {
        # 1. Association *.jenga -> Python (coloration syntaxique)
        "files.associations": {
            "*.jenga": "python",
        },
        # 2. Analyser les .jenga avec pylance/pyright
        "python.analysis.include": ["**/*.jenga", "**/*.py"],
        # 3. Tolerer les wildcard imports (faux positifs sur .jenga)
        "python.analysis.diagnosticSeverityOverrides": {
            "reportWildcardImportFromLibrary": "none",
            "reportMissingImports": "warning",
            "reportUndefinedVariable": "warning",
        },
    }
    # 4. Ajouter Jenga aux extraPaths pour resolution des imports
    if jenga_home:
        cfg["python.analysis.extraPaths"] = [jenga_home]
    return cfg


def _MergeVSCodeSettings(
    existing: Dict[str, Any], jenga_cfg: Dict[str, Any]
) -> Tuple[Dict[str, Any], bool]:
    """
    Fusionne `jenga_cfg` dans `existing` de maniere non-destructive.
    Pour chaque cle :
      - Si la cle n'existe pas dans existing, on l'ajoute.
      - Si elle existe mais avec une valeur dict : merge recursif (liste = union).
      - Si elle existe mais avec une autre forme : on remplace par la valeur jenga.

    Retourne (dict fusionne, changed bool).
    """
    changed = False
    result = dict(existing)  # copy shallow

    for key, jenga_value in jenga_cfg.items():
        if key not in result:
            result[key] = jenga_value
            changed = True
            continue
        existing_value = result[key]
        # Cas 1 : tous les deux sont dict -> merge profond
        if isinstance(existing_value, dict) and isinstance(jenga_value, dict):
            merged_sub, sub_changed = _MergeVSCodeSettings(existing_value, jenga_value)
            if sub_changed:
                result[key] = merged_sub
                changed = True
        # Cas 2 : tous les deux sont list -> union (preserve l'ordre user d'abord)
        elif isinstance(existing_value, list) and isinstance(jenga_value, list):
            for item in jenga_value:
                if item not in existing_value:
                    existing_value.append(item)
                    changed = True
        # Cas 3 : types incompatibles ou autres -> remplacement (jenga gagne)
        else:
            if existing_value != jenga_value:
                result[key] = jenga_value
                changed = True
    return result, changed


def ConfigureVSCode(workspace_root: Path, force: bool = False,
                    verbose: bool = False) -> bool:
    """
    Genere/maj .vscode/settings.json dans workspace_root.

    Marker d'idempotence : on stocke le fingerprint de la config jenga dans
    une cle privee `_jengaIdeConfigVersion` du settings.json. Si le marker
    est present avec le bon hash, on skip (sauf force=True).

    Retourne True si une maj a ete ecrite, False sinon.
    """
    settings_path = workspace_root / ".vscode" / "settings.json"

    jenga_home = GetJengaHome()
    jenga_cfg  = _GetVSCodeJengaConfig(jenga_home)
    fp_target  = _Fingerprint({"v": _CONFIG_SCHEMA_VERSION, "cfg": jenga_cfg})

    existing = _LoadJsonFile(settings_path)
    if existing is None:
        # Fichier present mais invalide JSON : on ne touche pas (eviter de
        # casser une config user).
        if verbose:
            print(f"[ide-setup] {settings_path} invalide, skip.")
        return False

    # Marker check : si deja a jour, skip.
    marker_key = "_jengaIdeConfigVersion"
    if not force and existing.get(marker_key) == fp_target:
        return False

    # Merge non-destructif des cles jenga.
    merged, changed = _MergeVSCodeSettings(existing, jenga_cfg)
    if not changed and existing.get(marker_key) == fp_target:
        return False

    merged[marker_key] = fp_target
    if _WriteJsonFile(settings_path, merged):
        if verbose:
            print(f"[ide-setup] VSCode settings.json mis a jour : {settings_path}")
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Editeur : LSP universel (pyrightconfig.json)
# Couvre : Neovim+pyright via nvim-lspconfig, Emacs+lsp-mode, Helix,
# Sublime+LSP, Zed, et n'importe quel client LSP qui consomme pyright.
# ─────────────────────────────────────────────────────────────────────────────
def _GetPyrightJengaConfig(jenga_home: Optional[str]) -> Dict[str, Any]:
    """Config pyrightconfig.json (universel LSP)."""
    cfg: Dict[str, Any] = {
        "include": ["**/*.py", "**/*.jenga"],
        "exclude": [
            "Build/**",
            "Externals/**",
            ".vscode/**",
            "**/__pycache__",
            "**/node_modules",
        ],
        "pythonVersion": "3.8",
        "reportMissingImports": "warning",
        "reportUndefinedVariable": "warning",
        "reportWildcardImportFromLibrary": "none",
    }
    if jenga_home:
        cfg["extraPaths"] = [jenga_home]
    return cfg


def ConfigurePyrightConfig(workspace_root: Path, force: bool = False,
                           verbose: bool = False) -> bool:
    """
    Genere/maj pyrightconfig.json a la racine du workspace.

    Comme c'est un fichier dedie a pyright, on assume que jenga le possede
    et on l'ecrit en plein (avec un marker integre). Si l'user veut une
    config custom, il peut la mettre dans .vscode/settings.json (qui gagne
    sur pyrightconfig.json pour pylance).
    """
    pyright_path = workspace_root / "pyrightconfig.json"

    jenga_home = GetJengaHome()
    jenga_cfg  = _GetPyrightJengaConfig(jenga_home)
    fp_target  = _Fingerprint({"v": _CONFIG_SCHEMA_VERSION, "cfg": jenga_cfg})

    existing = _LoadJsonFile(pyright_path)
    if existing is None:
        if verbose:
            print(f"[ide-setup] {pyright_path} invalide, skip.")
        return False

    marker_key = "_jengaIdeConfigVersion"
    if not force and existing.get(marker_key) == fp_target:
        return False

    # Merge : on ecrase nos cles jenga mais on preserve toute cle inconnue
    # que l'user aurait ajoutee (rare pour pyrightconfig mais possible).
    merged = dict(existing)
    for k, v in jenga_cfg.items():
        merged[k] = v
    merged[marker_key] = fp_target

    if _WriteJsonFile(pyright_path, merged):
        if verbose:
            print(f"[ide-setup] pyrightconfig.json mis a jour : {pyright_path}")
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Detection de l'editeur present dans le workspace
# ─────────────────────────────────────────────────────────────────────────────
def DetectEditors(workspace_root: Path) -> List[str]:
    """
    Detecte quels editeurs sont configures dans le workspace.
    Retourne une liste de tags : 'vscode', 'jetbrains', 'sublime', 'neovim',
    'lsp-generic'. Si aucun marqueur n'est trouve, retourne ['vscode', 'lsp-generic']
    par defaut (couvre la majorite des setups).
    """
    found: List[str] = []
    if (workspace_root / ".vscode").exists():
        found.append("vscode")
    if (workspace_root / ".idea").exists() or list(workspace_root.glob("*.iml")):
        found.append("jetbrains")
    if list(workspace_root.glob("*.sublime-project")):
        found.append("sublime")
    if (workspace_root / ".nvim.lua").exists() or \
       (workspace_root / "init.lua").exists():
        found.append("neovim")

    # Toujours generer pyrightconfig.json (universel LSP, ne nuit pas).
    if "lsp-generic" not in found:
        found.append("lsp-generic")

    # Si rien detecte, on assume VSCode (le plus repandu) en plus du LSP generique.
    if not any(e in found for e in ("vscode", "jetbrains", "sublime", "neovim")):
        found.insert(0, "vscode")

    return found


# ─────────────────────────────────────────────────────────────────────────────
# API publique
# ─────────────────────────────────────────────────────────────────────────────
def AutoConfigure(workspace_root: Path, force: bool = False,
                  verbose: bool = False) -> List[str]:
    """
    Configure tous les editeurs detectes pour le workspace_root.

    Args:
        workspace_root: dossier racine du workspace (contenant le .jenga).
        force: si True, regenere meme si le marker indique deja-fait.
        verbose: si True, log chaque fichier touche.

    Returns:
        Liste des editeurs effectivement configures (ceux qui ont eu une
        ecriture). Liste vide si tout etait deja a jour.
    """
    workspace_root = Path(workspace_root)
    if not workspace_root.is_dir():
        return []

    # Opt-out par variable d'environnement (CI / users mecontents).
    if os.environ.get("JENGA_NO_IDE_CONFIG", "").lower() in ("1", "true", "yes"):
        return []

    editors = DetectEditors(workspace_root)
    written: List[str] = []

    if "vscode" in editors:
        if ConfigureVSCode(workspace_root, force=force, verbose=verbose):
            written.append("vscode")

    if "lsp-generic" in editors:
        if ConfigurePyrightConfig(workspace_root, force=force, verbose=verbose):
            written.append("lsp-generic")

    # JetBrains / Sublime / Neovim natifs : a venir en E1+.
    return written


def Describe(workspace_root: Path) -> str:
    """Helper : decrit l'etat de la config IDE pour `jenga ide-setup --info`."""
    workspace_root = Path(workspace_root)
    editors = DetectEditors(workspace_root)
    lines = [
        f"Workspace : {workspace_root}",
        f"Editeurs detectes : {', '.join(editors) or '(aucun)'}",
        f"Jenga home : {GetJengaHome() or '(non resolu)'}",
        f"Schema version : {_CONFIG_SCHEMA_VERSION}",
    ]
    return "\n".join(lines)
