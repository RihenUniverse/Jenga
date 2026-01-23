@echo off
REM Force UTF-8 encoding
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
REM Jenga Build System - Windows Launcher

setlocal

REM Find Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON=python
) else (
    where python3 >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON=python3
    ) else (
        echo Error: Python not found in PATH
        exit /b 1
    )
)

REM Get script directory
set SCRIPT_DIR=%~dp0
set JENGA_DIR=%SCRIPT_DIR%

REM Execute jenga.py
%PYTHON% "%JENGA_DIR%\Jenga\jenga.py" %*

endlocal
exit /b %ERRORLEVEL%