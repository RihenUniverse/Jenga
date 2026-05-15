#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Commands – Dispatcher des commandes au niveau Core.
Ce fichier est différent de Commands/__init__.py (qui est le registre CLI).
Il est utilisé par le Daemon pour exécuter des commandes internes.
"""

from typing import Dict, Any, Callable, Optional
import inspect


# ✅ Import absolu cohérent avec l'API utilisateur
from Jenga.Core import Api

class CommandDispatcher:
    """
    Dispatche les commandes internes vers les fonctions d'exécution.
    Utilisé par le Daemon.
    """

    def __init__(self, workspace, builder=None):
        self.workspace = workspace
        self.builder = builder
        self._commands = {}

    def register(self, name: str, func: Callable):
        """Enregistre une commande."""
        self._commands[name] = func

    def register_module(self, module):
        """Enregistre toutes les fonctions d'un module."""
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if name.startswith('cmd_'):
                cmd_name = name[4:]  # enlève 'cmd_'
                self.register(cmd_name, func)

    def execute(self, command: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Exécute une commande et retourne le résultat."""
        if command not in self._commands:
            return {'status': 'error', 'message': f'Unknown command: {command}'}
        try:
            result = self._commands[command](self.workspace, self.builder, **(args or {}))
            if isinstance(result, dict):
                return result
            return {'status': 'ok', 'result': result}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}