@echo off
REM Wrapper for Zig C compiler
python "%~dp0zig-wrapper.py" cc %*
exit /b %ERRORLEVEL%
