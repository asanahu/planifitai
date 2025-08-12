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
docker-compose exec web pytest
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
3.  **Access Protected Endpoints:** Use the `access_token` in the `Authorization` header as a Bearer token.
4.  **Refresh Token:** If your `access_token` expires, send a POST request to `/api/v1/auth/refresh` with your `refresh_token` in the request body to get a new `access_token` and `refresh_token`.

## User Profile Module

*   **Create Profile:** POST `/api/v1/profile` (protected) - Creates a user profile for the authenticated user.
*   **Get Profile:** GET `/api/v1/profile/me` (protected) - Retrieves the authenticated user's profile.
*   **Update Profile:** PATCH `/api/v1/profile` (protected) - Partially updates the authenticated user's profile.
*   **Delete Profile:** DELETE `/api/v1/profile` (protected) - Deletes the authenticated user's profile.
