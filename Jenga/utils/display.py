#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Display Utilities
Colorful console output
"""

import sys


class Colors:
    """ANSI color codes"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright foreground colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    
    @staticmethod
    def disable():
        """Disable colors (for non-TTY output)"""
        for attr in dir(Colors):
            if not attr.startswith('_') and attr.isupper():
                setattr(Colors, attr, '')


# Disable colors if not outputting to a terminal
if not sys.stdout.isatty():
    Colors.disable()


class Display:
    """Display utilities for formatted console output"""
    
    @staticmethod
    def success(message: str):
        """Print success message"""
        print(f"{Colors.GREEN}✓{Colors.RESET} {message}")
    
    @staticmethod
    def error(message: str):
        """Print error message"""
        print(f"{Colors.RED}✗{Colors.RESET} {message}", file=sys.stderr)
    
    @staticmethod
    def warning(message: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")
    
    @staticmethod
    def info(message: str):
        """Print info message"""
        print(f"{Colors.CYAN}ℹ{Colors.RESET} {message}")
    
    @staticmethod
    def section(title: str):
        """Print section header"""
        line = "=" * 60
        print(f"\n{Colors.BOLD}{Colors.CYAN}{line}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{title}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{line}{Colors.RESET}\n")
    
    @staticmethod
    def subsection(title: str):
        """Print subsection header"""
        print(f"\n{Colors.BOLD}{title}{Colors.RESET}")
        print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
    
    @staticmethod
    def detail(message: str):
        """Print detail message"""
        print(f"{Colors.DIM}  {message}{Colors.RESET}")
    
    @staticmethod
    def progress(current: int, total: int, message: str = ""):
        """Print progress"""
        percentage = (current / total) * 100 if total > 0 else 0
        bar_length = 40
        filled = int(bar_length * current / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)
        
        print(f"\r{Colors.CYAN}[{bar}]{Colors.RESET} {percentage:3.0f}% {message}", end="", flush=True)
        
        if current >= total:
            print()  # New line when complete


class ProgressBar:
    """Context manager for progress bars"""
    
    def __init__(self, total: int, message: str = "Processing"):
        self.total = total
        self.current = 0
        self.message = message
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            Display.progress(self.total, self.total, f"{self.message} - Complete")
    
    def update(self, increment: int = 1, message: str = None):
        """Update progress"""
        self.current += increment
        msg = message or self.message
        Display.progress(self.current, self.total, msg)
