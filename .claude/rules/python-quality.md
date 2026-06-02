# Python Code Quality — Monohelper_Local

## Before committing

Run `make quality` — all gates must pass:
- `make lint` — ruff check (no errors allowed)
- `make format-check` — ruff format (no unformatted files)
- `make typecheck` — mypy (no errors allowed)
- `make coverage` — pytest ≥65% coverage
- `make security` — bandit (no issues)
- `make deadcode` — vulture (no dead code at ≥80% confidence)

## Type annotations

- Add return type and parameter annotations to all new functions
- Use `X | None` not `Optional[X]` (Python 3.10+ syntax)
- Use `dict[str, Any]` not `Dict[str, Any]` (no `typing` imports for builtins)
- SQLModel column access patterns need `# type: ignore[attr-defined]` — expected, not a real bug

## SQLModel patterns

- `session.get(Model, id)` returns `Model | None` — always assert or check before use
- `.where(Model.field == value)` looks like `bool` to mypy but is correct SQLAlchemy — use `# type: ignore[arg-type]` if mypy complains
- Never use `== True` in Python comparisons; SQLAlchemy `.where()` is the exception (ignore E712)

## Ruff ignores in use

- `B008` — FastAPI `Depends()` in argument defaults is idiomatic
- `E712` — SQLAlchemy `.where(Model.active == True)` requires this syntax
- `S101` — assert is allowed in tests
- `S106` — dummy tokens in test fixtures are not hardcoded secrets

## Skills to use

- `ecc:python-review` — after writing Python code
- `ecc:fastapi-review` — when modifying routers or services
- `ecc:security-review` — before committing code touching API keys, HTTP, or auth
