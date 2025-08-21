PORT ?= 8000

install:
	uv sync

dev:
	uv run flask --debug --app page_analyzer:app run

start:
	uv run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

render-start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

build:
	chmod +x build.sh
	./build.sh

lint:
		uv run ruff check

lint-fix:
		uv run ruff check --fix

test:
	uv run pytest

.PHONY: install dev start render-start build lint test