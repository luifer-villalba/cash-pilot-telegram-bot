.PHONY: install lint fmt test run help build

build:
	docker compose build

install: build
	docker compose run --rm bot pip install -r requirements.txt

lint:
	docker compose run --rm bot bash -c "ruff check src && black --check src && isort --check-only src"

fmt:
	docker compose run --rm bot bash -c "black src && isort src && ruff format src && ruff check --fix src"

test:
	docker compose run --rm bot pytest -v

run:
	docker compose up bot

sh:
	docker compose exec bot bash

help:
	@echo "Available commands:"
	@echo "  make build   - Build Docker image"
	@echo "  make install - Install dependencies"
	@echo "  make lint    - Check code quality"
	@echo "  make fmt     - Auto-format code"
	@echo "  make test    - Run tests"
	@echo "  make run     - Start bot"
	@echo "  make sh      - Open shell in container"
