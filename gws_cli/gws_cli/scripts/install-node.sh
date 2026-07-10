#!/bin/bash
set -euo pipefail

# Node.js version installed by `gws utils install-node`.
# Pinned to the 24.x LTS line ("Krypton"). If this exact patch release is not
# available from the Node distribution, we fall back to the latest LTS on the
# 24.x line rather than failing the whole install.
NODE_VERSION="24.18.0"
NODE_MAJOR="24"

echo "Installing Node.js via NVM..."

# Install NVM (Node Version Manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash

# In lieu of restarting the shell, source nvm
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
\. "$NVM_DIR/nvm.sh"

# Download and install Node.js
if ! nvm install "$NODE_VERSION"; then
    echo "Node.js $NODE_VERSION is not available; falling back to the latest $NODE_MAJOR.x LTS."
    nvm install "$NODE_MAJOR"
fi

# Use the version we just installed, and make it the default for new shells
nvm use "$NODE_MAJOR"
nvm alias default "$NODE_MAJOR"

# Verify the Node.js version
echo "Node.js version:"
node -v

# Verify npm version
echo "npm version:"
npm -v

echo "Node.js installation completed successfully!"
