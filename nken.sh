#!/bin/bash
# nken.sh - Lanceur de scripts situés dans le sous-dossier "nken"

# Répertoire du script (là où se trouve nken.sh)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Dossier contenant les scripts cibles
TARGET_DIR="$SCRIPT_DIR/nken"

# Aide si aucune commande
if [ $# -eq 0 ]; then
    echo "Usage: $0 <commande> [arguments...]"
    echo "Commandes disponibles dans $TARGET_DIR :"
    if [ -d "$TARGET_DIR" ]; then
        for f in "$TARGET_DIR"/*.sh; do
            [ -f "$f" ] || continue
            base=$(basename "$f" .sh)
            echo "  $base"
        done
    else
        echo "  (dossier nken introuvable)"
    fi
    exit 1
fi

CMD="$1"
shift

# Vérifier que le dossier cible existe
if [ ! -d "$TARGET_DIR" ]; then
    echo "Erreur : dossier cible '$TARGET_DIR' introuvable."
    exit 1
fi

# Script cible (chercher d'abord .sh, puis .bat ? Ici on cherche .sh car on est dans un script bash)
TARGET="$TARGET_DIR/$CMD.sh"

if [ ! -f "$TARGET" ]; then
    echo "Erreur : script '$CMD' introuvable dans $TARGET_DIR (cherché $CMD.sh)"
    exit 1
fi

# Exécution
exec "$TARGET" "$@"