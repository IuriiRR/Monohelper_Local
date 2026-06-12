.PHONY: docker-run install test server worker deploy-server \
        lint format format-check typecheck coverage security deadcode pyright quality \
        frontend-install frontend-dev frontend-build frontend-lint frontend-typecheck \
        frontend-test gen-types quality-all

docker-run:
	docker compose up

install:
	uv pip install -e ".[test,dev]"

test:
	.venv/bin/pytest tests/

server:
	PYTHONPATH=src .venv/bin/uvicorn main:app --reload --host 127.0.0.1 --port 8088

worker:
	PYTHONPATH=src .venv/bin/python -m worker

# CI/CD deploy service (pull, rebuild, restart) + dashboard at /app on port 8089.
deploy-server:
	PYTHONPATH=src .venv/bin/uvicorn deploy.app:app --reload --host 127.0.0.1 --port 8089

# --- Code quality ---

lint:
	.venv/bin/ruff check src/ tests/

format:
	.venv/bin/ruff format src/ tests/

format-check:
	.venv/bin/ruff format --check src/ tests/

typecheck:
	PYTHONPATH=src .venv/bin/mypy src/

coverage:
	PYTHONPATH=src .venv/bin/pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

security:
	.venv/bin/bandit -r src/ -c pyproject.toml

deadcode:
	.venv/bin/vulture src/ --min-confidence 80

pyright:
	PYTHONPATH=src .venv/bin/pyright src/

quality: lint format-check typecheck coverage security deadcode
	@echo "All quality gates passed."

# --- Frontend (React SPA, served at /app) ---

frontend-install:
	cd frontend && npm ci

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-lint:
	cd frontend && npm run lint

frontend-typecheck:
	cd frontend && npm run typecheck

frontend-test:
	cd frontend && npm test

# Regenerate frontend/src/api/schema.d.ts from the running server's OpenAPI schema.
# Requires the backend running on :8088 (make server). Run after any router/model change.
gen-types:
	cd frontend && npm run gen-types

quality-all: quality frontend-lint frontend-typecheck frontend-test
	@echo "All backend + frontend gates passed."
