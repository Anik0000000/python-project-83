#!/usr/bin/env bash

# Download and install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# Install dependencies
make install

# Run database migrations if DATABASE_URL is set
if [ -n "$DATABASE_URL" ]; then
    echo "Running database migrations..."
    # Добавляем флаг -f для принудительного выполнения
    psql -v ON_ERROR_STOP=1 $DATABASE_URL -f database.sql
    if [ $? -eq 0 ]; then
        echo "Database migrations completed successfully"
    else
        echo "Database migrations failed"
        exit 1
    fi
else
    echo "DATABASE_URL not set, skipping migrations"
fi