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
    DATABASE_URL="postgresql://<user>:<password>@db:5432/planifitai"
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

### Tests locales

En local, los tests ejecutan Celery en modo *eager* con broker y backend en memoria, por lo que no es necesario tener Redis en ejecución.

Para correrlos contra un Redis real exporta `CELERY_TASK_ALWAYS_EAGER=0`, levanta un contenedor Redis y vuelve a lanzar `pytest`.

```bash
CELERY_TASK_ALWAYS_EAGER=0 docker run -d -p 6379:6379 redis
pytest -q
```

Los tests ubicados en `tests/ai_jobs` se saltan automáticamente cuando Celery está en modo *eager*, ya que dependen de un broker real.

## Formateo automático

Instala y configura los hooks locales:

```bash
pip install pre-commit && pre-commit install
```

Para ejecutar todos los chequeos manualmente:

```bash
pre-commit run --all-files
```

En GitHub, un workflow aplica Black y Ruff y crea PRs automáticos si detecta cambios de estilo.
Si no aparece un PR, es porque no había diferencias de formato que aplicar.

## Arquitectura IA

El monolito puede delegar las operaciones de IA a un microservicio FastAPI
ubicado en `services/ai`. Para activarlo expón en el entorno:

```
AI_SERVICE_URL=http://ai:8080
AI_INTERNAL_SECRET=<shared-secret>
```

Si se elimina `AI_SERVICE_URL` el sistema vuelve automáticamente al modo local.

## Feature flags

Las rutas de IA están deshabilitadas por defecto.

- `AI_FEATURES_ENABLED=false` (por defecto): oculta `/api/v1/ai/*`
- `AI_FEATURES_ENABLED=true`: expone `/api/v1/ai/*`

Ejemplo:

```bash
export AI_FEATURES_ENABLED=true
uvicorn app.main:app --reload
```

En CI mantenerlo en `false`.
## API Documentation

The API documentation is available at:

* **Swagger UI:** `/api/v1/docs`
* **ReDoc:** `/api/v1/redoc`

### Endpoints públicos del MVP

| Método | Path | Descripción | Estado |
| --- | --- | --- | --- |
| POST | `/api/v1/auth/login` | Obtener tokens de acceso | ✅ |
| POST | `/api/v1/profiles` | Crear o actualizar el perfil del usuario | ✅ |
| GET | `/api/v1/routines/{id}` | Detalle de rutina y adherencia semanal | ✅ |
| GET | `/api/v1/routines/exercise-catalog` | Catálogo de ejercicios filtrable | ✅ |
| POST | `/api/v1/routines/{id}/schedule-notifications` | Programar notificaciones de rutina | ✅ |
| POST | `/api/v1/notifications/schedule/routines` | Programar notificaciones (duplicado) | ⚠️ Deprecated |
| POST | `/api/v1/notifications/schedule/weigh-in` | Recordatorios semanales de peso | ✅ |
| POST | `/api/v1/nutrition/meal` | Registrar comida diaria | ✅ |
| POST | `/api/v1/progress` | Registrar métricas de progreso | ✅ |

> Las rutas `/api/v1/ai/*` solo están disponibles si `AI_FEATURES_ENABLED=true`.

### Detalles de endpoints clave

#### Detalle de rutina y adherencia
`GET /api/v1/routines/{id}` devuelve la rutina y la adherencia de la semana solicitada. El parámetro `week` acepta `this`, `last` o `custom` con `start` y `end` en formato `YYYY-MM-DD`. Semana lunes–domingo en `Europe/Madrid`. Ejemplos en Swagger.

#### Programar recordatorio de peso
`POST /api/v1/notifications/schedule/weigh-in` crea recordatorios semanales de peso. Es idempotente por fecha local, de modo que reenviar la misma combinación no duplica eventos. Ejemplos en Swagger.

#### Programar notificaciones de rutina
`POST /api/v1/routines/{id}/schedule-notifications` genera recordatorios para los próximos 7 días. El duplicado `POST /api/v1/notifications/schedule/routines` está ⚠️ *deprecated* y responde con cabeceras `Deprecation` y `Link` hacia el endpoint canónico. Ejemplos en Swagger.

#### Catálogo de ejercicios
`GET /api/v1/routines/exercise-catalog` lista ejercicios filtrables por `q`, `muscle`, `equipment` y `level`, pagina con `limit` y `offset` y ordena por `name` ascendente. Ejemplos en Swagger.

## Estándar de respuestas y errores

Todas las respuestas utilizan un sobre homogéneo:

`OK` → `{ "ok": true, "data": { ... } }`

`ERROR` → `{ "ok": false, "error": { "code": "PLAN_NOT_FOUND", "message": "Plan no encontrado" } }`

| Código | HTTP |
| --- | --- |
| AUTH_INVALID_CREDENTIALS | 401 |
| AUTH_FORBIDDEN | 403 |
| PLAN_NOT_FOUND | 404 |
| PLAN_INVALID_STATE | 400 |
| NUTRI_MEAL_NOT_FOUND | 404 |
| COMMON_VALIDATION | 422 |
| COMMON_INTEGRITY | 409 |
| COMMON_HTTP | 4xx |
| COMMON_UNEXPECTED | 500 |
