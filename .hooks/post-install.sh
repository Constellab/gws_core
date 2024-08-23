#!/bin/bash

# Post-installation script executed after module installation

# Install the cli
echo "Installing gws cli"
# use to get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

pip install -e $SCRIPT_DIR/../gws_cli
echo "Cli installed successfully"