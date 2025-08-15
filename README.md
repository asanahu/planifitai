# PlanifitAI

PlanifitAI is a FastAPI-based API for managing user profiles, authentication, and fitness planning.

## Setup and Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-repo/PlanifitAI.git
    cd PlanifitAI
    ```

2.  **Environment Variables:**

    Create a `.env` file in the root directory of the project with the following content:

    ```
    DATABASE_URL="postgresql://postgres:postgres@db:5432/planifitai"
    SECRET_KEY="your-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES=60
    REFRESH_TOKEN_EXPIRE_DAYS=7
    ```

    Replace `your-secret-key` with a strong, random string.

3.  **Build and Run Docker Containers:**

    ```bash
    docker-compose build
    docker-compose up -d
    ```

    This will build the Docker images and start the services (web, worker, db, redis) in detached mode.

## Database Migrations

PlanifitAI uses Alembic for database migrations. To apply migrations:

1.  **Generate a new migration (if you made changes to models):**

    ```bash
    docker-compose exec web alembic revision --autogenerate -m "your_migration_message"
    ```

2.  **Apply pending migrations:**

    ```bash
    docker-compose exec web alembic upgrade head
    ```

## Running Tests

Tests are written using Pytest and can be run inside the `web` container:

```bash
docker-compose exec web pytest -q
```

## API Documentation

The API documentation is available at:

*   **Swagger UI:** `/api/v1/docs`
*   **ReDoc:** `/api/v1/redoc`

## Health Check

You can check the health of the API at:

*   `/health`

## Authentication Flow

1.  **Register:** Send a POST request to `/api/v1/auth/register` with `email` and `password`.
2.  **Login:** Send a POST request to `/api/v1/auth/login` with `username` (email) and `password` (form data). This will return an `access_token` and a `refresh_token`.
3.  **Access Protected Endpoints:** Use the `access_token` in the `Authorization` header as a Bearer token. Refresh tokens are rejected on protected routes.
4.  **Refresh Token:** If your `access_token` expires, send a POST request to `/api/v1/auth/refresh` with your `refresh_token` in the request body to get a new pair of tokens.

## User Profile Module

*   **List Profiles:** GET `/api/v1/profiles/` (protected) - Lists profiles owned by the authenticated user.
*   **Create Profile:** POST `/api/v1/profiles/` (protected) - Creates a user profile for the authenticated user.
*   **Get Profile:** GET `/api/v1/profiles/{profile_id}` (protected) - Retrieves the authenticated user's profile by ID.
*   **Update Profile:** PUT `/api/v1/profiles/{profile_id}` (protected) - Updates the authenticated user's profile.
*   **Delete Profile:** DELETE `/api/v1/profiles/{profile_id}` (protected) - Deletes the authenticated user's profile.

## Progress Module (MVP)

Tracks user metrics such as weight, steps, resting heart rate (rhr), and body fat.

**Data Model:** `progress_entries` with `id`, `user_id`, `date`, `metric`, `value`, `unit`, `notes` and a unique constraint on (`user_id`, `date`, `metric`).

**Endpoints:** (all protected with an access token)

* **Create:** `POST /api/v1/progress` – accepts a single entry or `{"items": [...]}` for bulk.
* **List:** `GET /api/v1/progress` – optional `metric`, `start`, `end` filters.
* **Summary:** `GET /api/v1/progress/summary` – requires `metric`, supports `window` (7|30|90) or `start`/`end`.
* **Delete:** `DELETE /api/v1/progress/{entry_id}` – removes an entry.

**Example cURL:**

```bash
# Login first and set ACCESS token
curl -X POST http://localhost:8000/api/v1/progress \
  -H "Authorization: Bearer $ACCESS" -H "Content-Type: application/json" \
  -d '{"date":"2025-08-13","metric":"weight","value":82.4,"unit":"kg"}'
```

## Roadmap

Upcoming modules and their tentative scope:

* **Routines**: workout plan templates (name, days, exercises).
* **Notifications**: scheduled reminders via Celery (message, send_at, user_id).
## Nutrition Module (MVP)

Tracks daily meals, macronutrients, water intake and targets.

**Endpoints:**

* **Create meal:** `POST /api/v1/nutrition/meal`
* **Day log:** `GET /api/v1/nutrition?date=YYYY-MM-DD`
* **Water log:** `POST /api/v1/nutrition/water` and `GET /api/v1/nutrition/water?date=YYYY-MM-DD`
* **Targets:** `GET /api/v1/nutrition/targets?date=YYYY-MM-DD`, `POST /api/v1/nutrition/targets/custom`, `POST /api/v1/nutrition/targets/auto/recompute`
* **Summary:** `GET /api/v1/nutrition/summary?start=YYYY-MM-DD&end=YYYY-MM-DD`
* **Reminders:** `POST /api/v1/nutrition/schedule-reminders`
* **Post daily summary to progress:** `POST /api/v1/nutrition/post-daily-summary?date=YYYY-MM-DD`

Example create meal:

```json
{
  "date": "2025-08-13",
  "meal_type": "lunch",
  "name": "Poke de pollo",
  "items": [
    {"food_name": "Pechuga de pollo", "serving_qty": 150, "serving_unit": "g", "calories_kcal": 247, "protein_g": 46.5, "carbs_g": 0, "fat_g": 5},
    {"food_name": "Arroz cocido", "serving_qty": 180, "serving_unit": "g", "calories_kcal": 234, "protein_g": 4.5, "carbs_g": 50.4, "fat_g": 0.6}
  ]
}
```

## Notifications Module (MVP)

Stores user notification preferences and schedules reminders using Celery.

**Endpoints:**

* `GET /api/v1/notifications/preferences` – get preferences.
* `PUT /api/v1/notifications/preferences` – update timezone, channels and quiet hours.
* `POST /api/v1/notifications/schedule/routines` – schedule workout reminders.
* `POST /api/v1/notifications/schedule/nutrition` – schedule meal and water reminders.
* `GET /api/v1/notifications` – list in-app notifications.

Example scheduling a routine:

```json
{ "routine_id": 123, "active_days": {"mon": true}, "hour_local": "07:30" }
```

## IA

The project includes an optional AI module available under `/api/v1/ai`.
Main endpoints:

* `POST /ai/generate/workout-plan`
* `POST /ai/generate/nutrition-plan`
* `POST /ai/chat`
* `POST /ai/insights`
* `POST /ai/recommend`

All endpoints require authentication and accept `?simulate=true` for
deterministic responses without contacting external services.

## Git hooks y escaneo de secretos

Usamos `pre-commit` con `detect-secrets`, `gitleaks`, `ruff`, `black` y otros.

**Primer uso**
```bash
pip install pre-commit detect-secrets gitleaks
pre-commit install
detect-secrets scan > .secrets.baseline
detect-secrets audit .secrets.baseline
```

## Riesgos de Seguridad Conocidos

- `ecdsa` (GHSA-wj6h-64fc-37mp / CVE-2024-23342) es una dependencia transitiva de `python-jose`. Riesgo bajo; se revisará cuando exista una corrección upstream.
