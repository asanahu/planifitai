# Repository Guidelines

## Project Structure & Module Organization
- app/: FastAPI application modules (routers, services, models, schemas).
- services/: External service adapters and shared service utilities.
- migrations/: Alembic migration scripts. Configure DB via `DATABASE_URL`.
- web/: Frontend assets (if applicable).
- tests/: API and unit tests.

## Build, Test, and Development Commands
- Run API (local): `uvicorn app.main:app --reload`
- Run with Docker: `docker-compose up --build`
- DB migrations: `alembic upgrade head` (create: `alembic revision -m "message"`)
- Tests: `pytest -q`
- Lint/format: `make lint` and `make format`

## Coding Style & Naming Conventions
- Python 3.11+, Black + Ruff enforced. 4-space indentation.
- Modules follow domain layout: `app/<domain>/{models,schemas,services,routers}.py`.
- SQLAlchemy models: plural table names (e.g., `nutrition_meals`), snake_case columns.
- Pydantic: PascalCase classes, explicit field types, `model_config = ConfigDict(from_attributes=True)` when needed.
- Routes: kebab-free, semantic paths (e.g., `/nutrition/foods/search`).

## Testing Guidelines
- Framework: `pytest`. Place tests under `tests/` mirroring module paths.
- Name tests `test_<module>.py`; use fixtures for DB/session.
- Aim for functional coverage on routers/services; prefer fast unit tests over integration unless required.

## Commit & Pull Request Guidelines
- Commits: concise imperative subject, scoped changes (e.g., `nutrition: add food cache`).
- PRs: clear description, linked issues, reproduction steps, and screenshots/logs where useful.
- Include API examples for new endpoints and migration notes if schema changes.

## Security & Configuration Tips
- Secrets from `.env` or environment only; never commit real keys.
- Required envs: `DATABASE_URL`, `SECRET_KEY`. For food data: `FOOD_SOURCE`, `FDC_API_KEY`.
- Timeouts and retries for external calls; degrade gracefully on failures.
