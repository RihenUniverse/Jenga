@echo off
REM Web server launcher for Emscripten builds
REM Usage: webserver.bat [port] [directory]

set PORT=8000
set DIR=.

if not "%1"=="" set PORT=%1
if not "%2"=="" set DIR=%2

echo.
echo ============================================================
echo   Emscripten Web Server
echo ============================================================
echo   Port: %PORT%
echo   Directory: %DIR%
echo ============================================================
echo.

python "%~dp0webserver.py" %PORT% "%DIR%"
