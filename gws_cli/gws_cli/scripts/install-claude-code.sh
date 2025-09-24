#!/bin/bash

echo "Installing Claude Code..."

# Source nvm to ensure node and npm are available
if [ -s "$HOME/.nvm/nvm.sh" ]; then
    \. "$HOME/.nvm/nvm.sh"
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js first using 'gws utils install-node'"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Please install Node.js first using 'gws utils install-node'"
    exit 1
fi

echo "Node.js version: $(node -v)"
echo "npm version: $(npm -v)"

# Install Claude Code globally
echo "Installing @anthropic-ai/claude-code..."
npm i -g @anthropic-ai/claude-code

# Verify installation
if command -v claude-code &> /dev/null; then
    echo "Claude Code installation completed successfully!"
    echo "You can now use 'claude-code' command"
else
    echo "Claude Code installation failed or is not in PATH"
    exit 1
fi