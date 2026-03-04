#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Jenga release script (Linux/macOS)
# Steps:
#  1) Clean old artifacts
#  2) Install/upgrade packaging tools
#  3) Build wheel + sdist
#  4) Validate artifacts with twine
#  5) Reinstall latest wheel locally
#  6) Verify jenga version
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "[ERROR] Python introuvable dans le PATH."
    exit 1
fi

echo "[1/7] Nettoyage des anciens artefacts..."
rm -rf build dist
find . -maxdepth 1 -type d -name "*.egg-info" -exec rm -rf {} +

echo "[2/7] Installation / mise a jour des outils de packaging..."
"$PYTHON_BIN" -m pip install --upgrade pip build twine wheel setuptools

echo "[3/7] Build des distributions (wheel + tar.gz)..."
"$PYTHON_BIN" -m build

echo "[4/7] Verification des artefacts avec twine..."
"$PYTHON_BIN" -m twine check dist/*

echo "[5/7] Detection du wheel genere..."
WHEEL_FILE="$(ls -1t dist/*.whl 2>/dev/null | head -n 1 || true)"
if [[ -z "${WHEEL_FILE}" ]]; then
    echo "[ERROR] Aucun fichier wheel trouve dans dist/."
    exit 1
fi
echo "Wheel: ${WHEEL_FILE}"

echo "[6/7] Reinstallation locale du wheel..."
"$PYTHON_BIN" -m pip install --force-reinstall "$WHEEL_FILE"

echo "[7/7] Verification de la version installee..."
if [[ -f "$SCRIPT_DIR/Jenga/jenga.sh" ]]; then
    bash "$SCRIPT_DIR/Jenga/jenga.sh" --version
else
    jenga --version
fi

echo
echo "Artefacts generes:"
ls -1 dist
echo
echo "Release terminee avec succes."
