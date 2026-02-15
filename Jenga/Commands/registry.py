#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Registry – Registre central des commandes CLI.
Ce module est dédié à la gestion des commandes et des alias pour éviter les imports circulaires.
Il ne doit importer aucune commande.
"""

from typing import Dict, Type, Callable, List
import sys

# Dictionnaire des commandes (sera rempli par Commands/__init__.py)
COMMANDS: Dict[str, Type] = {}

# Dictionnaire des alias (commande courte -> nom long)
ALIASES: Dict[str, str] = {}


def get_command_class(name: str):
    """Retourne la classe de commande correspondant au nom (avec gestion des alias)."""
    cmd = ALIASES.get(name, name)
    return COMMANDS.get(cmd)


def execute_command(name: str, args: List[str]) -> int:
    """Exécute une commande par son nom."""
    cmd_class = get_command_class(name)
    if not cmd_class:
        print(f"jenga: unknown command '{name}'", file=sys.stderr)
        return 1
    try:
        return cmd_class.Execute(args)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"jenga: error executing command '{name}': {e}", file=sys.stderr)
        if '--verbose' in sys.argv or '-v' in sys.argv:
            import traceback
            traceback.print_exc()
        return 1


__all__ = [
    'COMMANDS', 'ALIASES', 'get_command_class', 'execute_command'
]
