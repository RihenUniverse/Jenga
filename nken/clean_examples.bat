@echo off
REM clean_examples.bat
REM Supprime les dossiers .jenga\ et Build\ dans tous les sous-dossiers de Jenga\Exemples

cd /d "%~dp0Jenga\Exemples" || ( echo Dossier Jenga\Exemples introuvable & exit /b 1 )

for /d %%d in (*) do (
    echo Nettoyage de %%d
    if exist "%%d\.jenga" rmdir /s /q "%%d\.jenga"
    if exist "%%d\Build"  rmdir /s /q "%%d\Build"
)

echo Nettoyage terminé.
pause