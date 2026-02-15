@echo off
echo === Nettoyage des fichiers .pyc et __pycache__ ===
del /s /q *.pyc 2>nul
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo === Suppression des dossiers de build et egg-info ===
if exist build rmdir /s /q build
if exist Jenga.egg-info rmdir /s /q Jenga.egg-info
if exist dist rmdir /s /q dist

echo === Désinstallation du package Jenga ===
pip uninstall Jenga -y

echo === Réinstallation en mode développement ===
pip install -e .

echo === Terminé ===
pause