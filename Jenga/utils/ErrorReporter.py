#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Système de rapports d'erreurs amélioré avec contexte et suggestions.
"""

import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum

from .Colored import Colored


class ErrorSeverity(Enum):
    """Niveau de sévérité de l'erreur."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class ErrorContext:
    """Contexte d'une erreur."""

    def __init__(self):
        self.file: Optional[str] = None
        self.line: Optional[int] = None
        self.column: Optional[int] = None
        self.project: Optional[str] = None
        self.configuration: Optional[str] = None
        self.target: Optional[str] = None
        self.toolchain: Optional[str] = None
        self.command: Optional[str] = None
        self.working_dir: Optional[str] = None


class JengaError:
    """
    Erreur Jenga enrichie avec contexte et suggestions.
    """

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.severity = severity
        self.error_code = error_code
        self.context = ErrorContext()
        self.suggestions: List[str] = []
        self.related_docs: List[str] = []
        self.original_error: Optional[str] = None

    def add_suggestion(self, suggestion: str):
        """Ajoute une suggestion de résolution."""
        self.suggestions.append(suggestion)
        return self

    def add_doc(self, doc_url: str):
        """Ajoute un lien vers la documentation."""
        self.related_docs.append(doc_url)
        return self

    def set_context(
        self,
        file: Optional[str] = None,
        line: Optional[int] = None,
        project: Optional[str] = None,
        configuration: Optional[str] = None,
        target: Optional[str] = None,
        toolchain: Optional[str] = None,
        command: Optional[str] = None
    ):
        """Définit le contexte de l'erreur."""
        if file:
            self.context.file = file
        if line:
            self.context.line = line
        if project:
            self.context.project = project
        if configuration:
            self.context.configuration = configuration
        if target:
            self.context.target = target
        if toolchain:
            self.context.toolchain = toolchain
        if command:
            self.context.command = command
        return self

    def set_original_error(self, error: str):
        """Définit l'erreur originale (du compilateur par exemple)."""
        self.original_error = error
        return self

    def format(self) -> str:
        """Formate l'erreur pour affichage."""
        lines = []

        # En-tête avec sévérité
        severity_colors = {
            ErrorSeverity.INFO: Colored.CYAN,
            ErrorSeverity.WARNING: Colored.YELLOW,
            ErrorSeverity.ERROR: Colored.RED,
            ErrorSeverity.FATAL: Colored.RED
        }
        color = severity_colors.get(self.severity, Colored.RED)

        header = f"[{self.severity.value}]"
        if self.error_code:
            header += f" {self.error_code}"

        lines.append(color + header + Colored.RESET)

        # Contexte
        ctx_parts = []
        if self.context.project:
            ctx_parts.append(f"Project: {self.context.project}")
        if self.context.configuration:
            ctx_parts.append(f"Config: {self.context.configuration}")
        if self.context.target:
            ctx_parts.append(f"Target: {self.context.target}")
        if self.context.toolchain:
            ctx_parts.append(f"Toolchain: {self.context.toolchain}")

        if ctx_parts:
            lines.append(Colored.BLUE + " | ".join(ctx_parts) + Colored.RESET)

        # Fichier/ligne
        if self.context.file:
            location = self.context.file
            if self.context.line:
                location += f":{self.context.line}"
                if self.context.column:
                    location += f":{self.context.column}"
            lines.append(Colored.CYAN + f"  {location}" + Colored.RESET)

        # Message principal
        lines.append(f"\n  {self.message}\n")

        # Erreur originale (tronquée si trop longue)
        if self.original_error:
            lines.append(Colored.GRAY + "  Original error:" + Colored.RESET)
            error_lines = self.original_error.strip().split('\n')
            for err_line in error_lines[:5]:  # Max 5 lignes
                lines.append(Colored.GRAY + f"    {err_line}" + Colored.RESET)
            if len(error_lines) > 5:
                lines.append(Colored.GRAY + f"    ... ({len(error_lines) - 5} more lines)" + Colored.RESET)
            lines.append("")

        # Suggestions
        if self.suggestions:
            lines.append(Colored.GREEN + "  Suggestions:" + Colored.RESET)
            for i, suggestion in enumerate(self.suggestions, 1):
                lines.append(f"    {i}. {suggestion}")
            lines.append("")

        # Documentation
        if self.related_docs:
            lines.append(Colored.CYAN + "  Documentation:" + Colored.RESET)
            for doc in self.related_docs:
                lines.append(f"    - {doc}")
            lines.append("")

        # Commande exécutée
        if self.context.command:
            lines.append(Colored.GRAY + f"  Command: {self.context.command}" + Colored.RESET)

        return '\n'.join(lines)


class ErrorReporter:
    """
    Gestionnaire centralisé de rapports d'erreur.
    """

    # Patterns d'erreurs connues avec suggestions
    ERROR_PATTERNS = {
        r"file not found|No such file": {
            "suggestions": [
                "Vérifiez que le fichier existe",
                "Vérifiez les chemins relatifs/absolus",
                "Vérifiez la casse du nom de fichier (sensible sur Linux)"
            ]
        },
        r"undefined reference|undefined symbol": {
            "suggestions": [
                "Ajoutez la bibliothèque manquante avec links(['libname'])",
                "Vérifiez que tous les fichiers .cpp sont inclus",
                "Ajoutez le chemin de la bibliothèque avec libdirs(['path'])"
            ]
        },
        r"cannot find -l(\w+)": {
            "suggestions": [
                "Installez la bibliothèque manquante",
                "Ajoutez le chemin avec libdirs(['/path/to/lib'])",
                "Vérifiez le nom de la bibliothèque"
            ]
        },
        r"permission denied|Access is denied": {
            "suggestions": [
                "Vérifiez les permissions du fichier/dossier",
                "Fermez les programmes qui utilisent le fichier",
                "Exécutez avec les privilèges appropriés"
            ]
        },
        r"no such toolchain": {
            "suggestions": [
                "Listez les toolchains disponibles : jenga config toolchain list",
                "Enregistrez votre toolchain : jenga config toolchain add <name> <file>",
                "Vérifiez l'orthographe du nom du toolchain"
            ],
            "docs": ["docs/CUSTOM_TOOLCHAINS.md"]
        },
        r"X11.*not found|Xlib\.h.*not found": {
            "suggestions": [
                "Installez les headers X11 : sudo apt install libx11-dev",
                "Configurez un sysroot avec X11",
                "Enregistrez le sysroot : jenga config sysroot add <name> <path>"
            ],
            "docs": ["docs/CROSS_COMPILATION.md"]
        }
    }

    @staticmethod
    def parse_compiler_error(error_output: str, project: Optional[str] = None) -> JengaError:
        """
        Parse une erreur de compilateur et crée un JengaError enrichi.

        Args:
            error_output: Sortie d'erreur du compilateur
            project: Nom du projet en cours de compilation

        Returns:
            JengaError enrichi avec contexte et suggestions
        """
        # Extraire le fichier et la ligne
        file_match = re.search(r'(\S+?):(\d+):(\d+):', error_output)
        file_path = None
        line_num = None
        col_num = None

        if file_match:
            file_path = file_match.group(1)
            line_num = int(file_match.group(2))
            col_num = int(file_match.group(3))

        # Extraire le message principal
        error_lines = error_output.strip().split('\n')
        main_message = error_lines[0] if error_lines else "Compilation failed"

        # Déterminer la sévérité
        severity = ErrorSeverity.ERROR
        if "warning:" in error_output.lower():
            severity = ErrorSeverity.WARNING
        elif "fatal error:" in error_output.lower():
            severity = ErrorSeverity.FATAL

        # Créer l'erreur
        error = JengaError(main_message, severity=severity, error_code="COMPILE_ERROR")
        error.set_context(file=file_path, line=line_num, project=project)
        error.set_original_error(error_output)

        # Ajouter suggestions basées sur les patterns
        for pattern, info in ErrorReporter.ERROR_PATTERNS.items():
            if re.search(pattern, error_output, re.IGNORECASE):
                for suggestion in info.get("suggestions", []):
                    error.add_suggestion(suggestion)
                for doc in info.get("docs", []):
                    error.add_doc(doc)
                break

        return error

    @staticmethod
    def report_build_error(
        message: str,
        project: Optional[str] = None,
        configuration: Optional[str] = None,
        target: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ) -> JengaError:
        """
        Rapporte une erreur de build avec contexte.
        """
        error = JengaError(message, severity=ErrorSeverity.ERROR, error_code="BUILD_ERROR")
        error.set_context(project=project, configuration=configuration, target=target)

        if suggestions:
            for suggestion in suggestions:
                error.add_suggestion(suggestion)

        return error

    @staticmethod
    def report_config_error(message: str, suggestions: Optional[List[str]] = None) -> JengaError:
        """
        Rapporte une erreur de configuration.
        """
        error = JengaError(message, severity=ErrorSeverity.ERROR, error_code="CONFIG_ERROR")

        if suggestions:
            for suggestion in suggestions:
                error.add_suggestion(suggestion)

        error.add_doc("docs/README.md")

        return error

    @staticmethod
    def print_error(error: JengaError):
        """Affiche une erreur formatée."""
        print(error.format())
