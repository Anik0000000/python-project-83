PORT ?= 8000
DEV_PORT ?= 5000

install:
	uv sync

dev:
	uv run flask --debug --app page_analyzer:app run --port=$(DEV_PORT)

start:
	uv run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

render-start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

build:
	chmod +x build.sh
	./build.sh

lint:
	uv run flake8 page_analyzer

test:
	uv run pytest

.PHONY: install dev start render-start build lint test