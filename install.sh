#!/usr/bin/env bash
set -euo pipefail

APP_NAME="WizardingOps"
VERSION="0.1.0"

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INSTALL_ROOT="$HOME/.local/share/wizops"
BIN_DIR="$HOME/.local/bin"
LAUNCHER="$BIN_DIR/wizops"

BACKUP_ROOT="$HOME/.local/share/wizops-backups"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$BACKUP_ROOT/$STAMP"

RUNTIME_ROOT="$HOME/.wizops"

echo "Installing $APP_NAME $VERSION..."
echo

# ----------------------------------------------------------------------
# Sanity checks
# ----------------------------------------------------------------------

if [[ ! -d "$SRC/wizops" ]]; then
    echo "ERROR: wizops/ directory not found."
    echo "This installer must be located inside the WizardingOps project root."
    exit 1
fi

if [[ ! -f "$SRC/wizops/cli.py" ]]; then
    echo "ERROR: wizops/cli.py not found."
    exit 1
fi

if [[ ! -d "$SRC/docs" ]]; then
    echo "ERROR: docs/ directory not found."
    exit 1
fi

if [[ ! -f "$SRC/docs/manual.md" ]]; then
    echo "ERROR: docs/manual.md not found."
    exit 1
fi

# ----------------------------------------------------------------------
# Prepare directories
# ----------------------------------------------------------------------

mkdir -p "$BIN_DIR"
mkdir -p "$BACKUP_ROOT"
mkdir -p "$RUNTIME_ROOT"

# ----------------------------------------------------------------------
# Backup existing installation
# ----------------------------------------------------------------------

if [[ -e "$INSTALL_ROOT" || -L "$INSTALL_ROOT" ]]; then
    echo "Backing up previous installation..."
    echo "  $BACKUP"

    mkdir -p "$BACKUP"

    cp -a "$INSTALL_ROOT" "$BACKUP/wizops"
fi

if [[ -e "$LAUNCHER" || -L "$LAUNCHER" ]]; then
    mkdir -p "$BACKUP"

    # Preserve the existing launcher itself rather than following
    # a symlink into another installation.
    if [[ -L "$LAUNCHER" ]]; then
        cp -a "$LAUNCHER" "$BACKUP/wizops-launcher"
    else
        cp -a "$LAUNCHER" "$BACKUP/wizops-launcher"
    fi
fi

# ----------------------------------------------------------------------
# Install application
# ----------------------------------------------------------------------

echo
echo "Installing application..."
echo "  $INSTALL_ROOT"

rm -rf "$INSTALL_ROOT"

mkdir -p "$INSTALL_ROOT"

cp -a "$SRC/wizops" "$INSTALL_ROOT/"
cp -a "$SRC/docs" "$INSTALL_ROOT/"

if [[ -f "$SRC/README.md" ]]; then
    cp -a "$SRC/README.md" "$INSTALL_ROOT/"
fi

# Never ship development artifacts.
find "$INSTALL_ROOT" \
    \( \
        -name '__pycache__' \
        -o -name '*.pyc' \
        -o -name '*.bak' \
        -o -name 'crash.log' \
        -o -name '*.db' \
    \) \
    -print \
    -exec rm -rf {} +

# ----------------------------------------------------------------------
# Install launcher
# ----------------------------------------------------------------------

echo
echo "Installing launcher..."
echo "  $LAUNCHER"

# IMPORTANT:
# Remove an existing symlink/file before writing the launcher.
# Otherwise a previous symlink could cause the redirection below
# to overwrite the old personal toolkit launcher.
rm -f "$LAUNCHER"

cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="$INSTALL_ROOT"

export PYTHONPATH="\$APP_ROOT\${PYTHONPATH:+:\$PYTHONPATH}"

exec python3 -P -m wizops.cli "\$@"
EOF

chmod +x "$LAUNCHER"

# ----------------------------------------------------------------------
# Validate installed Python source
# ----------------------------------------------------------------------

echo
echo "Validating Python source..."

(
    cd "$INSTALL_ROOT"

    find wizops -type f -name '*.py' -print0 |
        xargs -0 python3 -m py_compile
)

# Remove validation artifacts.
find "$INSTALL_ROOT" \
    -type d \
    -name '__pycache__' \
    -prune \
    -exec rm -rf {} +

# ----------------------------------------------------------------------
# Validate installed CLI
# ----------------------------------------------------------------------

echo
echo "Testing installed CLI..."

"$LAUNCHER" --help >/dev/null

echo "  CLI ............ OK"

"$LAUNCHER" init >/dev/null

echo "  Database ....... OK"

# ----------------------------------------------------------------------
# Verify launcher
# ----------------------------------------------------------------------

echo
echo "Checking launcher..."

if [[ ! -f "$LAUNCHER" ]]; then
    echo "ERROR: launcher was not installed correctly."
    exit 1
fi

if [[ -L "$LAUNCHER" ]]; then
    echo "ERROR: launcher is still a symbolic link."
    exit 1
fi

if [[ ! -x "$LAUNCHER" ]]; then
    echo "ERROR: launcher is not executable."
    exit 1
fi

echo "  Launcher ........ OK"

# ----------------------------------------------------------------------
# Verify application
# ----------------------------------------------------------------------

if [[ ! -f "$INSTALL_ROOT/wizops/cli.py" ]]; then
    echo "ERROR: application was not installed correctly."
    exit 1
fi

if [[ ! -f "$INSTALL_ROOT/docs/manual.md" ]]; then
    echo "ERROR: documentation was not installed correctly."
    exit 1
fi

echo "  Application ...... OK"
echo "  Documentation .... OK"

# ----------------------------------------------------------------------
# Check for legacy/personal references
# ----------------------------------------------------------------------

echo
echo "Checking for legacy references..."

if grep -R -n -E \
    'AI/toolkit|~/AI|ai-console|ai console|AI Console' \
    "$INSTALL_ROOT" \
    --exclude-dir='__pycache__' \
    --exclude='*.pyc' \
    >/dev/null 2>&1; then

    echo
    echo "WARNING: legacy/personal references were found in the installed files."
    echo "Review the installation before distributing it."
else
    echo "  Legacy references . NONE"
fi

# ----------------------------------------------------------------------
# Verify runtime location
# ----------------------------------------------------------------------

mkdir -p "$RUNTIME_ROOT"

if [[ ! -d "$RUNTIME_ROOT" ]]; then
    echo "ERROR: runtime directory could not be created."
    exit 1
fi

# ----------------------------------------------------------------------
# PATH check
# ----------------------------------------------------------------------

echo

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "WARNING:"
    echo "  $BIN_DIR is not currently in your PATH."
    echo
    echo "Add this to ~/.bashrc:"
    echo
    echo '    export PATH="$HOME/.local/bin:$PATH"'
    echo
    echo "Then restart your shell."
    echo
fi

# ----------------------------------------------------------------------
# Finished
# ----------------------------------------------------------------------

echo "========================================"
echo "$APP_NAME $VERSION installed successfully."
echo "========================================"
echo
echo "Application : $INSTALL_ROOT"
echo "Runtime     : $RUNTIME_ROOT"
echo "Launcher    : $LAUNCHER"

if [[ -d "$BACKUP" ]]; then
    echo "Backup      : $BACKUP"
fi

echo
echo "Launch with:"
echo
echo "    wizops"
echo
echo "Or:"
echo
echo "    wizops tui"
echo
# ----------------------------------------------------------------------
# Shell command cache note
# ----------------------------------------------------------------------

if [[ "${BASH_VERSION:-}" != "" ]]; then
    echo
    echo "NOTE:"
    echo "  If wizops was previously installed in this shell,"
    echo "  refresh Bash's command cache before launching:"
    echo
    echo "      hash -r"
    echo
fi
