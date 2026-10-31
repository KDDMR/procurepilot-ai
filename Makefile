.PHONY: install run test lint security demo docker

install:
	python -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -e ".[dev]"

run:
	uvicorn procurepilot.api:app --reload --host 127.0.0.1 --port 8000

test:
	pytest

lint:
	ruff check .
	ruff format --check .
	mypy src/procurepilot

security:
	bandit -c pyproject.toml -r src

demo:
	python scripts/demo.py

docker:
	docker compose up --build

