#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Display – Pretty console output: trees, progress bars, tables, headers.
All public methods are PascalCase; private helpers are module‑level functions.
"""

import sys
import time
from typing import List, Any, Optional, Union, Iterator
from .Colored import Colored

# ---------------------------------------------------------------------------
# Private helpers (module level) – _PascalCase
# ---------------------------------------------------------------------------

def _BuildTreeLines(
    root: Any,
    childrenGetter: callable,
    labelGetter: callable,
    prefix: str = "",
    isLast: bool = True,
    isRoot: bool = True,
    maxDepth: int = -1,
    currentDepth: int = 0,
    colored: bool = True,
    color: Optional[str] = None
) -> List[str]:
    """Recursively build tree lines."""
    lines = []
    if not isRoot:
        connector = "└─ " if isLast else "├─ "
        line = prefix + connector
        if colored and color:
            label = Colored.Colorize(labelGetter(root), color=color)
        else:
            label = labelGetter(root)
        lines.append(line + label)
        prefix += "    " if isLast else "│   "

    if maxDepth >= 0 and currentDepth >= maxDepth:
        return lines

    children = childrenGetter(root)
    for idx, child in enumerate(children):
        is_last_child = (idx == len(children) - 1)
        lines.extend(_BuildTreeLines(
            child, childrenGetter, labelGetter,
            prefix, is_last_child, False,
            maxDepth, currentDepth + 1,
            colored, color
        ))
    return lines

# ---------------------------------------------------------------------------
# Display class – all methods static
# ---------------------------------------------------------------------------

class Display:

    @staticmethod
    def PrintTree(
        root: Any,
        childrenGetter: callable,
        labelGetter: callable,
        maxDepth: int = -1,
        colored: bool = True,
        color: Optional[str] = None
    ) -> None:
        """Print a tree structure."""
        lines = _BuildTreeLines(root, childrenGetter, labelGetter,
                                isRoot=True, maxDepth=maxDepth,
                                colored=colored, color=color)
        for line in lines:
            print(line)

    @staticmethod
    def PrintTable(
        rows: List[List[str]],
        headers: Optional[List[str]] = None,
        colored: bool = True,
        headerColor: str = "white",
        rowColors: Optional[List[Optional[str]]] = None
    ) -> None:
        """Print a formatted table."""
        header_colors = [headerColor] * len(headers) if headers else None
        table = Colored.FormatTable(rows, headers,
                                    colors=rowColors,
                                    headerColors=header_colors)
        print(table)

    @staticmethod
    def PrintHeader(text: str, char: str = "=", width: int = 80,
                    color: str = "white") -> None:
        """Print a centered header line."""
        display_text = f" {text} "
        if Colored.SupportsColor():
            display_text = Colored.Colorize(display_text, bold=True, color=color)
        total_pad = max(0, width - Colored.LenWithoutColors(display_text))
        left = total_pad // 2
        right = total_pad - left
        line = char * left + display_text + char * right
        print(line)

    @staticmethod
    def PrintSeparator(char: str = "-", width: int = 80, dim: bool = True) -> None:
        """Print a separator line."""
        line = char * width
        if dim and Colored.SupportsColor():
            line = Colored.Colorize(line, dim=True)
        print(line)

    # -----------------------------------------------------------------------
    # Shortcuts for common colored messages (PascalCase)
    # -----------------------------------------------------------------------

    @staticmethod
    def Success(message: str) -> None:
        """Print success message with green ✓."""
        Colored.Print(f"{Colored.Colorize('✓', color='green')} {message}")

    @staticmethod
    def Error(message: str) -> None:
        """Print error message in red to stderr."""
        Colored.PrintError(f"{Colored.Colorize('✗', color='red')} {message}", color=None)

    @staticmethod
    def Warning(message: str) -> None:
        """Print warning message in yellow."""
        Colored.Print(f"{Colored.Colorize('⚠', color='yellow')} {message}")

    @staticmethod
    def Info(message: str) -> None:
        """Print info message in cyan."""
        Colored.Print(f"{Colored.Colorize('ℹ', color='cyan')} {message}")

    @staticmethod
    def Section(title: str) -> None:
        """Print section header."""
        line = "=" * 60
        print()
        print(Colored.Colorize(line, bold=True, color='cyan'))
        print(Colored.Colorize(title, bold=True, color='cyan'))
        print(Colored.Colorize(line, bold=True, color='cyan'))
        print()

    @staticmethod
    def Subsection(title: str) -> None:
        """Print subsection header."""
        print()
        print(Colored.Colorize(title, bold=True))
        print(Colored.Colorize('-' * 60, dim=True))

    @staticmethod
    def Detail(message: str) -> None:
        """Print detail message in dim."""
        print(f"  {Colored.Colorize(message, dim=True)}")

    @staticmethod
    def Debug(message: str) -> None:
        """Print debug message (only if verbose enabled via Reporter)."""
        # La gestion du verbose est faite par Reporter, ici on fournit juste le format
        print(f"{Colored.Colorize('[DEBUG]', dim=True)} {message}")

    @staticmethod
    def PrintBanner(version: str = "2.0.0") -> None:
        """Print Jenga banner with exact design."""
        banner = f"""
{Colored.Colorize('╔══════════════════════════════════════════════════════════════════╗', color='cyan')}
{Colored.Colorize('║', color='cyan')}                                                                  {Colored.Colorize('║', color='cyan')}
{Colored.Colorize('║', color='cyan')}           {Colored.Colorize('     ██╗███████╗███╗   ██╗ ██████╗  █████╗', bold=True, color='magenta')}             {Colored.Colorize('║', color='cyan')}
{Colored.Colorize('║', color='cyan')}           {Colored.Colorize('     ██║██╔════╝████╗  ██║██╔════╝ ██╔══██╗', bold=True, color='magenta')}            {Colored.Colorize('║', color='cyan')}
{Colored.Colorize('║', color='cyan')}           {Colored.Colorize('     ██║█████╗  ██╔██╗ ██║██║  ███╗███████║', bold=True, color='magenta')}            {Colored.Colorize('║', color='cyan')}
{Colored.Colorize('║', color='cyan')}           {Colored.Colorize('██   ██║██╔══╝  ██║╚██╗██║██║   ██║██╔══██║', bold=True, color='magenta')}            {Colored.Colorize('║', color='cyan')}
{Colored.Colorize('║', color='cyan')}           {Colored.Colorize('╚█████╔╝███████╗██║ ╚████║╚██████╔╝██║  ██║', bold=True, color='magenta')}            {Colored.Colorize('║', color='cyan')}
{Colored.Colorize('║', color='cyan')}           {Colored.Colorize(' ╚════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝', bold=True, color='magenta')}            {Colored.Colorize('║', color='cyan')}
{Colored.Colorize('║', color='cyan')}                                                                  {Colored.Colorize('║', color='cyan')}
{Colored.Colorize('║', color='cyan')}             {Colored.Colorize(f'Multi-platform C/C++ Build System v{version}', bold=True)}             {Colored.Colorize('║', color='cyan')}
{Colored.Colorize('║', color='cyan')}                                                                  {Colored.Colorize('║', color='cyan')}
{Colored.Colorize('╚══════════════════════════════════════════════════════════════════╝', color='cyan')}
"""
        try:
            print(banner)
        except UnicodeEncodeError:
            # Fallback for legacy Windows consoles using non-UTF encodings.
            print(f"Jenga - Multi-platform C/C++ Build System v{version}")

    @staticmethod
    def PrintVersion(version: str = "1.0.0", copyright_year: str = "2025", 
                     copyright_holder: str = "Rihen", license_type: str = "Proprietary") -> None:
        """Print version information."""
        version_info = f"""
{Colored.Colorize('Jenga Build System', bold=True)}
Version: {Colored.Colorize(version, color='green')}
Python: {sys.version.split()[0]}
Platform: {sys.platform}
Copyright © {copyright_year} {copyright_holder}
License: {license_type}
"""
        print(version_info)

    @staticmethod
    def Prompt(question: str, default: str = "") -> str:
        """Affiche une question et lit la réponse de l'utilisateur."""
        if default:
            prompt = f"{question} [{default}]: "
        else:
            prompt = f"{question}: "
        try:
            response = input(prompt).strip()
            if not response:
                return default
            return response
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(1)

    @staticmethod
    def PromptPassword(question: str, allow_empty: bool = False) -> str:
        """
        Affiche une question et lit un mot de passe sans écho.
        Si `allow_empty` est True, une réponse vide est autorisée.
        """
        try:
            import getpass
            password = getpass.getpass(prompt=f"{question}: ")
            if not allow_empty and not password:
                print("Password cannot be empty.", file=sys.stderr)
                return Display.PromptPassword(question, allow_empty)
            return password
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(1)

    @staticmethod
    def PromptChoice(question: str, choices: list, default: str = None) -> str:
        """Display a numbered list and let user pick one."""
        print(f"\n{question}:")
        for i, choice in enumerate(choices, 1):
            marker = " *" if default and choice == default else ""
            print(f"  {i}. {choice}{marker}")
        while True:
            default_idx = choices.index(default) + 1 if default and default in choices else 1
            response = Display.Prompt("Selection", default=str(default_idx))
            try:
                idx = int(response) - 1
                if 0 <= idx < len(choices):
                    return choices[idx]
            except ValueError:
                for c in choices:
                    if c.lower() == response.lower():
                        return c
            print(f"  Please enter 1-{len(choices)}")

    @staticmethod
    def PromptMultiChoice(question: str, choices: list, defaults: list = None) -> list:
        """Display a numbered list and let user pick multiple."""
        if defaults is None:
            defaults = []
        print(f"\n{question}:")
        for i, choice in enumerate(choices, 1):
            mark = "x" if choice in defaults else " "
            print(f"  [{mark}] {i}. {choice}")
        print("  Enter numbers separated by commas, or 'all'")
        response = Display.Prompt("Selection", default=",".join(str(choices.index(d)+1) for d in defaults if d in choices))
        if response.lower() == 'all':
            return list(choices)
        try:
            indices = [int(x.strip()) - 1 for x in response.split(',') if x.strip()]
            selected = [choices[i] for i in indices if 0 <= i < len(choices)]
            return selected if selected else defaults
        except (ValueError, IndexError):
            return defaults

    @staticmethod
    def PromptYesNo(question: str, default: bool = True) -> bool:
        """Ask a yes/no question."""
        hint = "Y/n" if default else "y/N"
        response = Display.Prompt(f"{question} [{hint}]", default="y" if default else "n")
        return response.lower() in ('y', 'yes', 'oui', 'o', '')

    # -----------------------------------------------------------------------
    # Lowercase aliases for compatibility with existing code
    # -----------------------------------------------------------------------

    @staticmethod
    def section(title: str) -> None:
        """Alias for Section()."""
        Display.Section(title)

    @staticmethod
    def error(message: str) -> None:
        """Alias for Error()."""
        Display.Error(message)

    @staticmethod
    def warning(message: str) -> None:
        """Alias for Warning()."""
        Display.Warning(message)

    @staticmethod
    def info(message: str) -> None:
        """Alias for Info()."""
        Display.Info(message)

    @staticmethod
    def success(message: str) -> None:
        """Alias for Success()."""
        Display.Success(message)

    @staticmethod
    def detail(message: str) -> None:
        """Alias for Detail()."""
        Display.Detail(message)

    @staticmethod
    def debug(message: str) -> None:
        """Alias for Debug()."""
        Display.Debug(message)

    @staticmethod
    def print_banner(version: str = "1.0.0") -> None:
        """Alias for PrintBanner()."""
        Display.PrintBanner(version)

    @staticmethod
    def print_version(version: str = "1.0.0", copyright_year: str = "2025", 
                      copyright_holder: str = "Rihen", license_type: str = "Proprietary") -> None:
        """Alias for PrintVersion()."""
        Display.PrintVersion(version, copyright_year, copyright_holder, license_type)

# ---------------------------------------------------------------------------
# ProgressBar and Spinner (standalone classes, camelCase fields)
# ---------------------------------------------------------------------------

class ProgressBar:
    """Simple progress bar with percentage, bar, and optional message."""
    def __init__(self, total: int, width: int = 50, prefix: str = "",
                 suffix: str = "", fill: str = "█", empty: str = "░",
                 stream=sys.stderr):
        self.total = total
        self.width = width
        self.prefix = prefix
        self.suffix = suffix
        self.fill = fill
        self.empty = empty
        self.stream = stream
        self._current = 0
        self._startTime = time.time()

    def Update(self, advance: int = 1, msg: str = "") -> None:
        self._current += advance
        self._current = min(self._current, self.total)
        self._Print(msg)

    def Set(self, value: int, msg: str = "") -> None:
        self._current = max(0, min(value, self.total))
        self._Print(msg)

    def _Print(self, msg: str = "") -> None:
        percent = self._current / self.total if self.total > 0 else 1.0
        filled_len = int(self.width * percent)
        bar = self.fill * filled_len + self.empty * (self.width - filled_len)
        elapsed = time.time() - self._startTime
        elapsed_str = f"{elapsed:.1f}s" if elapsed < 60 else f"{int(elapsed // 60)}m{int(elapsed % 60)}s"
        line = f"\r{self.prefix} |{bar}| {self._current}/{self.total} ({percent*100:.1f}%) {elapsed_str} {msg}{self.suffix}"
        if self._current == self.total:
            line += "\n"
        self.stream.write(line)
        self.stream.flush()

    def Finish(self, msg: str = "Done") -> None:
        if self._current < self.total:
            self.Set(self.total, msg)
        else:
            self._Print(msg)

class Spinner:
    """Simple CLI spinner for indeterminate progress."""
    def __init__(self, msg: str = "Working...", stream=sys.stderr):
        self.msg = msg
        self.stream = stream
        self._frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._index = 0
        self._running = False

    def Start(self) -> None:
        self._running = True
        self._Spin()

    def _Spin(self) -> None:
        if not self._running:
            return
        self.stream.write(f"\r{self._frames[self._index]} {self.msg}")
        self.stream.flush()
        self._index = (self._index + 1) % len(self._frames)

    def Update(self) -> None:
        if self._running:
            self._Spin()

    def Stop(self, finalMsg: Optional[str] = None) -> None:
        self._running = False
        if finalMsg:
            self.stream.write(f"\r{finalMsg}\n")
        else:
            self.stream.write("\rDone.\n")
        self.stream.flush()
