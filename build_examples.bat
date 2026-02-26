@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================================================
REM build_examples.bat – Lance les builds pour tous les exemples Jenga
REM ============================================================================

:: Vérifier que jenga est accessible
where jenga >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] jenga n'est pas dans le PATH.
    echo Veuillez installer Jenga ou l'ajouter au PATH.
    pause
    exit /b 1
)

:: Déterminer le dossier des exemples
set "SCRIPT_DIR=%~dp0"
set "EXAMPLES_DIR=%SCRIPT_DIR%Jenga\Exemples"

if not exist "%EXAMPLES_DIR%" (
    echo Dossier introuvable : %EXAMPLES_DIR%
    pause
    exit /b 1
)

cd /d "%EXAMPLES_DIR%" || (
    echo Impossible d'accéder à %EXAMPLES_DIR%
    pause
    exit /b 1
)

echo ========================================================
echo   Construction de tous les exemples Jenga
echo ========================================================
echo.

set "TOTAL=0"
set "SUCCESS=0"
set "FAILED=0"

for /d %%d in (*) do (
    set "EXAMPLE=%%d"
    set "EXAMPLE_DIR=%EXAMPLES_DIR%\%%d"
    echo --------------------------------------------------------
    echo Traitement de l'exemple : !EXAMPLE!
    echo --------------------------------------------------------

    cd /d "!EXAMPLE_DIR!" 2>nul || (
        echo [ERREUR] Impossible d'entrer dans !EXAMPLE_DIR!
        set /a FAILED+=1
        goto :continue_loop
    )

    :: Chercher un fichier .jenga (le premier trouvé)
    set "JENGA_FILE="
    for %%f in (*.jenga) do (
        set "JENGA_FILE=%%f"
        goto :found_file
    )
    :found_file
    if "!JENGA_FILE!"=="" (
        echo [AVERTISSEMENT] Aucun fichier .jenga trouvé dans !EXAMPLE!
        set /a FAILED+=1
        goto :continue_loop
    )

    echo Fichier Jenga : !JENGA_FILE!

    :: Créer un script Python temporaire pour extraire les plateformes
    set "TEMP_SCRIPT=%TEMP%\get_platforms_!RANDOM!.py"
    set "TEMP_OUT=%TEMP%\get_platforms_!RANDOM!.out"
    (
        echo import sys
        echo from pathlib import Path
        echo sys.path.insert(0, r'%SCRIPT_DIR%')
        echo try:
        echo     from Jenga.Loader import Loader
        echo except ImportError as e:
        echo     print("Erreur d'import Jenga:", e, file=sys.stderr)
        echo     sys.exit(1)
        echo loader = Loader()
        echo wks = loader.LoadWorkspace(r'!JENGA_FILE!')
        echo if wks is None:
        echo     print("Impossible de charger le workspace", file=sys.stderr)
        echo     sys.exit(1)
        echo platforms = []
        echo if wks.targetOses:
        echo     platforms = [str(p.value) for p in wks.targetOses]
        echo elif wks.platforms:
        echo     platforms = wks.platforms
        echo else:
        echo     platforms = ['Windows', 'Linux', 'macOS', 'Android', 'Web']
        echo print(' '.join(platforms))
    ) > "%TEMP_SCRIPT%"

    :: Exécuter le script, capturer stdout et stderr dans un fichier
    python "%TEMP_SCRIPT%" > "%TEMP_OUT%" 2>&1
    set "PY_ERROR=%errorlevel%"

    :: Lire la sortie (première ligne)
    set "PLATFORMS="
    if exist "%TEMP_OUT%" (
        for /f "usebackq delims=" %%p in ("%TEMP_OUT%") do set "PLATFORMS=%%p"
        del "%TEMP_OUT%" 2>nul
    )
    del "%TEMP_SCRIPT%" 2>nul

    if %PY_ERROR% neq 0 (
        echo [ERREUR] Le script Python a échoué. Message :
        type "%TEMP_OUT%" 2>nul
        set /a FAILED+=1
        goto :continue_loop
    )

    if "!PLATFORMS!"=="" (
        echo [AVERTISSEMENT] Aucune plateforme détectée pour !EXAMPLE!
        set /a FAILED+=1
        goto :continue_loop
    )

    echo Plateformes détectées : !PLATFORMS!

    :: Lancer le build pour chaque plateforme
    for %%p in (!PLATFORMS!) do (
        echo.
        echo --- Build pour %%p ---
        jenga build --platform %%p
        if !errorlevel! equ 0 (
            echo [OK] %%p réussi
            set /a SUCCESS+=1
        ) else (
            echo [ERREUR] %%p échoué
            set /a FAILED+=1
        )
    )

    :continue_loop
    cd /d "%EXAMPLES_DIR%" 2>nul
    set /a TOTAL+=1
)

echo.
echo ========================================================
echo   Résumé
echo ========================================================
echo Total exemples traités : %TOTAL%
echo Builds réussis : %SUCCESS%
echo Builds échoués : %FAILED%
echo.

if %FAILED% neq 0 (
    echo Certains builds ont échoué.
    pause
    exit /b 1
) else (
    echo Tous les builds ont réussi.
    pause
    exit /b 0
)