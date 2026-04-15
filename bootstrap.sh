#!/usr/bin/env bash
# bootstrap.sh — One-command setup for Salad Loom (Linux + macOS)
#
# Usage (fresh install):
#   curl -sSL https://raw.githubusercontent.com/kleer001/Salad_Loom/main/bootstrap.sh | bash
#
# Usage (re-run from inside repo):
#   bash bootstrap.sh
set -euo pipefail

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC}   $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }
warn() { echo -e "${YELLOW}[!!]${NC}   $1"; }
info() { echo -e "${CYAN}[..]${NC}   $1"; }

echo -e "\n${BOLD}=== Salad Loom Bootstrap ===${NC}\n"
echo -e "${YELLOW}${BOLD}Disk space warning:${NC} This install downloads and unpacks approximately ${BOLD}~1 GB${NC} of data:"
echo -e "  • Python packages (spaCy, gensim, nltk, litellm, textual…)  ~750 MB"
echo -e "  • NLTK language data (tokenizer, tagger, lexicons)           ~110 MB"
echo -e "  • GloVe word vectors (glove-wiki-gigaword-50)                 ~88 MB"
echo -e "Make sure you have at least ${BOLD}1.5 GB${NC} of free disk space before continuing."
echo -e "Press ${BOLD}Ctrl-C${NC} now to cancel, or wait 5 seconds to proceed...\n"
sleep 5

OS="$(uname -s)"
case "$OS" in
    Linux)  os_label="Linux" ;;
    Darwin) os_label="macOS" ;;
    *)      fail "Unsupported OS: $OS"; exit 1 ;;
esac
info "Detected OS: $os_label"

# -------------------------------------------------------
# Step 1: Check prerequisites
# -------------------------------------------------------
echo -e "\n${BOLD}Step 1: Checking prerequisites${NC}"

if command -v git &>/dev/null; then
    ok "git found: $(git --version)"
else
    fail "git is not installed. Please install git first."
    exit 1
fi

PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        py_ver="$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
        if [ -n "$py_ver" ]; then
            major="${py_ver%%.*}"
            minor="${py_ver##*.}"
            if [ "$major" -ge 3 ] && [ "$minor" -ge 8 ]; then
                PYTHON="$cmd"
                break
            fi
        fi
    fi
done

if [ -n "$PYTHON" ]; then
    ok "Python found: $($PYTHON --version)"
else
    fail "Python 3.8+ is required but not found."
    echo "  Install from https://www.python.org/downloads/"
    exit 1
fi

NODE_AVAILABLE=false
if command -v node &>/dev/null; then
    node_major="$(node -v | sed 's/v//' | cut -d. -f1)"
    if [ "$node_major" -ge 18 ]; then
        NODE_AVAILABLE=true
        ok "Node.js $(node -v) found — GUI mode available"
    else
        warn "Node.js $(node -v) found but 18+ recommended — GUI mode may not build"
    fi
else
    warn "Node.js not found — GUI mode will not be available (TUI/REPL/API still work)"
fi

# -------------------------------------------------------
# Step 2: Clone repo (skip if already inside it)
# -------------------------------------------------------
echo -e "\n${BOLD}Step 2: Repository${NC}"

if [ -f "salad_loom" ] && [ -f "requirements.txt" ] && [ -d "src/core" ]; then
    ok "Already inside Salad Loom repo — skipping clone"
else
    info "Cloning Salad_Loom..."
    git clone https://github.com/kleer001/Salad_Loom.git
    cd Salad_Loom
    ok "Cloned into $(pwd)"
fi

REPO_DIR="$(pwd)"

# -------------------------------------------------------
# Step 3: Python environment
# -------------------------------------------------------
echo -e "\n${BOLD}Step 3: Python environment${NC}"

if [ ! -d ".venv" ]; then
    info "Creating virtual environment..."
    "$PYTHON" -m venv .venv
fi
ok "Virtual environment: .venv/"

# shellcheck disable=SC1091
source .venv/bin/activate
PYTHON="python"  # use venv python from here on

info "Installing Python dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install -e . --quiet
ok "Python dependencies installed"

# -------------------------------------------------------
# Step 4: NLP models
# -------------------------------------------------------
echo -e "\n${BOLD}Step 4: NLP models${NC}"

info "Downloading spaCy English model..."
python -m spacy download en_core_web_sm --quiet
ok "spaCy en_core_web_sm installed"

info "Downloading NLTK data..."
python -c "
import nltk, os
pkgs = ['averaged_perceptron_tagger_eng', 'punkt_tab', 'words', 'cmudict']
for p in pkgs:
    nltk.download(p, quiet=True)
print('  NLTK packages: ' + ', '.join(pkgs))
"
ok "NLTK data downloaded"

if [ -f "data/models/glove-wiki-gigaword-50.kv" ]; then
    ok "GloVe word vectors already present — skipping download"
else
    info "Downloading GloVe word vectors (~88 MB, one-time) ..."
    mkdir -p data/models
    python -c "
import gensim.downloader as api, pathlib, shutil
print('  Fetching glove-wiki-gigaword-50 from gensim ...')
wv = api.load('glove-wiki-gigaword-50')
dest = pathlib.Path('data/models/glove-wiki-gigaword-50.kv')
wv.save(str(dest))
print(f'  Saved to {dest}')
"
    ok "GloVe vectors saved to data/models/"
fi

# -------------------------------------------------------
# Step 5: GUI (optional)
# -------------------------------------------------------
echo -e "\n${BOLD}Step 5: Web GUI (optional)${NC}"

if [ "$NODE_AVAILABLE" = true ]; then
    info "Installing GUI dependencies..."
    cd src/GUI
    npm install --silent
    info "Building GUI..."
    npm run build --silent
    cd "$REPO_DIR"
    ok "GUI built — launch with: ./salad_loom -g"
else
    warn "Skipping GUI build (Node.js not available)"
    echo "  Install Node.js 18+ then re-run this script to enable GUI mode"
fi

# -------------------------------------------------------
# Step 6: MCP client configuration
# -------------------------------------------------------
echo -e "\n${BOLD}Step 6: MCP client configuration${NC}"

HAVE_CLAUDE_CODE=false
HAVE_CLAUDE_DESKTOP=false

if command -v claude &>/dev/null; then
    HAVE_CLAUDE_CODE=true
    ok "Claude Code CLI detected"
fi

case "$OS" in
    Linux)  desktop_config="$HOME/.config/Claude/claude_desktop_config.json" ;;
    Darwin) desktop_config="$HOME/Library/Application Support/Claude/claude_desktop_config.json" ;;
esac

if [ -d "$(dirname "$desktop_config")" ] || \
   ( [ "$OS" = "Darwin" ] && [ -d "/Applications/Claude.app" ] ) || \
   ( [ "$OS" = "Linux" ] && { command -v claude-desktop &>/dev/null || [ -d "/snap/claude-desktop" ]; } ); then
    HAVE_CLAUDE_DESKTOP=true
    ok "Claude Desktop detected"
fi

configure_claude_code() {
    info "Configuring Claude Code MCP server..."
    claude mcp remove salad-loom --scope user 2>/dev/null || true
    claude mcp add --transport stdio --scope user salad-loom -- \
        "$REPO_DIR/.venv/bin/python" "$REPO_DIR/mcp_server"
    ok "Claude Code configured (verify with: claude mcp list)"
}

configure_claude_desktop() {
    info "Configuring Claude Desktop MCP server..."
    "$PYTHON" - "$desktop_config" "$REPO_DIR" <<'PYEOF'
import json, sys, os
config_file, repo_dir = sys.argv[1], sys.argv[2]
config = {}
if os.path.exists(config_file):
    with open(config_file) as f:
        config = json.load(f)
config.setdefault("mcpServers", {})["salad-loom"] = {
    "command": os.path.join(repo_dir, ".venv", "bin", "python"),
    "args": [os.path.join(repo_dir, "mcp_server")]
}
os.makedirs(os.path.dirname(config_file), exist_ok=True)
with open(config_file, "w") as f:
    json.dump(config, f, indent=2)
    f.write("\n")
PYEOF
    ok "Claude Desktop configured: $desktop_config"
}

if [ "$HAVE_CLAUDE_CODE" = true ] && [ "$HAVE_CLAUDE_DESKTOP" = true ]; then
    echo -e "\nDetected both ${BOLD}Claude Code${NC} and ${BOLD}Claude Desktop${NC}."
    echo "  1) Claude Code  (CLI)"
    echo "  2) Claude Desktop (GUI)"
    echo "  3) Both"
    if [ -t 0 ]; then
        read -rp "Configure which? [1/2/3]: " choice
    else
        info "Non-interactive mode — configuring both"
        choice=3
    fi
    case "$choice" in
        1) configure_claude_code ;;
        2) configure_claude_desktop ;;
        3) configure_claude_code; configure_claude_desktop ;;
        *) warn "Invalid choice — skipping MCP configuration" ;;
    esac
elif [ "$HAVE_CLAUDE_CODE" = true ]; then
    configure_claude_code
elif [ "$HAVE_CLAUDE_DESKTOP" = true ]; then
    configure_claude_desktop
else
    warn "Neither Claude Code nor Claude Desktop detected — skipping MCP configuration"
    echo ""
    echo "  Install one of:"
    echo "    Claude Code:    https://docs.anthropic.com/en/docs/claude-code"
    echo "    Claude Desktop: https://claude.ai/download"
    echo ""
    echo "  Then re-run this script, or configure manually:"
    echo "    Claude Code:"
    echo "      claude mcp add --transport stdio --scope user salad-loom -- \\"
    echo "        ${REPO_DIR}/.venv/bin/python ${REPO_DIR}/mcp_server"
    echo "    Claude Desktop — add to ${desktop_config}:"
    cat <<JSONEOF
{
  "mcpServers": {
    "salad-loom": {
      "command": "${REPO_DIR}/.venv/bin/python",
      "args": ["${REPO_DIR}/mcp_server"]
    }
  }
}
JSONEOF
fi

# -------------------------------------------------------
# Done
# -------------------------------------------------------
echo -e "\n${BOLD}${GREEN}=== Salad Loom is ready! ===${NC}"
echo -e "  Repo:   ${REPO_DIR}"
echo -e "  Venv:   ${REPO_DIR}/.venv/"
echo -e ""
echo -e "  Launch modes:"
echo -e "    ${CYAN}source ${REPO_DIR}/.venv/bin/activate${NC}"
echo -e "    ${CYAN}./salad_loom -t${NC}   Terminal UI"
echo -e "    ${CYAN}./salad_loom -r${NC}   Python REPL"
echo -e "    ${CYAN}./salad_loom -a${NC}   API server  (http://localhost:8000/api/v1/docs)"
if [ "$NODE_AVAILABLE" = true ]; then
    echo -e "    ${CYAN}./salad_loom -g${NC}   Web GUI     (http://localhost:5173)"
fi
echo -e "    ${CYAN}./salad_loom -b -f examples/recipes/n_plus_7.json${NC}   Batch mode"
echo -e ""
echo -e "  Try a recipe: ${CYAN}./salad_loom -b -f examples/recipes/the_full_salad.json${NC}"
echo ""
