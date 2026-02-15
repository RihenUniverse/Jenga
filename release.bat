@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ============================================================================
REM Jenga release script (Windows)
REM Steps:
REM  1) Clean old artifacts
REM  2) Install/upgrade packaging tools
REM  3) Build wheel + sdist
REM  4) Validate artifacts with twine
REM  5) Reinstall latest wheel locally
REM  6) Verify jenga version
REM ============================================================================

cd /d "%~dp0"

set "PYTHON_CMD=py"
%PYTHON_CMD% -V >nul 2>&1
if errorlevel 1 (
    set "PYTHON_CMD=python"
    %PYTHON_CMD% -V >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python introuvable dans le PATH.
        exit /b 1
    )
)

echo [1/7] Nettoyage des anciens artefacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for /d %%D in (*.egg-info) do (
    rmdir /s /q "%%D"
)

echo [2/7] Installation / mise a jour des outils de packaging...
%PYTHON_CMD% -m pip install --upgrade pip build twine wheel setuptools
if errorlevel 1 exit /b 1

echo [3/7] Build des distributions (wheel + tar.gz)...
%PYTHON_CMD% -m build
if errorlevel 1 exit /b 1

echo [4/7] Verification des artefacts avec twine...
%PYTHON_CMD% -m twine check dist\*
if errorlevel 1 exit /b 1

echo [5/7] Detection du wheel genere...
set "WHEEL_FILE="
for /f "delims=" %%F in ('dir /b /o-d dist\*.whl 2^>nul') do (
    set "WHEEL_FILE=dist\%%F"
    goto :wheel_found
)

:wheel_found
if not defined WHEEL_FILE (
    echo [ERROR] Aucun fichier wheel trouve dans dist\.
    exit /b 1
)
echo Wheel: %WHEEL_FILE%

echo [6/7] Reinstallation locale du wheel...
%PYTHON_CMD% -m pip install --force-reinstall "%WHEEL_FILE%"
if errorlevel 1 exit /b 1

echo [7/7] Verification de la version installee...
if exist "%~dp0jenga.bat" (
    call "%~dp0jenga.bat" --version
) else (
    jenga --version
)

echo.
echo Artefacts generes:
dir /b dist
echo.
echo Release terminee avec succes.

endlocal
exit /b 0
