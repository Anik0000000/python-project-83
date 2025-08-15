#!/usr/bin/env bash
set -e

# Установка uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Установка зависимостей
uv sync