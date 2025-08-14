from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date

from app.main import app
from app.auth.deps import get_current_user, UserContext
from app.auth.models import User
from app.nutrition.models import NutritionMeal
from app.progress.models import ProgressEntry
from app.routines.models import Routine

def test_user_cannot_access_other_user_meal(db_session: Session):
    user_a = User(id=1, email="user_a@example.com", hashed_password="test")
    user_b = User(id=2, email="user_b@example.com", hashed_password="test")

    meal_of_b = NutritionMeal(id=1, user_id=user_b.id, meal_type="breakfast", date=date(2025, 1, 1))

    db_session.add_all([user_a, user_b, meal_of_b])
    db_session.commit()

    client = TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: UserContext(id=user_a.id, email=user_a.email, is_active=True)

    response = client.patch(f"/api/v1/nutrition/meal/{meal_of_b.id}", json={})

    assert response.status_code == 404
    assert response.json() == {"detail": "Meal not found"}

    app.dependency_overrides.clear()

def test_user_cannot_access_other_user_progress_entry(db_session: Session):
    user_a = User(id=1, email="user_a@example.com", hashed_password="test")
    user_b = User(id=2, email="user_b@example.com", hashed_password="test")

    progress_entry_of_b = ProgressEntry(id=1, user_id=user_b.id, metric="weight", value=70.0, date=date(2025, 1, 1))

    db_session.add_all([user_a, user_b, progress_entry_of_b])
    db_session.commit()

    client = TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: UserContext(id=user_a.id, email=user_a.email, is_active=True)

    response = client.delete(f"/api/v1/progress/{progress_entry_of_b.id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Progress entry not found"}

    app.dependency_overrides.clear()

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date

from app.main import app
from app.auth.deps import get_current_user, UserContext
from app.auth.models import User
from app.nutrition.models import NutritionMeal
from app.progress.models import ProgressEntry
from app.routines.models import Routine

def test_user_cannot_access_other_user_meal(db_session: Session, test_client: TestClient):
    user_a = User(id=1, email="user_a@example.com", hashed_password="test")
    user_b = User(id=2, email="user_b@example.com", hashed_password="test")

    meal_of_b = NutritionMeal(id=1, user_id=user_b.id, meal_type="breakfast", date=date(2025, 1, 1))

    db_session.add_all([user_a, user_b, meal_of_b])
    db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: UserContext(id=user_a.id, email=user_a.email, is_active=True)

    response = test_client.patch(f"/api/v1/nutrition/meal/{meal_of_b.id}", json={})

    assert response.status_code == 404
    assert response.json() == {"detail": "Meal not found"}

    app.dependency_overrides.clear()

def test_user_cannot_access_other_user_progress_entry(db_session: Session, test_client: TestClient):
    user_a = User(id=1, email="user_a@example.com", hashed_password="test")
    user_b = User(id=2, email="user_b@example.com", hashed_password="test")

    progress_entry_of_b = ProgressEntry(id=1, user_id=user_b.id, metric="weight", value=70.0, date=date(2025, 1, 1))

    db_session.add_all([user_a, user_b, progress_entry_of_b])
    db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: UserContext(id=user_a.id, email=user_a.email, is_active=True)

    response = test_client.delete(f"/api/v1/progress/{progress_entry_of_b.id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Progress entry not found"}

    app.dependency_overrides.clear()

def test_user_cannot_access_other_user_routine(db_session: Session, test_client: TestClient):
    user_a = User(id=1, email="user_a@example.com", hashed_password="test")
    user_b = User(id=2, email="user_b@example.com", hashed_password="test")

    routine_of_b = Routine(id=1, owner_id=user_b.id, name="Test Routine")

    db_session.add_all([user_a, user_b, routine_of_b])
    db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: UserContext(id=user_a.id, email=user_a.email, is_active=True)

    response = test_client.get(f"/api/v1/routines/{routine_of_b.id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Routine not found"}

    app.dependency_overrides.clear()
