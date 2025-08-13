# Changelog

## [Unreleased]

### Added

-   **Routines Module:**
    -   Added database models for routines, routine days, exercise catalog, and routine exercises.
    -   Added Alembic migration for the new tables.
    -   Added Pydantic schemas for data validation and serialization.
    -   Added business logic in the service layer for managing routines.
    -   Added API endpoints for creating, retrieving, updating, and deleting routines, as well as cloning templates and managing exercises.
    -   Added a comprehensive test suite for the new module.
    -   Updated the `README.md` file to document the new API endpoints.

-   **Nutrition Module:**
    -   Added models, schemas, CRUD services and API endpoints for meals, water logs and nutrition targets.
    -   Added automatic calculation of daily macro targets based on user profile.
    -   Added integration with notifications and progress modules.
