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

REM --- Force UTF-8 pour éviter les UnicodeDecodeError sur pip ---
chcp 65001 >nul 2>&1
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

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
echo   Jenga Build Script ^— Dev + Distribution
echo ============================================================
echo.

REM ─────────────────────────────────────────────────────────────
echo [1/6] Nettoyage des fichiers .pyc et __pycache__ ...
del /s /q *.pyc 2>nul
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

REM ─────────────────────────────────────────────────────────────
echo [2/6] Suppression des artefacts de build precedents ...
if exist build     rmdir /s /q build
if exist dist      rmdir /s /q dist
for /d %%D in (*.egg-info) do rmdir /s /q "%%D"

REM ─────────────────────────────────────────────────────────────
echo [3/6] Desinstallation des anciens paquets Jenga ...
%PY% -m pip uninstall Jenga -y 2>nul
%PY% -m pip uninstall jenga -y 2>nul
%PY% -m pip uninstall jenga-build-system -y 2>nul

REM Mise à jour de setuptools et wheel uniquement si absents
echo [3/6] Verification de setuptools et wheel ...
call :pip_ensure setuptools
call :pip_ensure wheel

REM Installation éditable avec --no-build-isolation pour éviter
REM de recréer un env isolé (et de retélécharger setuptools/wheel)
echo [3/6] Reinstallation en mode developpement (editable) ...
%PY% -m pip install -e . --no-build-isolation --quiet
if errorlevel 1 (
    echo [AVERTISSEMENT] L'installation en mode editable a echoue.
    echo                 Vous pourrez installer le wheel apres le build.
) else (
    echo [OK] Installation dev terminee.
)

REM ─────────────────────────────────────────────────────────────
if "%RUN_TESTS%"=="1" (
    echo.
    echo [4/6] Lancement de la suite de tests pytest ...
    call :pip_ensure pytest
    %PY% -m pytest tests/ -v --tb=short
    if errorlevel 1 (
        echo.
        echo [AVERTISSEMENT] Des tests ont echoue ^— le build de distribution continue.
    ) else (
        echo [OK] Tous les tests sont verts.
    )
) else (
    echo [4/6] Tests ignores ^(utilisez --tests pour les lancer^)
)

REM ─────────────────────────────────────────────────────────────
echo.
echo [5/6] Build de la distribution utilisateur ^(wheel + sdist^) ...
call :pip_ensure build

REM Utilise --no-isolation si setuptools est deja dispo localement,
REM ce qui evite tout appel reseau supplementaire.
%PY% -m pip show setuptools >nul 2>&1
if not errorlevel 1 (
    %PY% -m build --no-isolation
) else (
    %PY% -m build
)
if errorlevel 1 (
    echo [ERREUR] python -m build a echoue.
    exit /b 1
)

REM ─────────────────────────────────────────────────────────────
echo.
echo [6/6] Verification des artefacts ...
call :pip_ensure twine
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
echo   TERMINE avec succes.
echo ============================================================
echo.
endlocal
pause
exit /b 0


REM ============================================================
REM  Helper : installe un paquet pip seulement s'il est absent
REM  Usage  : call :pip_ensure <nom_paquet>
REM ============================================================
:pip_ensure
%PY% -m pip show %~1 >nul 2>&1
if errorlevel 1 (
    echo   [pip] %~1 absent ^— installation en cours ...
    %PY% -m pip install %~1 --quiet
    if errorlevel 1 (
        echo   [pip] AVERTISSEMENT : impossible d'installer %~1.
    ) else (
        echo   [pip] %~1 installe avec succes.
    )
) else (
    echo   [pip] %~1 deja present, aucune action reseau.
)
goto :eof