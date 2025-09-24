#!/bin/bash

echo "Installing Node.js via NVM..."

# Install NVM (Node Version Manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash

# In lieu of restarting the shell, source nvm
\. "$HOME/.nvm/nvm.sh"

# Download and install Node.js (version 20)
nvm install 20

# Use Node.js version 20
nvm use 20

# Verify the Node.js version
echo "Node.js version:"
node -v

# Verify npm version
echo "npm version:"
npm -v

echo "Node.js installation completed successfully!"