#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Reporter
Build logging and reporting
"""

from .display import Display, Colors
import time


class Reporter:
    """Build reporter for logging and progress"""
    
    verbose = False
    start_time = None
    
    @staticmethod
    def start():
        """Start build timer"""
        Reporter.start_time = time.time()
    
    @staticmethod
    def end():
        """End build and print elapsed time"""
        if Reporter.start_time:
            elapsed = time.time() - Reporter.start_time
            Display.info(f"Build completed in {elapsed:.2f}s")
    
    @staticmethod
    def section(title: str):
        """Print section"""
        Display.section(title)
    
    @staticmethod
    def subsection(title: str):
        """Print subsection"""
        Display.subsection(title)
    
    @staticmethod
    def success(message: str):
        """Print success"""
        Display.success(message)
    
    @staticmethod
    def error(message: str):
        """Print error"""
        Display.error(message)
    
    @staticmethod
    def warning(message: str):
        """Print warning"""
        Display.warning(message)
    
    @staticmethod
    def info(message: str):
        """Print info"""
        Display.info(message)
    
    @staticmethod
    def detail(message: str):
        """Print detail (only in verbose mode)"""
        if Reporter.verbose:
            Display.detail(message)
    
    @staticmethod
    def debug(message: str):
        """Print debug message (only in verbose mode)"""
        if Reporter.verbose:
            print(f"{Colors.DIM}[DEBUG] {message}{Colors.RESET}")
