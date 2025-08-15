#!/usr/bin/env bash
set -e

# Применяем миграции
psql $DATABASE_URL -f database.sql

# Запускаем приложение
gunicorn -w 5 -b 0.0.0.0:$PORT page_analyzer:app