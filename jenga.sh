#!/usr/bin/env bash
# Nken Build System - Unix/Linux/MacOS Launcher

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
JENGA_DIR="$SCRIPT_DIR"

# Find Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "Error: Python not found in PATH"
    exit 1
fi

# Execute jenga.py
exec "$PYTHON" "$JENGA_DIR/Jenga/jenga.py" "$@"
