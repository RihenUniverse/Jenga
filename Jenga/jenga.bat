@echo off
REM Jenga launcher script for Windows

set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%\jenga.py" %*
