#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga.Utils – Utilitaires généraux : console colorée, système de fichiers,
processus, rapports, affichage.
"""

from .Colored import Colored
from .FileSystem import FileSystem
from .Process import Process, ProcessResult
from .Reporter import (
    Report, BuildReport, TestReport,
    CreateBuildReport, CreateTestReport,
    GenerateReportFromData, ExportJUnitXml,
    Reporter, BuildLogger, BuildCoordinator
)
from .Display import Display, ProgressBar, Spinner

# Aliases DSL (lowercase, one word)
printcolor = Colored.Print
printerror = Colored.PrintError
printsuccess = Colored.PrintSuccess
printwarning = Colored.PrintWarning
printinfo = Colored.PrintInfo

__all__ = [
    'Colored',
    'FileSystem',
    'Process', 'ProcessResult',
    'Report', 'BuildReport', 'TestReport',
    'CreateBuildReport', 'CreateTestReport',
    'GenerateReportFromData', 'ExportJUnitXml',
    'Reporter', 'BuildLogger', 'BuildCoordinator',
    'Display', 'ProgressBar', 'Spinner',
    'printcolor', 'printerror', 'printsuccess', 'printwarning', 'printinfo',
]