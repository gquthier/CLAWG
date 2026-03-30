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
DIM='\033[2m'
NC='\033[0m'

REPO_URL="https://github.com/gquthier/CLAWG.git"
INSTALL_DIR="${CLAWG_INSTALL_DIR:-$HOME/.clawg-src}"

# ── Helpers ──

info()  { echo -e "  ${CYAN}→${NC} $1"; }
ok()    { echo -e "  ${GREEN}✓${NC} $1"; }
warn()  { echo -e "  ${YELLOW}⚠${NC} $1"; }
fail()  { echo -e "  ${RED}✗${NC} $1"; }
ask()   { echo -en "  ${PURPLE}?${NC} $1"; }

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
echo -e "${PURPLE}  Autonomous open-source AI agents with a portable brain${NC}"
echo -e "${DIM}  https://github.com/gquthier/CLAWG${NC}"
echo -e "${DIM}  www.gquthier.com${NC}"
echo ""

# ============================================================================
# Step 1 — Preflight checks
# ============================================================================

echo -e "${BOLD}[1/5] Preflight checks${NC}"

command -v git >/dev/null 2>&1 || { fail "git is required. Install it: https://git-scm.com"; exit 1; }
ok "git found"

command -v python3 >/dev/null 2>&1 || { fail "python3 is required. Install it: https://python.org"; exit 1; }

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
  fail "Python 3.10+ required (found $PY_VERSION)"
  exit 1
fi
ok "Python $PY_VERSION"
echo ""

# ============================================================================
# Step 2 — Clone or update CLAWG
# ============================================================================

echo -e "${BOLD}[2/5] Installing CLAWG${NC}"

if [ -d "$INSTALL_DIR/.git" ]; then
  info "Updating existing installation..."
  cd "$INSTALL_DIR"
  git pull --ff-only origin main 2>/dev/null || git pull origin main
  ok "Updated to latest version"
else
  info "Cloning CLAWG..."
  git clone "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
  ok "Cloned to $INSTALL_DIR"
fi

# ── Virtual environment ──
info "Setting up Python environment..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip --quiet 2>/dev/null
python -m pip install -e . --quiet 2>/dev/null
ok "Dependencies installed"

# ── Symlink CLI ──
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

if [ -f "$INSTALL_DIR/.venv/bin/clawg" ]; then
  ln -sf "$INSTALL_DIR/.venv/bin/clawg" "$BIN_DIR/clawg"
elif [ -f "$INSTALL_DIR/clawg_wrapper" ]; then
  ln -sf "$INSTALL_DIR/clawg_wrapper" "$BIN_DIR/clawg"
  chmod +x "$BIN_DIR/clawg"
fi
ok "CLI linked: ~/.local/bin/clawg"

# ── Clean up stale hermes/openclaw binaries that shadow the new install ──
for STALE_BIN in /opt/homebrew/bin/clawg /usr/local/bin/clawg; do
  if [ -f "$STALE_BIN" ] && grep -q "hermes_cli\|hermes_agent\|openclaw" "$STALE_BIN" 2>/dev/null; then
    warn "Found outdated binary at $STALE_BIN (references old hermes/openclaw)"
    if [ -w "$STALE_BIN" ]; then
      rm -f "$STALE_BIN"
      ok "Removed stale $STALE_BIN"
    else
      warn "Cannot remove $STALE_BIN — run: sudo rm $STALE_BIN"
    fi
  fi
done

# ── Ensure PATH ──
SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
  SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
  SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ] && ! grep -q '.local/bin' "$SHELL_RC" 2>/dev/null; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
  ok "Added ~/.local/bin to PATH in $SHELL_RC"
fi
echo ""

# ============================================================================
# Step 3 — Obsidian & Second Brain setup
# ============================================================================

echo -e "${BOLD}[3/5] Obsidian Second Brain Setup${NC}"
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
  command -v snap >/dev/null 2>&1 && snap list 2>/dev/null | grep -qi obsidian && OBSIDIAN_INSTALLED=true
fi

if [ "$OBSIDIAN_INSTALLED" = true ]; then
  ok "Obsidian detected"
else
  warn "Obsidian not detected on this machine"
  echo ""
  echo -e "  Obsidian is ${BOLD}free${NC} and works on macOS, Linux, Windows, iOS, and Android."
  echo -e "  CLAWG uses it as the editor for your Second Brain vault."
  echo ""
  echo -e "  ${CYAN}Download Obsidian:${NC}"
  echo -e "    ${PURPLE}https://obsidian.md/download${NC}"
  echo ""

  if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "  ${DIM}Quick install on macOS:${NC}"
    echo -e "    ${CYAN}brew install --cask obsidian${NC}"
    echo ""
    ask "Install Obsidian now via Homebrew? [y/N] "
    read -r INSTALL_OBS </dev/tty 2>/dev/null || INSTALL_OBS=""
    if [[ "$INSTALL_OBS" =~ ^[Yy]$ ]]; then
      if command -v brew >/dev/null 2>&1; then
        brew install --cask obsidian && OBSIDIAN_INSTALLED=true && ok "Obsidian installed"
      else
        warn "Homebrew not found. Install from: https://obsidian.md/download"
      fi
    fi
  elif [[ "$OSTYPE" == "linux"* ]]; then
    echo -e "  ${DIM}Install options on Linux:${NC}"
    echo -e "    ${CYAN}flatpak install flathub md.obsidian.Obsidian${NC}"
    echo -e "    ${CYAN}snap install obsidian --classic${NC}"
    echo -e "    ${DIM}Or download AppImage from https://obsidian.md/download${NC}"
    echo ""
  fi

  echo ""
  echo -e "  ${DIM}Note: Obsidian is optional for running CLAWG in CLI mode.${NC}"
  echo -e "  ${DIM}You can always install it later and link your vault.${NC}"
  echo ""
fi

# ── Link or create Second Brain vault ──
VAULT_PATH=""

# Check if already configured
EXISTING_VAULT=""
for env_key in CLAWG_SECOND_BRAIN_ROOT SECOND_BRAIN_ROOT; do
  val="${!env_key}"
  if [ -n "$val" ] && [ -d "$val" ]; then
    EXISTING_VAULT="$val"
    break
  fi
done

# Check common locations
if [ -z "$EXISTING_VAULT" ]; then
  for candidate in \
    "$HOME/.clawg/second-brain" \
    "$HOME/Second Brain" \
    "$HOME/Documents/Second Brain" \
    "$HOME/Obsidian" \
    "$HOME/Documents/Obsidian"; do
    if [ -d "$candidate" ]; then
      EXISTING_VAULT="$candidate"
      break
    fi
  done
fi

if [ -n "$EXISTING_VAULT" ]; then
  ok "Found existing vault: $EXISTING_VAULT"
  ask "Use this vault as your Second Brain? [Y/n] "
  read -r USE_EXISTING </dev/tty 2>/dev/null || USE_EXISTING=""
  if [[ "$USE_EXISTING" =~ ^[Nn]$ ]]; then
    EXISTING_VAULT=""
  else
    VAULT_PATH="$EXISTING_VAULT"
  fi
fi

if [ -z "$VAULT_PATH" ]; then
  echo ""
  echo -e "  ${BOLD}Where is your Obsidian vault?${NC}"
  echo ""
  DEFAULT_VAULT="$HOME/.clawg/second-brain"
  echo -e "  Enter the ${BOLD}full path${NC} to an existing vault, or press Enter"
  echo -e "  to create a new one at ${CYAN}$DEFAULT_VAULT${NC}"
  echo ""
  ask "Vault path: "
  read -r USER_VAULT_PATH </dev/tty 2>/dev/null || USER_VAULT_PATH=""

  if [ -z "$USER_VAULT_PATH" ]; then
    VAULT_PATH="$DEFAULT_VAULT"
  else
    # Expand ~ if present
    VAULT_PATH="${USER_VAULT_PATH/#\~/$HOME}"
  fi
fi

# ── Create vault directory if needed ──
if [ ! -d "$VAULT_PATH" ]; then
  info "Creating vault at: $VAULT_PATH"
  mkdir -p "$VAULT_PATH"
  ok "Vault directory created"
fi

# ── Choose agent identity ──
echo ""
ask "Name your first agent (default: founder): "
read -r AGENT_ID </dev/tty 2>/dev/null || AGENT_ID=""
AGENT_ID="${AGENT_ID:-founder}"

# ── Link and bootstrap Second Brain ──
info "Linking vault and initializing templates..."

# Set the env var for the current process
export CLAWG_SECOND_BRAIN_ROOT="$VAULT_PATH"

# Run the Python bootstrap
python3 -c "
import sys
sys.path.insert(0, '$INSTALL_DIR')
from clawg_cli.paths import bootstrap_second_brain
from pathlib import Path
result = bootstrap_second_brain(Path('$VAULT_PATH'), '$AGENT_ID')
print(f'  Created {len(result[\"dirs\"])} directories, {len(result[\"files\"])} files')
" 2>/dev/null || warn "Bootstrap script failed — you can run 'clawg second-brain init' later"

# Persist the vault path in CLAWG config
CLAWG_CONFIG_DIR="${CLAWG_HOME:-$HOME/.clawg}"
mkdir -p "$CLAWG_CONFIG_DIR"

if [ -f "$CLAWG_CONFIG_DIR/config.yaml" ]; then
  # Update existing config
  if grep -q "second_brain:" "$CLAWG_CONFIG_DIR/config.yaml" 2>/dev/null; then
    # Already has second_brain section — update root
    if command -v sed >/dev/null 2>&1; then
      sed -i.bak "s|root:.*|root: \"$VAULT_PATH\"|" "$CLAWG_CONFIG_DIR/config.yaml" 2>/dev/null || true
      rm -f "$CLAWG_CONFIG_DIR/config.yaml.bak"
    fi
  else
    # Add second_brain section
    echo "" >> "$CLAWG_CONFIG_DIR/config.yaml"
    echo "second_brain:" >> "$CLAWG_CONFIG_DIR/config.yaml"
    echo "  root: \"$VAULT_PATH\"" >> "$CLAWG_CONFIG_DIR/config.yaml"
    echo "  agent_default_id: \"$AGENT_ID\"" >> "$CLAWG_CONFIG_DIR/config.yaml"
  fi
else
  # Create minimal config
  cat > "$CLAWG_CONFIG_DIR/config.yaml" << YAML
# CLAWG Configuration
# Generated by install script

second_brain:
  root: "$VAULT_PATH"
  agent_default_id: "$AGENT_ID"
YAML
fi

ok "Second Brain linked: $VAULT_PATH"
ok "Agent profile: agents/$AGENT_ID/"
echo ""

# ============================================================================
# Step 4 — Dashboard setup
# ============================================================================

echo -e "${BOLD}[4/5] Command Center Dashboard${NC}"

DASHBOARD_SRC="$INSTALL_DIR/dashboard/command-center.html"
DASHBOARD_DST="$VAULT_PATH/dashboard/command-center.html"

if [ -f "$DASHBOARD_SRC" ]; then
  mkdir -p "$VAULT_PATH/dashboard"
  cp "$DASHBOARD_SRC" "$DASHBOARD_DST"
  ok "Dashboard installed in vault"
  echo -e "  ${DIM}Open in Obsidian or run: clawg dashboard${NC}"
else
  warn "Dashboard file not found (optional)"
fi
echo ""

# ============================================================================
# Step 5 — Summary
# ============================================================================

echo -e "${BOLD}[5/5] Installation Complete${NC}"
echo ""
echo -e "  ${GREEN}${BOLD}SMART-CLAWG is ready.${NC}"
echo ""
echo -e "  ${BOLD}Your Second Brain:${NC}"
echo -e "    ${CYAN}$VAULT_PATH${NC}"
echo ""
echo -e "  ${BOLD}Vault structure:${NC}"
echo -e "    ${DIM}$VAULT_PATH/${NC}"
echo -e "    ${DIM}├── agents/$AGENT_ID/   ${NC}${PURPLE}← your agent's identity${NC}"
echo -e "    ${DIM}├── skills/            ${NC}${PURPLE}← shared skills${NC}"
echo -e "    ${DIM}├── subagent/          ${NC}${PURPLE}← specialist agents${NC}"
echo -e "    ${DIM}├── learning/          ${NC}${PURPLE}← lessons & postmortems${NC}"
echo -e "    ${DIM}├── Projects/          ${NC}${PURPLE}← project notes${NC}"
echo -e "    ${DIM}├── dashboard/         ${NC}${PURPLE}← Command Center${NC}"
echo -e "    ${DIM}├── user.md            ${NC}${PURPLE}← your profile${NC}"
echo -e "    ${DIM}├── environment.md     ${NC}${PURPLE}← machine context${NC}"
echo -e "    ${DIM}└── philosophy.md      ${NC}${PURPLE}← principles${NC}"
echo ""

if [ "$OBSIDIAN_INSTALLED" = true ]; then
  echo -e "  ${BOLD}Open in Obsidian:${NC}"
  echo -e "    Open Obsidian → Open folder as vault → select ${CYAN}$VAULT_PATH${NC}"
  echo ""
fi

echo -e "  ${BOLD}Quick start:${NC}"
echo -e "    ${PURPLE}clawg setup${NC}                 — Configure API keys"
echo -e "    ${PURPLE}clawg --agent-id $AGENT_ID${NC}  — Launch with your agent"
echo -e "    ${PURPLE}clawg dashboard${NC}             — Open Command Center"
echo ""
echo -e "  ${BOLD}Useful commands:${NC}"
echo -e "    ${PURPLE}clawg second-brain status${NC}   — Check vault connection"
echo -e "    ${PURPLE}clawg cron list${NC}             — View scheduled jobs"
echo -e "    ${PURPLE}clawg skills list${NC}           — Browse available skills"
echo -e "    ${PURPLE}clawg doctor${NC}                — Diagnose issues"
echo ""

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  echo -e "  ${YELLOW}Restart your shell or run:${NC}"
  echo -e "    ${CYAN}source $SHELL_RC${NC}"
  echo ""
fi
