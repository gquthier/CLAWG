#!/bin/bash
# ============================================================================
# CLAWG Setup Script
# ============================================================================
# Quick setup for developers who cloned the repo manually.
# Uses uv for fast Python provisioning and package management.
#
# Usage:
#   ./setup-clawg.sh
#
# This script:
# 1. Installs uv if not present
# 2. Creates a virtual environment with Python 3.11 via uv
# 3. Installs all dependencies (main package + submodules)
# 4. Creates .env from template (if not exists)
# 5. Symlinks the 'clawg' CLI command into ~/.local/bin
# 6. Runs the setup wizard (optional)
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_VERSION="3.11"

PURPLE='\033[0;35m'
BOLD='\033[1m'

echo ""
echo -e "${PURPLE}${BOLD}"
echo '  ███████╗███╗   ███╗ █████╗ ██████╗ ████████╗'
echo '  ██╔════╝████╗ ████║██╔══██╗██╔══██╗╚══██╔══╝'
echo '  ███████╗██╔████╔██║███████║██████╔╝   ██║   '
echo '  ╚════██║██║╚██╔╝██║██╔══██║██╔══██╗   ██║   '
echo '  ███████║██║ ╚═╝ ██║██║  ██║██║  ██║   ██║   '
echo '  ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   '
echo '   ██████╗██╗      █████╗ ██╗    ██╗ ██████╗ '
echo '  ██╔════╝██║     ██╔══██╗██║    ██║██╔════╝ '
echo '  ██║     ██║     ███████║██║ █╗ ██║██║  ███╗'
echo '  ██║     ██║     ██╔══██║██║███╗██║██║   ██║'
echo '  ╚██████╗███████╗██║  ██║╚███╔███╔╝╚██████╔╝'
echo '   ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝  ╚═════╝ '
echo -e "${NC}"
echo -e "${PURPLE}  Shared Obsidian Second Brain for AI Agents${NC}"
echo ""

# ============================================================================
# Install / locate uv
# ============================================================================

echo -e "${CYAN}→${NC} Checking for uv..."

UV_CMD=""
if command -v uv &> /dev/null; then
    UV_CMD="uv"
elif [ -x "$HOME/.local/bin/uv" ]; then
    UV_CMD="$HOME/.local/bin/uv"
elif [ -x "$HOME/.cargo/bin/uv" ]; then
    UV_CMD="$HOME/.cargo/bin/uv"
fi

if [ -n "$UV_CMD" ]; then
    UV_VERSION=$($UV_CMD --version 2>/dev/null)
    echo -e "${GREEN}✓${NC} uv found ($UV_VERSION)"
else
    echo -e "${CYAN}→${NC} Installing uv..."
    if curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null; then
        if [ -x "$HOME/.local/bin/uv" ]; then
            UV_CMD="$HOME/.local/bin/uv"
        elif [ -x "$HOME/.cargo/bin/uv" ]; then
            UV_CMD="$HOME/.cargo/bin/uv"
        fi
        
        if [ -n "$UV_CMD" ]; then
            UV_VERSION=$($UV_CMD --version 2>/dev/null)
            echo -e "${GREEN}✓${NC} uv installed ($UV_VERSION)"
        else
            echo -e "${RED}✗${NC} uv installed but not found. Add ~/.local/bin to PATH and retry."
            exit 1
        fi
    else
        echo -e "${RED}✗${NC} Failed to install uv. Visit https://docs.astral.sh/uv/"
        exit 1
    fi
fi

# ============================================================================
# Python check (uv can provision it automatically)
# ============================================================================

echo -e "${CYAN}→${NC} Checking Python $PYTHON_VERSION..."

if $UV_CMD python find "$PYTHON_VERSION" &> /dev/null; then
    PYTHON_PATH=$($UV_CMD python find "$PYTHON_VERSION")
    PYTHON_FOUND_VERSION=$($PYTHON_PATH --version 2>/dev/null)
    echo -e "${GREEN}✓${NC} $PYTHON_FOUND_VERSION found"
else
    echo -e "${CYAN}→${NC} Python $PYTHON_VERSION not found, installing via uv..."
    $UV_CMD python install "$PYTHON_VERSION"
    PYTHON_PATH=$($UV_CMD python find "$PYTHON_VERSION")
    PYTHON_FOUND_VERSION=$($PYTHON_PATH --version 2>/dev/null)
    echo -e "${GREEN}✓${NC} $PYTHON_FOUND_VERSION installed"
fi

# ============================================================================
# Virtual environment
# ============================================================================

echo -e "${CYAN}→${NC} Setting up virtual environment..."

if [ -d "venv" ]; then
    echo -e "${CYAN}→${NC} Removing old venv..."
    rm -rf venv
fi

$UV_CMD venv venv --python "$PYTHON_VERSION"
echo -e "${GREEN}✓${NC} venv created (Python $PYTHON_VERSION)"

# Tell uv to install into this venv (no activation needed for uv)
export VIRTUAL_ENV="$SCRIPT_DIR/venv"

# ============================================================================
# Dependencies
# ============================================================================

echo -e "${CYAN}→${NC} Installing dependencies..."

$UV_CMD pip install -e ".[all]" || $UV_CMD pip install -e "."

echo -e "${GREEN}✓${NC} Dependencies installed"

# ============================================================================
# Submodules (terminal backend + RL training)
# ============================================================================

echo -e "${CYAN}→${NC} Installing submodules..."

# mini-swe-agent (terminal tool backend)
if [ -d "mini-swe-agent" ] && [ -f "mini-swe-agent/pyproject.toml" ]; then
    $UV_CMD pip install -e "./mini-swe-agent" && \
        echo -e "${GREEN}✓${NC} mini-swe-agent installed" || \
        echo -e "${YELLOW}⚠${NC} mini-swe-agent install failed (terminal tools may not work)"
else
    echo -e "${YELLOW}⚠${NC} mini-swe-agent not found (run: git submodule update --init --recursive)"
fi

# tinker-atropos (RL training backend)
if [ -d "tinker-atropos" ] && [ -f "tinker-atropos/pyproject.toml" ]; then
    $UV_CMD pip install -e "./tinker-atropos" && \
        echo -e "${GREEN}✓${NC} tinker-atropos installed" || \
        echo -e "${YELLOW}⚠${NC} tinker-atropos install failed (RL tools may not work)"
else
    echo -e "${YELLOW}⚠${NC} tinker-atropos not found (run: git submodule update --init --recursive)"
fi

# ============================================================================
# Optional: ripgrep (for faster file search)
# ============================================================================

echo -e "${CYAN}→${NC} Checking ripgrep (optional, for faster search)..."

if command -v rg &> /dev/null; then
    echo -e "${GREEN}✓${NC} ripgrep found"
else
    echo -e "${YELLOW}⚠${NC} ripgrep not found (file search will use grep fallback)"
    read -p "Install ripgrep for faster search? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        INSTALLED=false
        
        # Check if sudo is available
        if command -v sudo &> /dev/null && sudo -n true 2>/dev/null; then
            if command -v apt &> /dev/null; then
                sudo apt install -y ripgrep && INSTALLED=true
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y ripgrep && INSTALLED=true
            fi
        fi
        
        # Try brew (no sudo needed)
        if [ "$INSTALLED" = false ] && command -v brew &> /dev/null; then
            brew install ripgrep && INSTALLED=true
        fi
        
        # Try cargo (no sudo needed)
        if [ "$INSTALLED" = false ] && command -v cargo &> /dev/null; then
            echo -e "${CYAN}→${NC} Trying cargo install (no sudo required)..."
            cargo install ripgrep && INSTALLED=true
        fi
        
        if [ "$INSTALLED" = true ]; then
            echo -e "${GREEN}✓${NC} ripgrep installed"
        else
            echo -e "${YELLOW}⚠${NC} Auto-install failed. Install options:"
            echo "    sudo apt install ripgrep     # Debian/Ubuntu"
            echo "    brew install ripgrep         # macOS"
            echo "    cargo install ripgrep        # With Rust (no sudo)"
            echo "    https://github.com/BurntSushi/ripgrep#installation"
        fi
    fi
fi

# ============================================================================
# Environment file
# ============================================================================

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓${NC} Created .env from template"
    fi
else
    echo -e "${GREEN}✓${NC} .env exists"
fi

# ============================================================================
# PATH setup — symlink clawg into ~/.local/bin
# ============================================================================

echo -e "${CYAN}→${NC} Setting up clawg command..."

CLAWG_BIN="$SCRIPT_DIR/venv/bin/clawg"
mkdir -p "$HOME/.local/bin"
ln -sf "$CLAWG_BIN" "$HOME/.local/bin/clawg"
echo -e "${GREEN}✓${NC} Symlinked clawg → ~/.local/bin/clawg"

# Determine the appropriate shell config file
SHELL_CONFIG=""
if [[ "$SHELL" == *"zsh"* ]]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [[ "$SHELL" == *"bash"* ]]; then
    SHELL_CONFIG="$HOME/.bashrc"
    [ ! -f "$SHELL_CONFIG" ] && SHELL_CONFIG="$HOME/.bash_profile"
else
    # Fallback to checking existing files
    if [ -f "$HOME/.zshrc" ]; then
        SHELL_CONFIG="$HOME/.zshrc"
    elif [ -f "$HOME/.bashrc" ]; then
        SHELL_CONFIG="$HOME/.bashrc"
    elif [ -f "$HOME/.bash_profile" ]; then
        SHELL_CONFIG="$HOME/.bash_profile"
    fi
fi

if [ -n "$SHELL_CONFIG" ]; then
    # Touch the file just in case it doesn't exist yet but was selected
    touch "$SHELL_CONFIG" 2>/dev/null || true
    
    if ! echo "$PATH" | tr ':' '\n' | grep -q "^$HOME/.local/bin$"; then
        if ! grep -q '\.local/bin' "$SHELL_CONFIG" 2>/dev/null; then
            echo "" >> "$SHELL_CONFIG"
            echo "# CLAWG — ensure ~/.local/bin is on PATH" >> "$SHELL_CONFIG"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_CONFIG"
            echo -e "${GREEN}✓${NC} Added ~/.local/bin to PATH in $SHELL_CONFIG"
        else
            echo -e "${GREEN}✓${NC} ~/.local/bin already in $SHELL_CONFIG"
        fi
    else
        echo -e "${GREEN}✓${NC} ~/.local/bin already on PATH"
    fi
fi

# ============================================================================
# Seed bundled skills into ~/.clawg/skills/
# ============================================================================

CLAWG_SKILLS_DIR="${CLAWG_HOME:-$HOME/.clawg}/skills"
mkdir -p "$CLAWG_SKILLS_DIR"

echo ""
echo "Syncing bundled skills to ~/.clawg/skills/ ..."
if "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/tools/skills_sync.py" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Skills synced"
else
    # Fallback: copy if sync script fails (missing deps, etc.)
    if [ -d "$SCRIPT_DIR/skills" ]; then
        cp -rn "$SCRIPT_DIR/skills/"* "$CLAWG_SKILLS_DIR/" 2>/dev/null || true
        echo -e "${GREEN}✓${NC} Skills copied"
    fi
fi

# ============================================================================
# Obsidian & Second Brain setup
# ============================================================================

BOLD='\033[1m'
DIM='\033[2m'

echo ""
echo -e "${BOLD}Obsidian Second Brain Setup${NC}"
echo ""
echo -e "  CLAWG uses an ${BOLD}Obsidian vault${NC} as its shared memory."
echo -e "  All your agents read from the same source of truth."
echo ""

# ── Detect Obsidian ──
OBSIDIAN_INSTALLED=false

if [[ "$OSTYPE" == "darwin"* ]]; then
    [ -d "/Applications/Obsidian.app" ] && OBSIDIAN_INSTALLED=true
elif [[ "$OSTYPE" == "linux"* ]]; then
    command -v obsidian >/dev/null 2>&1 && OBSIDIAN_INSTALLED=true
    [ -f "/usr/bin/obsidian" ] && OBSIDIAN_INSTALLED=true
    command -v flatpak >/dev/null 2>&1 && flatpak list 2>/dev/null | grep -qi obsidian && OBSIDIAN_INSTALLED=true
fi

if [ "$OBSIDIAN_INSTALLED" = true ]; then
    echo -e "  ${GREEN}✓${NC} Obsidian detected"
else
    echo -e "  ${YELLOW}⚠${NC} Obsidian not detected"
    echo ""
    echo -e "  Obsidian is ${BOLD}free${NC} — download at: ${CYAN}https://obsidian.md/download${NC}"

    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "  Quick install: ${CYAN}brew install --cask obsidian${NC}"
        echo ""
        read -p "  Install Obsidian via Homebrew? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if command -v brew >/dev/null 2>&1; then
                brew install --cask obsidian && OBSIDIAN_INSTALLED=true && echo -e "  ${GREEN}✓${NC} Obsidian installed"
            else
                echo -e "  ${YELLOW}⚠${NC} Homebrew not found"
            fi
        fi
    elif [[ "$OSTYPE" == "linux"* ]]; then
        echo -e "  Install: ${CYAN}flatpak install flathub md.obsidian.Obsidian${NC}"
        echo -e "       or: ${CYAN}snap install obsidian --classic${NC}"
    fi
    echo ""
    echo -e "  ${DIM}Obsidian is optional for CLI mode. Install anytime.${NC}"
    echo ""
fi

# ── Find or create vault ──
VAULT_PATH=""

# Check common locations
for candidate in \
    "$HOME/.clawg/second-brain" \
    "$HOME/Second Brain" \
    "$HOME/Documents/Second Brain" \
    "$HOME/Obsidian" \
    "$HOME/Documents/Obsidian"; do
    if [ -d "$candidate" ]; then
        VAULT_PATH="$candidate"
        break
    fi
done

if [ -n "$VAULT_PATH" ]; then
    echo -e "  Found vault: ${CYAN}$VAULT_PATH${NC}"
    read -p "  Use this as your Second Brain? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        VAULT_PATH=""
    fi
fi

if [ -z "$VAULT_PATH" ]; then
    echo ""
    DEFAULT_VAULT="$HOME/.clawg/second-brain"
    echo -e "  Enter the path to your Obsidian vault (or press Enter for ${CYAN}$DEFAULT_VAULT${NC}):"
    read -p "  Vault path: " USER_VAULT_PATH
    VAULT_PATH="${USER_VAULT_PATH:-$DEFAULT_VAULT}"
    VAULT_PATH="${VAULT_PATH/#\~/$HOME}"
fi

if [ ! -d "$VAULT_PATH" ]; then
    mkdir -p "$VAULT_PATH"
    echo -e "  ${GREEN}✓${NC} Created vault directory"
fi

# ── Agent identity ──
read -p "  Name your first agent (default: founder): " AGENT_ID
AGENT_ID="${AGENT_ID:-founder}"

# ── Bootstrap Second Brain ──
echo -e "  ${CYAN}→${NC} Initializing Second Brain templates..."

export CLAWG_SECOND_BRAIN_ROOT="$VAULT_PATH"

"$SCRIPT_DIR/venv/bin/python" -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from clawg_cli.paths import bootstrap_second_brain
from pathlib import Path
result = bootstrap_second_brain(Path('''$VAULT_PATH'''), '$AGENT_ID')
print(f'  Created {len(result[\"dirs\"])} dirs, {len(result[\"files\"])} files')
" 2>/dev/null || echo -e "  ${YELLOW}⚠${NC} Bootstrap failed — run 'clawg second-brain init' later"

# ── Copy dashboard ──
DASHBOARD_SRC="$SCRIPT_DIR/dashboard/command-center.html"
if [ -f "$DASHBOARD_SRC" ]; then
    mkdir -p "$VAULT_PATH/dashboard"
    cp "$DASHBOARD_SRC" "$VAULT_PATH/dashboard/command-center.html"
    echo -e "  ${GREEN}✓${NC} Dashboard installed in vault"
fi

# ── Persist config ──
CLAWG_CONFIG_DIR="${CLAWG_HOME:-$HOME/.clawg}"
mkdir -p "$CLAWG_CONFIG_DIR"

if [ -f "$CLAWG_CONFIG_DIR/config.yaml" ]; then
    if ! grep -q "second_brain:" "$CLAWG_CONFIG_DIR/config.yaml" 2>/dev/null; then
        echo "" >> "$CLAWG_CONFIG_DIR/config.yaml"
        echo "second_brain:" >> "$CLAWG_CONFIG_DIR/config.yaml"
        echo "  root: \"$VAULT_PATH\"" >> "$CLAWG_CONFIG_DIR/config.yaml"
        echo "  agent_default_id: \"$AGENT_ID\"" >> "$CLAWG_CONFIG_DIR/config.yaml"
    fi
else
    cat > "$CLAWG_CONFIG_DIR/config.yaml" << YAML
second_brain:
  root: "$VAULT_PATH"
  agent_default_id: "$AGENT_ID"
YAML
fi

echo -e "  ${GREEN}✓${NC} Second Brain linked: ${CYAN}$VAULT_PATH${NC}"
echo -e "  ${GREEN}✓${NC} Agent profile: agents/$AGENT_ID/"

# ============================================================================
# Done
# ============================================================================

echo ""
echo -e "${GREEN}${BOLD}✓ Setup complete!${NC}"
echo ""
echo -e "  ${BOLD}Your Second Brain:${NC} ${CYAN}$VAULT_PATH${NC}"
echo ""

if [ "$OBSIDIAN_INSTALLED" = true ]; then
    echo -e "  ${BOLD}Open in Obsidian:${NC}"
    echo -e "    Open Obsidian → Open folder as vault → ${CYAN}$VAULT_PATH${NC}"
    echo ""
fi

echo -e "  ${BOLD}Quick start:${NC}"
echo ""
echo -e "    1. Reload shell:     ${CYAN}source $SHELL_CONFIG${NC}"
echo -e "    2. Configure keys:   ${CYAN}clawg setup${NC}"
echo -e "    3. Launch agent:     ${CYAN}clawg --agent-id $AGENT_ID${NC}"
echo -e "    4. Open dashboard:   ${CYAN}clawg dashboard${NC}"
echo ""
echo -e "  ${BOLD}Other commands:${NC}"
echo -e "    ${CYAN}clawg second-brain status${NC}   — Check vault connection"
echo -e "    ${CYAN}clawg gateway install${NC}       — Install messaging service"
echo -e "    ${CYAN}clawg cron list${NC}             — View scheduled jobs"
echo -e "    ${CYAN}clawg doctor${NC}                — Diagnose issues"
echo ""

# Ask if they want to run setup wizard now
read -p "Run the API key setup wizard now? [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    echo ""
    "$SCRIPT_DIR/venv/bin/python" -m clawg_cli.main setup
fi
