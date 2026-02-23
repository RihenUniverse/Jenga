@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

REM ============================================================================
REM cri.bat — Jenga Dev + Distribution Build Script
REM
REM Mode dev (par défaut) :
REM   cri.bat           → nettoie, réinstalle en mode éditable, build dist/
REM
REM Avec tests :
REM   cri.bat --tests   → identique + lance la suite pytest
REM ============================================================================

set "RUN_TESTS=0"
if /i "%1"=="--tests" set "RUN_TESTS=1"
if /i "%1"=="-t"      set "RUN_TESTS=1"

REM --- Détection Python ---
set "PY=python"
python -V >nul 2>&1 || (
    set "PY=py"
    py -V >nul 2>&1 || (
        echo [ERREUR] Python introuvable dans le PATH.
        exit /b 1
    )
)

echo.
echo ============================================================
echo   Jenga Build Script — Dev + Distribution
echo ============================================================
echo.

REM ─────────────────────────────────────────────────────────────
echo [1/6] Nettoyage des fichiers .pyc et __pycache__ ...
del /s /q *.pyc 2>nul
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

REM ─────────────────────────────────────────────────────────────
echo [2/6] Suppression des artefacts de build precedents ...
if exist build           rmdir /s /q build
if exist dist            rmdir /s /q dist
for /d %%D in (*.egg-info) do rmdir /s /q "%%D"

REM ─────────────────────────────────────────────────────────────
echo [3/6] Desinstallation du package Jenga ...
%PY% -m pip uninstall Jenga -y 2>nul

echo [3/6] Reinstallation en mode developpement (editable) ...
%PY% -m pip install -e . --quiet
if errorlevel 1 (
    echo [ERREUR] pip install -e . a echoue.
    exit /b 1
)

REM ─────────────────────────────────────────────────────────────
if "%RUN_TESTS%"=="1" (
    echo.
    echo [4/6] Lancement de la suite de tests pytest ...
    %PY% -m pytest tests/ -v --tb=short
    if errorlevel 1 (
        echo.
        echo [AVERTISSEMENT] Des tests ont echoue — le build de distribution continue.
    ) else (
        echo [OK] Tous les tests sont verts.
    )
) else (
    echo [4/6] Tests ignores  ^(utilisez --tests pour les lancer^)
)

REM ─────────────────────────────────────────────────────────────
echo.
echo [5/6] Build de la distribution utilisateur ^(wheel + sdist^) ...
%PY% -m pip install --upgrade build --quiet
%PY% -m build
if errorlevel 1 (
    echo [ERREUR] python -m build a echoue.
    exit /b 1
)

REM ─────────────────────────────────────────────────────────────
echo.
echo [6/6] Verification des artefacts ...
%PY% -m pip install --upgrade twine --quiet
%PY% -m twine check dist\*
if errorlevel 1 (
    echo [AVERTISSEMENT] twine check a signale des problemes.
)

REM ─────────────────────────────────────────────────────────────
echo.
echo ============================================================
echo   ARTEFACTS GENERES POUR DISTRIBUTION :
echo ============================================================
dir /b dist
echo.
echo   Pour installer localement le wheel :
for /f "delims=" %%F in ('dir /b /o-d dist\*.whl 2^>nul') do (
    echo     pip install dist\%%F --force-reinstall
    goto :show_done
)
:show_done

echo.
echo   Pour publier sur PyPI :
echo     python -m twine upload dist\*
echo.
echo ============================================================
echo   TERMINÉ avec succes.
echo ============================================================
echo.
endlocal
pause
