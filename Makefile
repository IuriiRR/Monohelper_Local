.PHONY: docker-run install test server worker \
        lint format format-check typecheck coverage security deadcode pyright quality

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
