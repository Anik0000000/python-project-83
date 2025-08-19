#!/usr/bin/env bash

# Download and install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# Install dependencies
make install

echo "Build completed successfully. Database will be initialized on first request."