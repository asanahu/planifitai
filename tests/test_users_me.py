"""Tests for /users/me endpoints"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.models import User
from app.main import app
from app.user_profile.models import ActivityLevel, Goal, UserProfile


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def user_with_profile(db_session: Session):
    """Create a user with a complete profile"""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    profile = UserProfile(
        user_id=user.id,
        age=30,
        height_cm=175.0,
        weight_kg=70.0,
        goal=Goal.MAINTAIN_WEIGHT,
        activity_level=ActivityLevel.MODERATELY_ACTIVE,
        profile_completed=True,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    return user, profile


@pytest.fixture
def user_without_profile(db_session: Session):
    """Create a user without a profile"""
    user = User(email="test2@example.com", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(user_with_profile):
    """Get auth headers for the user"""
    user, _ = user_with_profile

    # Create a simple token (in real tests you'd use proper JWT)
    from app.auth.services import create_access_token

    token = create_access_token({"sub": str(user.id), "token_type": "access"})
    return {"Authorization": f"Bearer {token}"}


def test_get_me_with_complete_profile(
    test_client: TestClient, user_with_profile, auth_headers
):
    """Test GET /users/me with complete profile"""
    user, profile = user_with_profile

    response = test_client.get("/api/v1/users/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["data"]["age"] == 30
    assert data["data"]["height_cm"] == 175.0
    assert data["data"]["weight_kg"] == 70.0
    assert data["data"]["goal"] == "maintain"
    assert data["data"]["activity_level"] == "moderate"
    assert data["data"]["profile_completed"] is True


def test_get_me_without_profile(test_client: TestClient, user_without_profile):
    """Test GET /users/me without profile"""
    user = user_without_profile

    from app.auth.services import create_access_token

    token = create_access_token({"sub": str(user.id), "token_type": "access"})
    headers = {"Authorization": f"Bearer {token}"}

    response = test_client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["data"]["age"] is None
    assert data["data"]["height_cm"] is None
    assert data["data"]["weight_kg"] is None
    assert data["data"]["goal"] is None
    assert data["data"]["activity_level"] is None
    assert data["data"]["profile_completed"] is False


def test_get_me_unauthorized(test_client: TestClient):
    """Test GET /users/me without token"""
    response = test_client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_put_me_profile_create_new(test_client: TestClient, user_without_profile):
    """Test PUT /users/me/profile creates new profile"""
    user = user_without_profile

    from app.auth.services import create_access_token

    token = create_access_token({"sub": str(user.id), "token_type": "access"})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "age": 25,
        "height_cm": 180,
        "weight_kg": 75.5,
        "goal": "gain_muscle",
        "activity_level": "active",
    }

    response = test_client.put(
        "/api/v1/users/me/profile", json=payload, headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["data"]["age"] == 25
    assert data["data"]["height_cm"] == 180
    assert data["data"]["weight_kg"] == 75.5
    assert data["data"]["goal"] == "gain_muscle"
    assert data["data"]["activity_level"] == "active"
    assert data["data"]["profile_completed"] is True


def test_put_me_profile_update_existing(
    test_client: TestClient, user_with_profile, auth_headers
):
    """Test PUT /users/me/profile updates existing profile"""
    user, profile = user_with_profile

    payload = {
        "age": 35,
        "height_cm": 185,
        "weight_kg": 80.0,
        "goal": "lose_weight",
        "activity_level": "very_active",
    }

    response = test_client.put(
        "/api/v1/users/me/profile", json=payload, headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["data"]["age"] == 35
    assert data["data"]["height_cm"] == 185
    assert data["data"]["weight_kg"] == 80.0
    assert data["data"]["goal"] == "lose_weight"
    assert data["data"]["activity_level"] == "very_active"
    assert data["data"]["profile_completed"] is True


def test_put_me_profile_validation_errors(
    test_client: TestClient, user_without_profile
):
    """Test PUT /users/me/profile validation errors"""
    user = user_without_profile

    from app.auth.services import create_access_token

    token = create_access_token({"sub": str(user.id), "token_type": "access"})
    headers = {"Authorization": f"Bearer {token}"}

    # Test invalid age
    payload = {
        "age": 5,  # Too young
        "height_cm": 180,
        "weight_kg": 75.5,
        "goal": "gain_muscle",
        "activity_level": "active",
    }

    response = test_client.put(
        "/api/v1/users/me/profile", json=payload, headers=headers
    )
    assert response.status_code == 422

    # Test invalid goal
    payload = {
        "age": 25,
        "height_cm": 180,
        "weight_kg": 75.5,
        "goal": "invalid_goal",
        "activity_level": "active",
    }

    response = test_client.put(
        "/api/v1/users/me/profile", json=payload, headers=headers
    )
    assert response.status_code == 422


def test_put_me_profile_unauthorized(test_client: TestClient):
    """Test PUT /users/me/profile without token"""
    payload = {
        "age": 25,
        "height_cm": 180,
        "weight_kg": 75.5,
        "goal": "gain_muscle",
        "activity_level": "active",
    }

    response = test_client.put("/api/v1/users/me/profile", json=payload)
    assert response.status_code == 401


def test_put_me_profile_idempotent(
    test_client: TestClient, user_with_profile, auth_headers
):
    """Test PUT /users/me/profile is idempotent"""
    user, profile = user_with_profile

    payload = {
        "age": 30,
        "height_cm": 175,
        "weight_kg": 70.0,
        "goal": "maintain",
        "activity_level": "moderate",
    }

    # First request
    response1 = test_client.put(
        "/api/v1/users/me/profile", json=payload, headers=auth_headers
    )
    assert response1.status_code == 200

    # Second identical request
    response2 = test_client.put(
        "/api/v1/users/me/profile", json=payload, headers=auth_headers
    )
    assert response2.status_code == 200

    # Both should return the same data
    assert response1.json() == response2.json()
