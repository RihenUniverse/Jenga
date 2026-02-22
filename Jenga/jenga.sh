#!/bin/bash
# Jenga launcher script for Linux/macOS

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/jenga.py" "$@"
