@echo off
setlocal enabledelayedexpansion

REM nken.bat - Lanceur de scripts situés dans le sous-dossier "nken"

REM Dossier du script (sans antislash final)
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
REM Dossier contenant les scripts cibles
set "TARGET_DIR=%SCRIPT_DIR%\nken"

REM Aide si aucune commande
if "%~1"=="" (
    echo Usage: %~nx0 ^<commande^> [arguments...]
    echo Commandes disponibles dans %TARGET_DIR% :
    if exist "%TARGET_DIR%\" (
        for %%f in ("%TARGET_DIR%\*.bat") do (
            set "fname=%%~nf"
            echo   !fname!
        )
    ) else (
        echo   (dossier nken introuvable)
    )
    exit /b 1
)

set "CMD=%~1"
shift

REM Vérifier que le dossier cible existe
if not exist "%TARGET_DIR%\" (
    echo Erreur : dossier cible '%TARGET_DIR%' introuvable.
    exit /b 1
)

REM Script cible (chercher .bat)
set "TARGET=%TARGET_DIR%\%CMD%.bat"

if not exist "%TARGET%" (
    echo Erreur : script '%CMD%' introuvable dans %TARGET_DIR% (cherché %CMD%.bat)
    exit /b 1
)

REM Exécution
call "%TARGET%" %*