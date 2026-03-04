@echo off
:: =============================================================================
::  build_all_examples.bat — Jenga Examples Builder (Windows / Android / Web)
::  Parcourt tous les sous-dossiers de Exemples\ contenant un fichier .jenga,
::  détecte les TargetOS déclarés et build uniquement les plateformes présentes.
::  Note : TargetOS.LINUX est ignoré sur Windows.
:: =============================================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "EXEMPLES_DIR=%SCRIPT_DIR%Jenga\Exemples"

set /a TOTAL=0
set /a PASSED=0
set /a FAILED=0

echo.
echo ================================================================
echo           Jenga -- Build All Examples (Windows)
echo ================================================================
echo.

if not exist "%EXEMPLES_DIR%" (
    echo [ERROR] Dossier Exemples\ introuvable : %EXEMPLES_DIR%
    exit /b 1
)

echo Projets decouverts :
echo.

:: ---------------------------------------------------------------------------
:: Ecrire la liste des fichiers .jenga dans un fichier temporaire
:: (evite les problemes de parsing avec les listes longues et les espaces)
:: On cherche uniquement a maxdepth 2 : Exemples\*\*.jenga
:: ---------------------------------------------------------------------------
set "TMPLIST=%TEMP%\jenga_projects_%RANDOM%.txt"

:: Vider/creer le fichier temporaire
type nul > "%TMPLIST%"

for /d %%D in ("%EXEMPLES_DIR%\*") do (
    for %%F in ("%%D\*.jenga") do (
        if exist "%%F" (
            :: Exclure les fichiers dans un sous-dossier .jenga\
            echo %%~dpF | findstr /i "\\.jenga\\" >nul 2>&1
            if errorlevel 1 (
                echo   * %%~nxF  ^(%%~dpF^)
                echo %%F>> "%TMPLIST%"
            )
        )
    )
)

:: Compter les projets
set /a COUNT=0
for /f "usebackq delims=" %%L in ("%TMPLIST%") do set /a COUNT+=1

if %COUNT% EQU 0 (
    echo [WARNING] Aucun fichier .jenga trouve dans %EXEMPLES_DIR%
    del "%TMPLIST%" 2>nul
    exit /b 0
)

echo.
echo %COUNT% projet(s) trouve(s).
echo.

:: ---------------------------------------------------------------------------
:: Boucle principale : lire le fichier temporaire ligne par ligne
:: ---------------------------------------------------------------------------
for /f "usebackq delims=" %%F in ("%TMPLIST%") do (
    set "JENGA_FILE=%%F"
    set "PROJECT_DIR=%%~dpF"
    :: Enlever le backslash final du dossier
    if "!PROJECT_DIR:~-1!"=="\" set "PROJECT_DIR=!PROJECT_DIR:~0,-1!"
    for %%N in ("!PROJECT_DIR!") do set "PROJECT_NAME=%%~nxN"

    echo +-----------------------------------------------------------------+
    echo ^|  Projet : !PROJECT_NAME!
    echo +-----------------------------------------------------------------+

    :: Detecter les plateformes declarees dans le .jenga
    set "DO_WEB=0"
    set "DO_ANDROID=0"
    set "DO_WINDOWS=0"

    findstr /i "TargetOS\.WEB"     "!JENGA_FILE!" >nul 2>&1 && set "DO_WEB=1"
    findstr /i "TargetOS\.ANDROID" "!JENGA_FILE!" >nul 2>&1 && set "DO_ANDROID=1"
    findstr /i "TargetOS\.WINDOWS" "!JENGA_FILE!" >nul 2>&1 && set "DO_WINDOWS=1"

    if "!DO_WEB!!DO_ANDROID!!DO_WINDOWS!"=="000" (
        echo   [SKIP] Aucun TargetOS compatible Windows detecte dans le .jenga
        echo          ^(TargetOS.LINUX ignore sur Windows^)
        echo.
    ) else (
        set "DETECTED="
        if "!DO_WEB!"=="1"     set "DETECTED=!DETECTED! web"
        if "!DO_ANDROID!"=="1" set "DETECTED=!DETECTED! android"
        if "!DO_WINDOWS!"=="1" set "DETECTED=!DETECTED! windows"
        echo   Plateformes detectees :!DETECTED!
        echo.

        if "!DO_WEB!"=="1" (
            set /a TOTAL+=1
            echo   ^> jenga build --platform web
            pushd "!PROJECT_DIR!"
            jenga build --platform web
            set "EC=!errorlevel!"
            popd
            if "!EC!"=="0" (
                echo   [OK] web
                set /a PASSED+=1
            ) else (
                echo   [FAILED] web
                set /a FAILED+=1
            )
            echo.
        )

        if "!DO_ANDROID!"=="1" (
            set /a TOTAL+=1
            echo   ^> jenga build --platform android
            pushd "!PROJECT_DIR!"
            jenga build --platform android
            set "EC=!errorlevel!"
            popd
            if "!EC!"=="0" (
                echo   [OK] android
                set /a PASSED+=1
            ) else (
                echo   [FAILED] android
                set /a FAILED+=1
            )
            echo.
        )

        if "!DO_WINDOWS!"=="1" (
            set /a TOTAL+=1
            echo   ^> jenga build --platform windows
            pushd "!PROJECT_DIR!"
            jenga build --platform windows
            set "EC=!errorlevel!"
            popd
            if "!EC!"=="0" (
                echo   [OK] windows
                set /a PASSED+=1
            ) else (
                echo   [FAILED] windows
                set /a FAILED+=1
            )
            echo.
        )
    )
)

:: Nettoyage
del "%TMPLIST%" 2>nul

:: ---------------------------------------------------------------------------
:summary
echo.
echo ================================================================
echo                          RESUME
echo ================================================================
echo   Builds lances  : %TOTAL%
echo   Reussis        : %PASSED%
echo   Echoues        : %FAILED%
echo.

if "%FAILED%"=="0" (
    echo   [OK] Tous les builds ont reussi !
    exit /b 0
) else (
    echo   [FAILED] %FAILED% build(s) ont echoue.
    exit /b 1
)

endlocal