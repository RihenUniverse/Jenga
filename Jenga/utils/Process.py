#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Process – Execute external commands and capture output.
All public methods are PascalCase; private helpers are module‑level functions.
"""

import subprocess
import shlex
import os
import signal
import sys
import shutil
from typing import List, Optional, Union, Dict, Any
from pathlib import Path
from threading import Timer

# ---------------------------------------------------------------------------
# Private helpers (module level) – _PascalCase
# ---------------------------------------------------------------------------

def _FormatCommand(args: Union[str, List[str]]) -> str:
    """Convert command to a single string for logging."""
    if isinstance(args, str):
        return args
    return " ".join(shlex.quote(str(a)) for a in args)

def _KillProcess(proc: subprocess.Popen) -> None:
    """Kill process and its children."""
    if sys.platform == "win32":
        proc.kill()
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except AttributeError:
            proc.kill()

# ---------------------------------------------------------------------------
# ProcessResult – Dataclass (camelCase fields)
# ---------------------------------------------------------------------------

class ProcessResult:
    """Result of a command execution."""
    def __init__(self, returnCode: int, stdout: str, stderr: str, command: str):
        self.returnCode = returnCode
        self.stdout = stdout
        self.stderr = stderr
        self.command = command

    @property
    def succeeded(self) -> bool:
        return self.returnCode == 0

    @property
    def failed(self) -> bool:
        return self.returnCode != 0

    def __repr__(self) -> str:
        return f"<ProcessResult cmd='{self.command}' return={self.returnCode}>"

# ---------------------------------------------------------------------------
# Process class – all methods static
# ---------------------------------------------------------------------------

class Process:

    @staticmethod
    def ExecuteCommand(
        args: Union[str, List[str]],
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        captureOutput: bool = True,
        shell: bool = False,
        check: bool = False,
        input: Optional[str] = None,
        silent: bool = False,
    ) -> ProcessResult:
        """
        Execute a command and return result.
        - captureOutput: if True, capture stdout/stderr; else inherit from parent.
        - shell: use system shell (not recommended for security).
        - check: raise exception if return code != 0.
        - input: string to pass to stdin.
        - silent: if captureOutput=False, suppress output to parent streams.
        """
        cmd_str = _FormatCommand(args)

        env_dict = os.environ.copy()
        if env:
            env_dict.update(env)

        cwd_path = str(Path(cwd).resolve()) if cwd else None

        stdout_dest = subprocess.PIPE if captureOutput else (subprocess.DEVNULL if silent else None)
        stderr_dest = subprocess.PIPE if captureOutput else (subprocess.DEVNULL if silent else None)
        stdin_dest = subprocess.PIPE if input is not None else None

        preexec_fn = None
        if sys.platform != "win32" and not shell:
            preexec_fn = os.setsid

        try:
            proc = subprocess.Popen(
                args if isinstance(args, list) else args,
                cwd=cwd_path,
                env=env_dict,
                stdout=stdout_dest,
                stderr=stderr_dest,
                stdin=stdin_dest,
                shell=shell,
                preexec_fn=preexec_fn,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Command not found: {cmd_str}") from e

        timer = None
        if timeout is not None:
            timer = Timer(timeout, _KillProcess, [proc])
            timer.daemon = True
            timer.start()

        try:
            stdout_data, stderr_data = proc.communicate(input=input, timeout=timeout)
        except subprocess.TimeoutExpired:
            _KillProcess(proc)
            proc.wait()
            raise TimeoutError(f"Command timed out after {timeout}s: {cmd_str}")
        finally:
            if timer is not None:
                timer.cancel()

        result = ProcessResult(proc.returncode, stdout_data or "", stderr_data or "", cmd_str)

        if check and result.failed:
            raise subprocess.CalledProcessError(
                result.returnCode,
                cmd_str,
                output=result.stdout,
                stderr=result.stderr
            )

        return result

    @staticmethod
    def Run(args: Union[str, List[str]], **kwargs) -> int:
        """
        Simple run, return return code. Outputs to parent streams.
        Equivalent to ExecuteCommand(..., captureOutput=False, silent=False).returnCode.
        """
        result = Process.ExecuteCommand(args, captureOutput=False, silent=False, **kwargs)
        return result.returnCode

    @staticmethod
    def Capture(args: Union[str, List[str]], **kwargs) -> str:
        """
        Run command and capture stdout as string.
        Raises exception on non-zero return.
        """
        result = Process.ExecuteCommand(args, captureOutput=True, check=True, **kwargs)
        return result.stdout

    @staticmethod
    def CaptureLines(args: Union[str, List[str]], **kwargs) -> List[str]:
        """Run command, capture stdout, split into lines."""
        output = Process.Capture(args, **kwargs)
        return [line.rstrip("\n\r") for line in output.splitlines()]

    @staticmethod
    def RunBackground(
        args: Union[str, List[str]],
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
        shell: bool = False,
    ) -> subprocess.Popen:
        """Start a process in background, return Popen object."""
        env_dict = os.environ.copy()
        if env:
            env_dict.update(env)
        cwd_path = str(Path(cwd).resolve()) if cwd else None

        return subprocess.Popen(
            args if isinstance(args, list) else args,
            cwd=cwd_path,
            env=env_dict,
            shell=shell,
            stdout=None,
            stderr=None,
            stdin=subprocess.DEVNULL,
            preexec_fn=os.setsid if sys.platform != "win32" else None,
        )

    @staticmethod
    def Which(executable: str, path: Optional[str] = None) -> Optional[str]:
        """Find executable in PATH (or custom path)."""
        return shutil.which(executable, path=path)

    @staticmethod
    def SetEnvironmentVariable(key: str, value: str) -> None:
        """Set environment variable in current process."""
        os.environ[key] = value

    @staticmethod
    def GetEnvironmentVariable(key: str, default: str = "") -> str:
        """Get environment variable."""
        return os.environ.get(key, default)

    @staticmethod
    def UnsetEnvironmentVariable(key: str) -> None:
        """Remove environment variable."""
        os.environ.pop(key, None)