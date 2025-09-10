# Repository Guidelines

## Project Structure & Module Organization
- `app/`: FastAPI domains with `models`, `schemas`, `services`, `routers` (e.g., `app/nutrition/...`).
- `services/`: External adapters and shared service utilities.
- `migrations/`: Alembic scripts; configure DB via `DATABASE_URL`.
- `web/`: Frontend assets (if present).
- `tests/`: Mirrors `app/` and `services/` paths for unit/API tests.

## Build, Test, and Development Commands
- Run API (local): `uvicorn app.main:app --reload` — start FastAPI with auto-reload.
- Docker: `docker-compose up --build` — build and run full stack.
- DB migrate: `alembic upgrade head` (create: `alembic revision -m "message"`).
- Tests: `pytest -q` — run the test suite quietly.
- Lint/format: `make lint` and `make format` — Ruff + Black.

## Coding Style & Naming Conventions
- Python 3.11+, 4-space indentation. Type hints everywhere.
- Formatting: Black; Linting: Ruff. Keep imports tidy.
- Modules follow domain layout: `app/<domain>/{models,schemas,services,routers}.py`.
- SQLAlchemy: plural table names (e.g., `nutrition_meals`), `snake_case` columns.
- Pydantic: PascalCase models; set `model_config = ConfigDict(from_attributes=True)` for ORM reads.
- Routes: semantic, kebab-free paths (e.g., `/nutrition/foods/search`).

## Testing Guidelines
- Framework: `pytest`. Place tests under `tests/` mirroring module paths.
- Name tests `test_<module>.py`. Use fixtures for DB/session setup.
- Prefer fast unit tests for routers/services; add integration tests as needed.
- Ensure schema is current before integration tests: `alembic upgrade head`.

## Commit & Pull Request Guidelines
- Commits: concise, imperative, with scope (e.g., `nutrition: add food cache`). Group related changes only.
- PRs: clear description, linked issues, repro steps, and screenshots/logs when useful.
- Include API examples for new endpoints and migration notes for schema changes.
- Run `make lint` and `make format` before pushing.

## Security & Configuration Tips
- Do not commit secrets. Load from `.env` or environment.
- Required: `DATABASE_URL`, `SECRET_KEY`. For food data: `FOOD_SOURCE`, `FDC_API_KEY`.
- Add timeouts/retries to external calls; fail gracefully with actionable errors.

