#!/usr/bin/env bash

# Download and install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# Install dependencies
uv sync

echo "Build completed successfully"