.PHONY: docker-run install test server worker

docker-run:
	docker compose up

install:
	uv pip install -e ".[test]"

test:
	.venv/bin/pytest tests/

server:
	PYTHONPATH=src .venv/bin/uvicorn main:app --reload --host 127.0.0.1 --port 8088

worker:
	PYTHONPATH=src .venv/bin/python -m worker
