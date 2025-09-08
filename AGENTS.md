# Repository Guidelines

## Project Structure & Module Organization
- `app/`: FastAPI application modules grouped by domain (`app/<domain>/{models,schemas,services,routers}.py`).
- `services/`: External service adapters and shared service utilities.
- `migrations/`: Alembic migration scripts. Configure DB via `DATABASE_URL`.
- `web/`: Frontend assets (if applicable).
- `tests/`: API and unit tests mirroring module paths.

## Build, Test, and Development Commands
- Run API (local): `uvicorn app.main:app --reload` — starts FastAPI with auto-reload.
- Run with Docker: `docker-compose up --build` — builds and runs the stack.
- DB migrations: `alembic upgrade head` (create: `alembic revision -m "message"`).
- Tests: `pytest -q` — runs test suite quietly.
- Lint/format: `make lint` and `make format` — Ruff + Black.
- Env: create `.env` with `DATABASE_URL` and `SECRET_KEY` (plus `FOOD_SOURCE`, `FDC_API_KEY` when needed).

## Coding Style & Naming Conventions
- Python 3.11+, 4-space indentation; format with Black, lint with Ruff.
- Modules follow domain layout; filenames use `snake_case`.
- SQLAlchemy: plural table names (e.g., `nutrition_meals`), `snake_case` columns.
- Pydantic: PascalCase classes; set `model_config = ConfigDict(from_attributes=True)` when reading from ORM.
- Routes: kebab-free, semantic paths (e.g., `/nutrition/foods/search`); use type hints throughout.

## Testing Guidelines
- Framework: `pytest`. Place tests under `tests/` mirroring `app/` structure.
- Name tests `test_<module>.py`; use fixtures for DB/session setup.
- Focus on routers/services with fast unit tests; add integration tests only where required.
- Run locally with `pytest -q`; ensure schema up to date via `alembic upgrade head` before integration tests.

## Commit & Pull Request Guidelines
- Commits: concise, imperative subject with scope (e.g., `nutrition: add food cache`); group only related changes.
- PRs: clear description, linked issues, reproduction steps, and screenshots/logs when useful.
- Include API examples for new endpoints and migration notes for schema changes.
- Keep noise low: run `make lint` and `make format` before pushing.

## Security & Configuration Tips
- Never commit secrets. Load from `.env` or environment.
- Required: `DATABASE_URL`, `SECRET_KEY`. For food data: `FOOD_SOURCE`, `FDC_API_KEY`.
- Add timeouts/retries to external calls; fail gracefully with actionable errors.

