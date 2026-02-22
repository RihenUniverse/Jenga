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
    'tvOS': ('Jenga.Core.Builders.Ios', 'IOSBuilder'),
    'watchOS': ('Jenga.Core.Builders.Ios', 'IOSBuilder'),
    'Web': ('Jenga.Core.Builders.Emscripten', 'EmscriptenBuilder'),
    'HarmonyOS': ('Jenga.Core.Builders.HarmonyOs', 'HarmonyOsBuilder'),
    'XboxOne': ('Jenga.Core.Builders.Xbox', 'XboxBuilder'),
    'XboxSeries': ('Jenga.Core.Builders.Xbox', 'XboxBuilder'),
    'Xbox': ('Jenga.Core.Builders.Xbox', 'XboxBuilder'),
    # aliases
    'Macos': ('Jenga.Core.Builders.Macos', 'MacOSBuilder'),
    'IOS': ('Jenga.Core.Builders.Ios', 'IOSBuilder'),
    'TVOS': ('Jenga.Core.Builders.Ios', 'IOSBuilder'),
    'WATCHOS': ('Jenga.Core.Builders.Ios', 'IOSBuilder'),
    'iPadOS': ('Jenga.Core.Builders.Ios', 'IOSBuilder'),
    'visionOS': ('Jenga.Core.Builders.Ios', 'IOSBuilder'),
    'xrOS': ('Jenga.Core.Builders.Ios', 'IOSBuilder'),
    'AppleTV': ('Jenga.Core.Builders.Ios', 'IOSBuilder'),
    'AppleWatch': ('Jenga.Core.Builders.Ios', 'IOSBuilder'),
    'Emscripten': ('Jenga.Core.Builders.Emscripten', 'EmscriptenBuilder'),
}

_APPLE_MOBILE_XCODE_BUILDERS: Dict[str, Tuple[str, str]] = {
    'iOS': ('Jenga.Core.Builders.MacosXcodeBuilder', 'IOSBuilder'),
    'tvOS': ('Jenga.Core.Builders.MacosXcodeBuilder', 'IOSBuilder'),
    'watchOS': ('Jenga.Core.Builders.MacosXcodeBuilder', 'IOSBuilder'),
    'macOS': ('Jenga.Core.Builders.MacosXcodeBuilder', 'MacOSBuilder'),
    # aliases
    'IOS': ('Jenga.Core.Builders.MacosXcodeBuilder', 'IOSBuilder'),
    'TVOS': ('Jenga.Core.Builders.MacosXcodeBuilder', 'IOSBuilder'),
    'WATCHOS': ('Jenga.Core.Builders.MacosXcodeBuilder', 'IOSBuilder'),
    'Macos': ('Jenga.Core.Builders.MacosXcodeBuilder', 'MacOSBuilder'),
    'iPadOS': ('Jenga.Core.Builders.MacosXcodeBuilder', 'IOSBuilder'),
    'visionOS': ('Jenga.Core.Builders.MacosXcodeBuilder', 'IOSBuilder'),
    'xrOS': ('Jenga.Core.Builders.MacosXcodeBuilder', 'IOSBuilder'),
    'AppleTV': ('Jenga.Core.Builders.MacosXcodeBuilder', 'IOSBuilder'),
    'AppleWatch': ('Jenga.Core.Builders.MacosXcodeBuilder', 'IOSBuilder'),
}


def get_builder_class(os_name: str, apple_mobile_mode: str = "direct") -> Optional[Type[Builder]]:
    """
    Retourne la classe du builder pour un système d'exploitation donné.
    Le chargement du module est effectué uniquement lors du premier appel.
    """
    mode = str(apple_mobile_mode or "direct").strip().lower()
    entry = None
    if mode in ("xcode", "xbuilder"):
        entry = _APPLE_MOBILE_XCODE_BUILDERS.get(os_name)
    if entry is None:
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
