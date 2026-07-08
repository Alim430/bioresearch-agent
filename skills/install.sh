#!/usr/bin/env bash
# BioResearch Agent — Complete Installation Script
# Usage: ./install.sh [options]
#
# This script installs BOTH the framework AND the workflow skills.
# Run it once, get everything.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# Discover all skill dirs (folders directly containing a SKILL.md) — works with any grouping
mapfile -t SKILL_DIRS < <(find "$SCRIPT_DIR" -name SKILL.md -not -path '*/.*' | xargs -n1 dirname | sort)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ──── Detect agent skill directory ────
detect_agent_dir() {
    if [ -n "$1" ]; then
        echo "$1"
        return
    fi

    # Claude Desktop (macOS)
    if [ -d "$HOME/Library/Application Support/Claude/skills" ]; then
        echo "$HOME/Library/Application Support/Claude/skills"
        return
    fi

    # Claude Desktop (Linux)
    if [ -d "$HOME/.config/claude/skills" ]; then
        echo "$HOME/.config/claude/skills"
        return
    fi

    # Cursor / generic
    if [ -d "$HOME/.config/agent/skills" ]; then
        echo "$HOME/.config/agent/skills"
        return
    fi

    # Fallback (local, gitignored)
    echo "./skills-installed"
}

# ──── Check if framework is installed ────
check_framework() {
    if python3 -c "import bioresearch" 2>/dev/null; then
        return 0
    fi
    return 1
}

# ──── Install framework ────
install_framework() {
    echo -e "${BLUE}▶ Installing BioResearch Agent framework...${NC}"
    cd "$PROJECT_ROOT"
    pip install -e . >/dev/null 2>&1
    echo -e "${GREEN}✓ Framework installed${NC}"
}

# ──── Install skills ────
install_skills() {
    local target_dir="$1"
    mkdir -p "$target_dir"

    echo ""
    echo -e "${BLUE}▶ Installing workflow skills...${NC}"
    if [ ${#SKILL_DIRS[@]} -eq 0 ]; then
        echo -e "${YELLOW}  ⚠ No skills found under $SCRIPT_DIR${NC}"
        return
    fi
    for src in "${SKILL_DIRS[@]}"; do
        local skill
        skill="$(basename "$src")"
        dest="$target_dir/$skill"

        if [ -d "$dest" ]; then
            rm -rf "$dest"
        fi

        cp -r "$src" "$dest"
        echo -e "${GREEN}  ✓ $skill${NC}"
    done
}

# ──── Verify installation ────
verify() {
    echo ""
    echo -e "${BLUE}▶ Verifying installation...${NC}"

    if ! python3 -c "import bioresearch" 2>/dev/null; then
        echo -e "${RED}  ✗ Framework not found${NC}"
        return 1
    fi
    echo -e "${GREEN}  ✓ Framework importable${NC}"

    # Try bioresearch doctor; fall back to python -m when entry point is not in PATH
    if command -v bioresearch >/dev/null 2>&1; then
        DOCTOR_CMD="bioresearch doctor"
    else
        DOCTOR_CMD="python3 -m bioresearch.cli doctor"
    fi

    if ! ${DOCTOR_CMD} >/dev/null 2>&1; then
        echo -e "${RED}  ✗ Doctor check failed${NC}"
        return 1
    fi
    echo -e "${GREEN}  ✓ Doctor check passed${NC}"

    return 0
}

# ──── Main ────
main() {
    echo "═══════════════════════════════════════════════════════════════"
    echo "  BioResearch Agent — Complete Installer"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    TARGET_DIR="$(detect_agent_dir "$1")"

    # Step 1: Framework
    if check_framework; then
        echo -e "${GREEN}✓ Framework already installed${NC}"
    else
        echo -e "${YELLOW}! Framework not detected — will install${NC}"
        install_framework
    fi

    # Step 2: Skills
    install_skills "$TARGET_DIR"

    # Step 3: Verify
    if verify; then
        echo ""
        echo "═══════════════════════════════════════════════════════════════"
        echo -e "  ${GREEN}Installation complete!${NC}"
        echo "═══════════════════════════════════════════════════════════════"
        echo ""
        echo "Skills installed to: $TARGET_DIR"
        echo ""
        echo "Available commands:"
        echo "  bioresearch run literature --query \"your topic\""
        echo "  bioresearch run biomarker --disease \"your disease\""
        echo "  bioresearch run causal --exposure BMI --outcome \"Type 2 Diabetes\""
        echo ""
        echo "Or via your AI agent:"
        echo "  'Run a literature review on microglia in Alzheimer's disease'"
    else
        echo ""
        echo -e "${RED}Verification failed. Please check errors above.${NC}"
        exit 1
    fi
}

main "$@"
