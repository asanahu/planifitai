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

*   **Create Profile:** POST `/api/v1/profile` (protected) - Creates a user profile for the authenticated user.
*   **Get Profile:** GET `/api/v1/profile/me` (protected) - Retrieves the authenticated user's profile.
*   **Update Profile:** PATCH `/api/v1/profile` (protected) - Partially updates the authenticated user's profile.
*   **Delete Profile:** DELETE `/api/v1/profile` (protected) - Deletes the authenticated user's profile.

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