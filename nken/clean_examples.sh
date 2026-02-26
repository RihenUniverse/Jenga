#!/bin/bash
# clean_examples.sh
# Supprime les dossiers .jenga/ et Build/ dans tous les sous-dossiers de Jenga/Exemples

cd "$(dirname "$0")/Jenga/Exemples" || { echo "Dossier Jenga/Exemples introuvable"; exit 1; }

for d in */ ; do
    if [ -d "$d" ]; then
        echo "Nettoyage de $d"
        rm -rf "${d}.jenga" 2>/dev/null
        rm -rf "${d}Build" 2>/dev/null
    fi
done

echo "Nettoyage terminé."