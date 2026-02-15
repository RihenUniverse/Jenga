#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga.Core.Builders – Implémentations spécifiques par plateforme.
Ce module n'importe aucun builder directement pour éviter :
- Les erreurs d'import si un builder n'est pas encore implémenté.
- Les imports circulaires.
- Le chargement inutile de modules pour des plateformes non utilisées.

Utiliser get_builder_class(platform_name) pour obtenir la classe du builder.
"""

import importlib
from typing import Optional, Type, Dict, Tuple
from ..Builder import Builder


# Mapping OS name -> (module path, builder class)
_BUILDERS: Dict[str, Tuple[str, str]] = {
    'Windows': ('Jenga.Core.Builders.Windows', 'WindowsBuilder'),
    'Linux': ('Jenga.Core.Builders.Linux', 'LinuxBuilder'),
    'macOS': ('Jenga.Core.Builders.Macos', 'MacOSBuilder'),
    'Android': ('Jenga.Core.Builders.Android', 'AndroidBuilder'),
    'iOS': ('Jenga.Core.Builders.Ios', 'IOSBuilder'),
    'Web': ('Jenga.Core.Builders.Emscripten', 'EmscriptenBuilder'),
    'HarmonyOS': ('Jenga.Core.Builders.HarmonyOs', 'HarmonyOsBuilder'),
    'XboxOne': ('Jenga.Core.Builders.Xbox', 'XboxBuilder'),
    'XboxSeries': ('Jenga.Core.Builders.Xbox', 'XboxBuilder'),
    'Xbox': ('Jenga.Core.Builders.Xbox', 'XboxBuilder'),
    # aliases
    'Macos': ('Jenga.Core.Builders.Macos', 'MacOSBuilder'),
    'IOS': ('Jenga.Core.Builders.Ios', 'IOSBuilder'),
    'Emscripten': ('Jenga.Core.Builders.Emscripten', 'EmscriptenBuilder'),
}


def get_builder_class(os_name: str) -> Optional[Type[Builder]]:
    """
    Retourne la classe du builder pour un système d'exploitation donné.
    Le chargement du module est effectué uniquement lors du premier appel.
    """
    entry = _BUILDERS.get(os_name)
    if not entry:
        return None
    module_path, class_name = entry
    try:
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        # Éviter d'imprimer ici car cela pourrait polluer la console
        # lors de l'import normal. Le problème sera remonté lors de l'appel.
        return None


def list_available_builders() -> list:
    """Retourne la liste des noms de builders potentiellement disponibles."""
    return sorted(set(_BUILDERS.keys()))


__all__ = ['get_builder_class', 'list_available_builders']
