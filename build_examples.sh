#!/usr/bin/env bash
# =============================================================================
#  build_all_examples.sh — Jenga Examples Builder (Linux)
#  Parcourt tous les sous-dossiers de Exemples/ contenant un fichier .jenga,
#  détecte les TargetOS déclarés et build uniquement les plateformes présentes.
# =============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXEMPLES_DIR="$SCRIPT_DIR/Exemples"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

TOTAL=0
PASSED=0
FAILED=0

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}════════════════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}          Jenga — Build All Examples (Linux)${RESET}"
echo -e "${BOLD}════════════════════════════════════════════════════════════════${RESET}"
echo ""

if [ ! -d "$EXEMPLES_DIR" ]; then
    echo -e "${RED}[ERROR] Dossier Exemples/ introuvable : $EXEMPLES_DIR${RESET}"
    exit 1
fi

# ---------------------------------------------------------------------------
# Découverte des projets
# ---------------------------------------------------------------------------
mapfile -t JENGA_FILES < <(find "$EXEMPLES_DIR" -maxdepth 2 -name "*.jenga" ! -path "*/.jenga/*" | sort)

if [ ${#JENGA_FILES[@]} -eq 0 ]; then
    echo -e "${YELLOW}[WARNING] Aucun fichier .jenga trouvé dans $EXEMPLES_DIR${RESET}"
    exit 0
fi

echo -e "${CYAN}Projets découverts :${RESET}"
for f in "${JENGA_FILES[@]}"; do
    echo "  • $(basename "$(dirname "$f")")"
done
echo ""

# ---------------------------------------------------------------------------
# Build de chaque projet selon les TargetOS présents dans le .jenga
# ---------------------------------------------------------------------------
for jenga_file in "${JENGA_FILES[@]}"; do
    project_dir="$(dirname "$jenga_file")"
    project_name="$(basename "$project_dir")"

    echo -e "${BOLD}┌──────────────────────────────────────────────────────────────┐${RESET}"
    echo -e "${BOLD}│  Projet : $project_name${RESET}"
    echo -e "${BOLD}└──────────────────────────────────────────────────────────────┘${RESET}"

    # Détecter les plateformes à builder selon ce qui est déclaré dans le .jenga
    declare -a platforms_to_build=()

    grep -q "TargetOS\.WEB"     "$jenga_file" && platforms_to_build+=("web")
    grep -q "TargetOS\.ANDROID" "$jenga_file" && platforms_to_build+=("android")
    grep -q "TargetOS\.WINDOWS" "$jenga_file" && platforms_to_build+=("windows")
    grep -q "TargetOS\.LINUX"   "$jenga_file" && platforms_to_build+=("linux")

    if [ ${#platforms_to_build[@]} -eq 0 ]; then
        echo -e "  ${YELLOW}[SKIP] Aucun TargetOS reconnu dans le fichier .jenga${RESET}"
        echo ""
        unset platforms_to_build
        continue
    fi

    echo -e "  ${CYAN}Plateformes détectées : ${platforms_to_build[*]}${RESET}"
    echo ""

    for platform in "${platforms_to_build[@]}"; do
        TOTAL=$((TOTAL + 1))
        echo -e "  ${CYAN}▶ jenga build --platform $platform${RESET}"

        if (cd "$project_dir" && jenga build --platform "$platform"); then
            echo -e "  ${GREEN}✓ $platform — OK${RESET}"
            PASSED=$((PASSED + 1))
        else
            echo -e "  ${RED}✗ $platform — FAILED${RESET}"
            FAILED=$((FAILED + 1))
        fi
        echo ""
    done

    unset platforms_to_build
done

# ---------------------------------------------------------------------------
# Résumé
# ---------------------------------------------------------------------------
echo -e "${BOLD}════════════════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}                        RÉSUMÉ${RESET}"
echo -e "${BOLD}════════════════════════════════════════════════════════════════${RESET}"
echo -e "  Builds lancés  : $TOTAL"
echo -e "  ${GREEN}Réussis         : $PASSED${RESET}"
echo -e "  ${RED}Échoués         : $FAILED${RESET}"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}${BOLD}  ✓ Tous les builds ont réussi !${RESET}"
    exit 0
else
    echo -e "${RED}${BOLD}  ✗ $FAILED build(s) ont échoué.${RESET}"
    exit 1
fi