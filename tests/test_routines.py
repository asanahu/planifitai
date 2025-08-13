
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db, Base
from app.auth.models import User
from app.routines import schemas
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)

@pytest.fixture(scope="function")
def test_user(test_client: TestClient):
    user_data = {"email": "testuser_routines@example.com", "password": "testpassword"}
    response = test_client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture(scope="function")
def auth_headers(test_client: TestClient, test_user: dict):
    login_data = {
        "username": test_user["email"],
        "password": "testpassword",
    }
    response = test_client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_routine(
    test_client: TestClient, auth_headers: dict
):
    routine_data = {
        "name": "My First Routine",
        "description": "A simple routine for beginners",
        "active_days": {"mon": True, "wed": True, "fri": True},
        "days": [
            {
                "weekday": 0,
                "exercises": [
                    {
                        "exercise_name": "Push-ups",
                        "sets": 3,
                        "reps": 10,
                        "rest_seconds": 60,
                    },
                    {
                        "exercise_name": "Squats",
                        "sets": 3,
                        "reps": 12,
                        "rest_seconds": 60,
                    },
                ],
            }
        ],
    }
    response = test_client.post("/api/v1/routines/", json=routine_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == routine_data["name"]
    assert data["description"] == routine_data["description"]
    assert len(data["days"]) == 1
    assert len(data["days"][0]["exercises"]) == 2


def test_list_routines(test_client: TestClient, auth_headers: dict):
    # Create a couple of routines first
    routine_data_1 = {"name": "Routine 1", "description": "Desc 1"}
    routine_data_2 = {"name": "Routine 2", "description": "Desc 2"}
    test_client.post("/api/v1/routines/", json=routine_data_1, headers=auth_headers)
    test_client.post("/api/v1/routines/", json=routine_data_2, headers=auth_headers)

    response = test_client.get("/api/v1/routines/?skip=0&limit=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_get_routine(test_client: TestClient, auth_headers: dict):
    routine_data = {"name": "Gettable Routine", "description": "Desc"}
    response = test_client.post("/api/v1/routines/", json=routine_data, headers=auth_headers)
    routine_id = response.json()["id"]

    response = test_client.get(f"/api/v1/routines/{routine_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == routine_data["name"]


def test_update_routine(test_client: TestClient, auth_headers: dict):
    routine_data = {"name": "Updatable Routine", "description": "Desc"}
    response = test_client.post("/api/v1/routines/", json=routine_data, headers=auth_headers)
    routine_id = response.json()["id"]

    update_data = {"name": "Updated Name"}
    response = test_client.put(f"/api/v1/routines/{routine_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]


def test_delete_routine(test_client: TestClient, auth_headers: dict):
    routine_data = {"name": "Deletable Routine", "description": "Desc"}
    response = test_client.post("/api/v1/routines/", json=routine_data, headers=auth_headers)
    routine_id = response.json()["id"]

    response = test_client.delete(f"/api/v1/routines/{routine_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify it's soft-deleted
    response = test_client.get(f"/api/v1/routines/{routine_id}", headers=auth_headers)
    assert response.status_code == 404


def test_clone_template(test_client: TestClient, auth_headers: dict):
    # First, create a public template (as an admin or with a special flag, for now we'll just create it)
    template_data = {
        "name": "Public Template",
        "description": "A template for all to use",
        "is_template": True,
        "is_public": True,
    }
    # This would normally be created by an admin, but for the test we'll create it directly
    # In a real scenario, we would need an admin user to create this
    response = test_client.post("/api/v1/routines/", json=template_data, headers=auth_headers)
    template_id = response.json()["id"]

    clone_data = {"template_id": template_id}
    response = test_client.post("/api/v1/routines/clone", json=clone_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == f"{template_data['name']} (Copy)"
    assert not data["is_template"]


def test_unauthorized_access(test_client: TestClient):
    response = test_client.get("/api/v1/routines/")
    assert response.status_code == 401

