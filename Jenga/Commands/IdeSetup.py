#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Commande 'jenga ide-setup' - Configure l'editeur de code pour les projets jenga.

Genere/met a jour les fichiers de config IDE necessaires pour que les
fichiers `*.jenga` soient reconnus comme du Python (coloration syntaxique +
autocomplete sur les fonctions DSL).

Editeurs supportes :
  - VSCode / Cursor / Windsurf  : .vscode/settings.json
  - LSP universel               : pyrightconfig.json
    (couvre Neovim+pyright, Emacs+lsp-mode, Helix, Sublime+LSP, Zed)

Usage :
  jenga ide-setup                       # auto-detecte + applique
  jenga ide-setup --force               # regenere meme si deja a jour
  jenga ide-setup --info                # affiche l'etat sans rien ecrire
  jenga ide-setup --editor vscode       # cible un editeur
  jenga ide-setup --editor lsp          # cible LSP universel
"""

import argparse
from pathlib import Path

from ..Core.IDEConfigurator import (
    AutoConfigure, ConfigureVSCode, ConfigurePyrightConfig,
    DetectEditors, Describe, GetJengaHome,
)
from ..Utils import Colored, FileSystem


class IdeSetupCommand:
    """
    Configure l'IDE du user pour les fichiers .jenga.

    Strategies :
      - MERGE NON-DESTRUCTIF : les cles user existantes sont preservees.
      - IDEMPOTENT : un marker evite de re-ecrire si la config est a jour.
      - SILENCIEUX en auto-mode (appele depuis jenga build), VERBEUX en CLI.
    """

    @staticmethod
    def Execute(args: list) -> int:
        parser = argparse.ArgumentParser(
            prog="jenga ide-setup",
            description="Configure l'editeur de code pour les fichiers .jenga"
        )
        parser.add_argument(
            "--editor",
            choices=["auto", "vscode", "lsp", "all"],
            default="auto",
            help="Cible un editeur (defaut: auto-detection)"
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Regenere meme si la config semble deja a jour"
        )
        parser.add_argument(
            "--info",
            action="store_true",
            help="Affiche l'etat de la config sans rien ecrire"
        )
        parser.add_argument(
            "--workspace",
            help="Chemin du workspace (defaut: dossier courant ou parent .jenga)"
        )

        parsed = parser.parse_args(args)

        # Resolution du workspace root.
        if parsed.workspace:
            workspace_root = Path(parsed.workspace).resolve()
        else:
            entry_file = FileSystem.FindWorkspaceEntry(Path.cwd())
            workspace_root = entry_file.parent if entry_file else Path.cwd()

        # --info : juste lister l'etat, pas d'ecriture.
        if parsed.info:
            Colored.PrintInfo("Etat de la configuration IDE jenga :")
            print()
            print(Describe(workspace_root))
            return 0

        # Verifier Jenga home (sanity check pour les extraPaths).
        jenga_home = GetJengaHome()
        if jenga_home is None:
            Colored.PrintWarning(
                "[ide-setup] Impossible de resoudre le chemin du package Jenga. "
                "Les imports `from Jenga import *` ne seront peut-etre pas resolus "
                "par pyright. Cela peut arriver si jenga tourne sans installation "
                "site-packages standard."
            )

        # Dispatch par editeur.
        written = []
        if parsed.editor in ("auto", "all"):
            written = AutoConfigure(workspace_root, force=parsed.force, verbose=True)
        elif parsed.editor == "vscode":
            if ConfigureVSCode(workspace_root, force=parsed.force, verbose=True):
                written.append("vscode")
        elif parsed.editor == "lsp":
            if ConfigurePyrightConfig(workspace_root, force=parsed.force, verbose=True):
                written.append("lsp-generic")

        if not written:
            Colored.PrintInfo(
                "[ide-setup] Aucune mise a jour necessaire (config IDE deja a jour). "
                "Utiliser --force pour regenerer."
            )
        else:
            Colored.PrintSuccess(
                f"[ide-setup] Config IDE mise a jour : {', '.join(written)}"
            )
            Colored.PrintInfo(
                "Astuce : recharger la fenetre de l'editeur (Ctrl+Shift+P -> "
                "Reload Window dans VSCode) pour que les changements prennent effet."
            )

        return 0
