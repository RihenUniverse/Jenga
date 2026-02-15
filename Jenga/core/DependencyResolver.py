#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DependencyResolver – Ordonnancement topologique des projets.
Détecte les cycles et fournit l'ordre de build.
Toutes les méthodes publiques sont en PascalCase.
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from collections import deque, defaultdict

# ✅ Import absolu cohérent avec l'API utilisateur
from Jenga.Core import Api


class DependencyResolver:
    """
    Résout les dépendances entre projets d'un workspace.
    Utilise un tri topologique (algorithme de Kahn) sur le graphe des dépendances.
    """

    @staticmethod
    def ResolveBuildOrder(workspace: Any, targetProject: Optional[str] = None) -> List[str]:
        """
        Retourne la liste ordonnée des noms de projets à compiler.
        Si targetProject est spécifié, ne retourne que les dépendances de ce projet.
        Lève une exception en cas de cycle.
        """
        # 1. Construire le graphe des dépendances (prédécesseurs)
        pred: Dict[str, Set[str]] = {}
        all_projects = set(workspace.projects.keys())

        for name, proj in workspace.projects.items():
            deps = set(proj.dependsOn)
            deps = {d for d in deps if d in all_projects}
            pred[name] = deps

        # Si on cible un projet spécifique, on réduit le graphe aux projets concernés
        if targetProject:
            if targetProject not in pred:
                raise ValueError(f"Target project '{targetProject}' not found in workspace")
            # On veut tous les ancêtres (dépendances directes et indirectes)
            visited = set()
            stack = [targetProject]
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                visited.add(node)
                stack.extend(pred[node])
            # Restreindre le graphe aux nœuds visités
            pred = {k: {d for d in v if d in visited} for k, v in pred.items() if k in visited}

        # 2. Construire le graphe des successeurs
        succ: Dict[str, Set[str]] = {node: set() for node in pred}
        for node, deps in pred.items():
            for dep in deps:
                succ[dep].add(node)

        # 3. Tri topologique (Kahn) en utilisant les prédécesseurs
        #    degré entrant = nombre de prédécesseurs
        in_degree = {node: len(pred[node]) for node in pred}
        queue = deque([node for node in pred if in_degree[node] == 0])
        order = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for neighbor in succ[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(pred):
            # Détection de cycle
            cycles = DependencyResolver._FindCycles(pred)
            raise RuntimeError(f"Circular dependencies detected: {cycles}")

        return order

    @staticmethod
    def _FindCycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
        """Détecte les cycles dans le graphe des prédécesseurs."""
        cycles = []
        visited = set()
        stack = []

        def dfs(node, path):
            if node in stack:
                idx = stack.index(node)
                cycles.append(stack[idx:] + [node])
                return
            if node in visited:
                return
            visited.add(node)
            stack.append(node)
            for neighbor in graph.get(node, []):
                dfs(neighbor, path)
            stack.pop()

        for node in graph:
            dfs(node, [])
        return cycles

    @staticmethod
    def GetDependencyTree(workspace: Any, rootProject: str) -> Dict[str, List[str]]:
        """
        Retourne un arbre de dépendances (récursif) pour un projet racine.
        """
        result = {}
        visited = set()

        def recurse(name):
            if name in visited:
                return
            visited.add(name)
            proj = workspace.projects.get(name)
            if not proj:
                result[name] = []
                return
            deps = [d for d in proj.dependsOn if d in workspace.projects]
            result[name] = deps
            for d in deps:
                recurse(d)

        recurse(rootProject)
        return result

    @staticmethod
    def ValidateDependencies(workspace: Any) -> List[str]:
        """
        Vérifie que toutes les dépendances existent et qu'il n'y a pas de cycle.
        Retourne une liste d'erreurs (vide si tout est OK).
        """
        errors = []
        all_projects = set(workspace.projects.keys())

        for name, proj in workspace.projects.items():
            for dep in proj.dependsOn:
                if dep not in all_projects:
                    errors.append(f"Project '{name}' depends on unknown project '{dep}'")
                if dep == name:
                    errors.append(f"Project '{name}' depends on itself")

        if not errors:
            try:
                DependencyResolver.ResolveBuildOrder(workspace)
            except RuntimeError as e:
                errors.append(str(e))

        return errors