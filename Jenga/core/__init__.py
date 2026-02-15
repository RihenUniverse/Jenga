#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga.Core – Moteur de build, gestion du cache, résolution de dépendances,
surveillance de fichiers, daemon, etc.
"""

from .Variables import VariableExpander
from .Loader import Loader
from .State import BuildState
from .Cache import Cache
from .DependencyResolver import DependencyResolver
from .Platform import Platform
from .Toolchains import ToolchainManager
from .Builder import Builder
from .Incremental import Incremental
from .Watcher import FileWatcher
from .Daemon import Daemon, DaemonClient, StartDaemon, StopDaemon, DaemonStatus

# Import des builders uniquement via la fonction de résolution
from .Builders import get_builder_class, list_available_builders

__all__ = [
    'VariableExpander',
    'Loader',
    'BuildState',
    'Cache',
    'DependencyResolver',
    'Platform',
    'ToolchainManager',
    'Builder',
    'Incremental',
    'FileWatcher',
    'Daemon', 'DaemonClient', 'StartDaemon', 'StopDaemon', 'DaemonStatus',
    'get_builder_class', 'list_available_builders',
]