#!/usr/bin/env bash
# =============================================================================
# cri.sh — Jenga Dev + Distribution Build Script (Linux / macOS)
#
# Mode dev (par défaut) :
#   ./cri.sh            → nettoie, réinstalle en mode éditable, build dist/
#
# Avec tests :
#   ./cri.sh --tests    → identique + lance la suite pytest
# =============================================================================

set -e
cd "$(dirname "${BASH_SOURCE[0]}")"

RUN_TESTS=0
for arg in "$@"; do
    case "$arg" in
        --tests|-t) RUN_TESTS=1 ;;
    esac
done

# --- Détection Python ----------------------------------------------------------
if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    echo "[ERREUR] Python introuvable dans le PATH." >&2
    exit 1
fi

echo
echo "============================================================"
echo "  Jenga Build Script — Dev + Distribution"
echo "  Python : $($PY --version)"
echo "============================================================"
echo

# ─────────────────────────────────────────────────────────────────────────────
echo "[1/6] Nettoyage des fichiers .pyc et __pycache__ ..."
find . -name "*.pyc" -delete 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# ─────────────────────────────────────────────────────────────────────────────
echo "[2/6] Suppression des artefacts de build précédents ..."
rm -rf build dist
rm -rf *.egg-info

# ─────────────────────────────────────────────────────────────────────────────
echo "[3/6] Désinstallation du package Jenga ..."
$PY -m pip uninstall Jenga -y 2>/dev/null || true

echo "[3/6] Réinstallation en mode développement (editable) ..."
$PY -m pip install -e . --quiet
echo "[OK] Installation dev terminée."

# ─────────────────────────────────────────────────────────────────────────────
if [ "$RUN_TESTS" = "1" ]; then
    echo
    echo "[4/6] Lancement de la suite de tests pytest ..."
    if $PY -m pytest tests/ -v --tb=short; then
        echo "[OK] Tous les tests sont verts."
    else
        echo
        echo "[AVERTISSEMENT] Des tests ont échoué — le build de distribution continue."
    fi
else
    echo "[4/6] Tests ignorés  (utilisez --tests pour les lancer)"
fi

# ─────────────────────────────────────────────────────────────────────────────
echo
echo "[5/6] Build de la distribution utilisateur (wheel + sdist) ..."
$PY -m pip install --upgrade build --quiet
$PY -m build
echo "[OK] Build terminé."

# ─────────────────────────────────────────────────────────────────────────────
echo
echo "[6/6] Vérification des artefacts ..."
$PY -m pip install --upgrade twine --quiet
$PY -m twine check dist/*

# ─────────────────────────────────────────────────────────────────────────────
echo
echo "============================================================"
echo "  ARTEFACTS GÉNÉRÉS POUR DISTRIBUTION :"
echo "============================================================"
ls -1 dist/
echo
echo "  Pour installer localement le wheel :"
WHEEL=$(ls dist/*.whl 2>/dev/null | sort -r | head -1)
if [ -n "$WHEEL" ]; then
    echo "    pip install $WHEEL --force-reinstall"
fi
echo
echo "  Pour publier sur PyPI :"
echo "    python -m twine upload dist/*"
echo
echo "============================================================"
echo "  TERMINÉ avec succès."
echo "============================================================"
echo
