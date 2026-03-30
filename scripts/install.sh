#!/usr/bin/env bash
# ============================================================================
# SMART-CLAWG Installer
# ============================================================================
# One-line install:
#   curl -fsSL https://raw.githubusercontent.com/gquthier/CLAWG/main/scripts/install.sh | bash
# ============================================================================

set -e

PURPLE='\033[0;35m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

REPO_URL="https://github.com/gquthier/CLAWG.git"
INSTALL_DIR="${CLAWG_INSTALL_DIR:-$HOME/.clawg-src}"

echo ""
echo -e "${PURPLE}${BOLD}"
cat << 'LOGO'
  ███████╗███╗   ███╗ █████╗ ██████╗ ████████╗
  ██╔════╝████╗ ████║██╔══██╗██╔══██╗╚══██╔══╝
  ███████╗██╔████╔██║███████║██████╔╝   ██║   
  ╚════██║██║╚██╔╝██║██╔══██║██╔══██╗   ██║   
  ███████║██║ ╚═╝ ██║██║  ██║██║  ██║   ██║   
  ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   
   ██████╗██╗      █████╗ ██╗    ██╗ ██████╗ 
  ██╔════╝██║     ██╔══██╗██║    ██║██╔════╝ 
  ██║     ██║     ███████║██║ █╗ ██║██║  ███╗
  ██║     ██║     ██╔══██║██║███╗██║██║   ██║
  ╚██████╗███████╗██║  ██║╚███╔███╔╝╚██████╔╝
   ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝  ╚═════╝ 
LOGO
echo -e "${NC}"
echo -e "${PURPLE}  Shared Obsidian Second Brain for AI Agents${NC}"
echo ""

# ── Preflight ──
command -v git >/dev/null 2>&1 || { echo -e "${RED}git is required but not installed.${NC}"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}python3 is required but not installed.${NC}"; exit 1; }

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
  echo -e "${RED}Python 3.10+ required (found $PY_VERSION).${NC}"
  exit 1
fi

echo -e "${CYAN}Python $PY_VERSION detected.${NC}"

# ── Clone or update ──
if [ -d "$INSTALL_DIR/.git" ]; then
  echo -e "${YELLOW}Updating existing installation...${NC}"
  cd "$INSTALL_DIR"
  git pull --ff-only origin main 2>/dev/null || git pull origin main
else
  echo -e "${CYAN}Cloning CLAWG...${NC}"
  git clone "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
fi

# ── Virtual environment ──
echo -e "${CYAN}Setting up Python environment...${NC}"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip --quiet 2>/dev/null
python -m pip install -e . --quiet 2>/dev/null

# ── Symlink CLI ──
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

if [ -f "$INSTALL_DIR/.venv/bin/clawg" ]; then
  ln -sf "$INSTALL_DIR/.venv/bin/clawg" "$BIN_DIR/clawg"
  echo -e "${GREEN}CLI linked: $BIN_DIR/clawg${NC}"
elif [ -f "$INSTALL_DIR/clawg_wrapper" ]; then
  ln -sf "$INSTALL_DIR/clawg_wrapper" "$BIN_DIR/clawg"
  chmod +x "$BIN_DIR/clawg"
  echo -e "${GREEN}CLI linked: $BIN_DIR/clawg${NC}"
fi

# ── Ensure PATH ──
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  SHELL_RC=""
  if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
  elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
  fi

  if [ -n "$SHELL_RC" ] && ! grep -q '.local/bin' "$SHELL_RC" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
    echo -e "${YELLOW}Added ~/.local/bin to PATH in $SHELL_RC${NC}"
  fi
fi

# ── Done ──
echo ""
echo -e "${GREEN}${BOLD}SMART-CLAWG installed successfully.${NC}"
echo ""
echo -e "  ${CYAN}Next steps:${NC}"
echo -e "  1. ${PURPLE}clawg setup${NC}                    — First-time configuration"
echo -e "  2. ${PURPLE}clawg second-brain link --path \"~/My Second Brain\"${NC}"
echo -e "  3. ${PURPLE}clawg second-brain init --agent-id founder${NC}"
echo -e "  4. ${PURPLE}clawg --agent-id founder${NC}        — Launch with context"
echo ""
echo -e "  ${YELLOW}If 'clawg' is not found, restart your shell or run:${NC}"
echo -e "  ${CYAN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
echo ""
