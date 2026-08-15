#!/usr/bin/env bash
set -euo pipefail

APP_NAME="WizardingOps"

INSTALL_ROOT="$HOME/.local/share/wizops"
VENV_ROOT="$INSTALL_ROOT/.venv"
LAUNCHER="$HOME/.local/bin/wizops"
RUNTIME_ROOT="$HOME/.wizops"

echo "========================================"
echo "$APP_NAME Uninstaller"
echo "========================================"
echo

echo "This will remove:"
echo
echo "  Application : $INSTALL_ROOT"
echo "  Python env  : $VENV_ROOT"
echo "  Launcher    : $LAUNCHER"
echo
echo "Runtime data will be preserved:"
echo
echo "  Runtime     : $RUNTIME_ROOT"
echo

read -r -p "Continue with uninstall? [y/N] " answer

case "$answer" in
    y|Y|yes|YES)
        ;;
    *)
        echo
        echo "Uninstall cancelled."
        exit 0
        ;;
esac

# ----------------------------------------------------------------------
# Remove application
# ----------------------------------------------------------------------

echo
echo "Removing application..."

if [[ -e "$INSTALL_ROOT" || -L "$INSTALL_ROOT" ]]; then
    rm -rf "$INSTALL_ROOT"
    echo "  Application removed."
else
    echo "  Application not found."
fi

# ----------------------------------------------------------------------
# Verify application removal
# ----------------------------------------------------------------------

if [[ -e "$INSTALL_ROOT" || -L "$INSTALL_ROOT" ]]; then
    echo
    echo "ERROR: application directory still exists:"
    echo "  $INSTALL_ROOT"
    exit 1
fi

echo "  Python environment removed."

# ----------------------------------------------------------------------
# Remove launcher
# ----------------------------------------------------------------------

echo
echo "Removing launcher..."

if [[ -e "$LAUNCHER" || -L "$LAUNCHER" ]]; then
    rm -f "$LAUNCHER"
    echo "  Launcher removed."
else
    echo "  Launcher not found."
fi

# ----------------------------------------------------------------------
# Verify launcher removal
# ----------------------------------------------------------------------

if [[ -e "$LAUNCHER" || -L "$LAUNCHER" ]]; then
    echo
    echo "ERROR: launcher still exists:"
    echo "  $LAUNCHER"
    exit 1
fi

# ----------------------------------------------------------------------
# Runtime data
# ----------------------------------------------------------------------

echo
echo "Runtime data has been preserved."

if [[ -d "$RUNTIME_ROOT" ]]; then
    echo "  $RUNTIME_ROOT"
else
    echo "  No runtime data directory found."
fi

echo
echo "----------------------------------------"
echo "Application and launcher removed."
echo "Runtime data was preserved."
echo "----------------------------------------"
echo

# ----------------------------------------------------------------------
# Optional runtime removal
# ----------------------------------------------------------------------

if [[ -d "$RUNTIME_ROOT" ]]; then
    read -r -p "Remove runtime data as well? [y/N] " remove_runtime

    case "$remove_runtime" in
        y|Y|yes|YES)
            echo
            echo "Removing runtime data..."
            rm -rf "$RUNTIME_ROOT"

            if [[ -d "$RUNTIME_ROOT" ]]; then
                echo
                echo "ERROR: runtime data could not be completely removed."
                exit 1
            fi

            echo "  Runtime data removed."
            ;;
        *)
            echo
            echo "Runtime data preserved."
            ;;
    esac
fi

# ----------------------------------------------------------------------
# Finished
# ----------------------------------------------------------------------

echo
echo "██╗    ██╗██╗███████╗ ██████╗ ██████╗ ███████╗"
echo "██║    ██║██║╚══███╔╝██╔═══██╗██╔══██╗██╔════╝"
echo "██║ █╗ ██║██║  ███╔╝ ██║   ██║██████╔╝███████╗"
echo "██║███╗██║██║ ███╔╝  ██║   ██║██╔═══╝ ╚════██║"
echo "╚███╔███╔╝██║███████╗╚██████╔╝██║     ███████║"
echo " ╚══╝╚══╝ ╚═╝╚══════╝ ╚═════╝ ╚═╝     ╚══════╝"
echo
echo "        Linux Wizardry Operations Console"
echo "────────────────────────────────────────────────────────"
echo
echo "========================================"
echo "$APP_NAME has been uninstalled."
echo "========================================"
echo

if [[ -d "$RUNTIME_ROOT" ]]; then
    echo "Runtime data remains at:"
    echo "  $RUNTIME_ROOT"
    echo
fi

echo "You can reinstall $APP_NAME at any time with:"
echo
echo "    ./install.sh"
echo
