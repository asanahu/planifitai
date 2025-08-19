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

## Feature flags (MVP)

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

*   **Swagger UI:** `/api/v1/docs`
*   **ReDoc:** `/api/v1/redoc`

### Endpoints de programación de notificaciones (MVP)

| Estado | Endpoint |
| --- | --- |
| ✅ Canónico | `POST /api/v1/routines/{id}/schedule-notifications` |
| ⚠️ Deprecated | `POST /api/v1/notifications/schedule/routines` |

Las llamadas son idempotentes y, en el duplicado, la respuesta incluye la cabecera `Deprecation: true` con un enlace al sucesor.

## POST /api/v1/training/generate

Genera un plan de entrenamiento a partir de los siguientes campos:

| Campo | Tipo | Notas |
| --- | --- | --- |
| `objective` | string | Objetivo principal (ej. `strength`). |
| `frequency` | int | Días por semana (2-6). |
| `level` | string | `beginner`, `intermediate` o `advanced` (def. `beginner`). |
| `session_minutes` | int | Duración de cada sesión (def. `25`). |
| `restrictions` | array[str] | Lesiones o limitaciones (opcional). |
| `persist` | bool | Guarda el plan y devuelve `routine_id`. |
| `use_ai` | bool | Refinar con IA (def. `false`). |

### Respuesta OK

```json
{
  "ok": true,
  "data": {
    "days": [ { "day": 1, "blocks": [] }, ... ],
    "note": "IA pendiente"
  }
}
```

Si `persist=true` la respuesta incluye:

```json
{"ok": true, "data": {"routine_id": 123, "plan": { ... }}}
```

### Respuesta de Error

```json
{
  "ok": false,
  "error": { "code": "PLAN_INVALID_FREQ", "message": "Frecuencia fuera de rango (usa 2 a 6 días)." }
}
```

> Compatibilidad: `data.note` y `day.exercises` se retirarán en la versión `v0.4`.

## Estándar de Respuestas y Errores

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

Ejemplos:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d 'username=user@example.com&password=string'
# → {"ok": true, "data": {"access_token": "..."}}

curl -X GET http://localhost:8000/api/v1/routines/999 \
  -H "Authorization: Bearer TOKEN"
# → {"ok": false, "error": {"code": "PLAN_NOT_FOUND", "message": "Plan no encontrado"}}
```

La variable de entorno `API_ENVELOPE_COMPAT` permite habilitar un modo de compatibilidad temporal para clientes legacy.

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

## Training Adherence

Weekly adherence to a routine based on planned vs. completed workouts.

* **Endpoint:** `GET /api/v1/routines/{id}/adherence?range=last_week`

**Example cURL (OK):**

```bash
curl -H "Authorization: Bearer $ACCESS" \
  http://localhost:8000/api/v1/routines/1/adherence?range=last_week
```

**Example cURL (Error):**

```bash
curl http://localhost:8000/api/v1/routines/999/adherence
# 404 Routine not found
```

> This metric will also be exposed on `/routines/{id}` in v0.4.

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

- Migrado de `python-jose` a `PyJWT` (algoritmo HS256) para eliminar la dependencia transitiva de `ecdsa` (GHSA-wj6h-64fc-37mp / CVE-2024-23342).
- 

## Estándar de Respuestas y Errores

Formato común de todas las respuestas:

```json
{ "ok": true, "data": { ... } }
{ "ok": false, "error": { "code": "PLAN_NOT_FOUND", "message": "Plan no encontrado" } }
```

### Códigos principales

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

### Ejemplos

```bash
curl -X POST /api/v1/auth/login -d 'username=a@b.com&password=secret'

curl -X GET /api/v1/routines/999
```

### Adherencia de Entrenamiento (detalle de rutina)
**Endpoint:** `GET /api/v1/routines/{id}`  
**Parámetros de consulta:**
- `week`: `this` | `last` | `custom` (por defecto: `this`)
- `start`, `end`: `YYYY-MM-DD` (requeridos si `week=custom`)

**Notas:**
- Semana **Lunes–Domingo** en `Europe/Madrid`.
- El campo `adherence` se calcula para el rango solicitado.

**Ejemplo OK:**
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://<host>/api/v1/routines/123e4567-e89b-12d3-a456-426614174000?week=last"
```
```json
{
  "ok": true,
  "data": {
    "id": 123,
    "name": "Summer Shred",
    "adherence": {
      "routine_id": 123,
      "week_start": "2024-08-05",
      "week_end": "2024-08-11",
      "planned": 3,
      "completed": 2,
      "adherence_pct": 67,
      "status": "fair"
    }
  }
}
```

**Ejemplo Error (`week=custom` sin fechas):**
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://<host>/api/v1/routines/123?week=custom"
```
```json
{
  "ok": false,
  "error": {
    "code": "COMMON_VALIDATION",
    "message": "start and end required for custom week"
  }
}
```

### Programar Recordatorio de Peso (Weigh-In)
**Endpoint:** `POST /api/v1/notifications/schedule/weigh-in`  
**Cuerpo JSON:**
```json
{
  "day_of_week": 6,
  "local_time": "09:00",
  "weeks_ahead": 8
}
```

**Notas:**
- Semana **Lunes–Domingo** en `Europe/Madrid`.
- Programa recordatorios semanales de peso.

**Ejemplo OK:**
```bash
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"day_of_week":6,"local_time":"09:00","weeks_ahead":8}' \
  https://<host>/api/v1/notifications/schedule/weigh-in
```
```json
{
  "ok": true,
  "data": {
    "scheduled_count": 8,
    "first_scheduled_local": "2024-08-19T09:00:00+02:00",
    "timezone": "Europe/Madrid"
  }
}
```

**Ejemplo Error (`day_of_week` fuera de rango):**
```bash
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"day_of_week":7,"local_time":"09:00","weeks_ahead":8}' \
  https://<host>/api/v1/notifications/schedule/weigh-in
```
```json
{
  "ok": false,
  "error": {
    "code": "COMMON_VALIDATION",
    "message": "day_of_week must be between 0 and 6"
  }
}
```
