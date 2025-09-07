"""Tests simples para /users/me endpoints sin encriptación PHI"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.auth.models import User
from app.user_profile.models import UserProfile, ActivityLevel, Goal


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def user_with_profile_simple(db_session: Session):
    """Create a user with a complete profile (sin campos encriptados)"""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    profile = UserProfile(
        user_id=user.id,
        age=30,
        # No incluimos height_cm, weight_kg para evitar encriptación
        goal=Goal.MAINTAIN_WEIGHT,
        activity_level=ActivityLevel.MODERATELY_ACTIVE,
        profile_completed=True
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    
    return user, profile


@pytest.fixture
def user_without_profile_simple(db_session: Session):
    """Create a user without a profile"""
    user = User(email="test2@example.com", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers_simple(user_with_profile_simple):
    """Get auth headers for the user"""
    user, _ = user_with_profile_simple
    
    # Create a simple token (in real tests you'd use proper JWT)
    from app.auth.services import create_access_token
    token = create_access_token({"sub": str(user.id), "token_type": "access"})
    return {"Authorization": f"Bearer {token}"}


def test_get_me_with_complete_profile_simple(test_client: TestClient, user_with_profile_simple, auth_headers_simple):
    """Test GET /users/me with complete profile (sin campos encriptados)"""
    user, profile = user_with_profile_simple
    
    response = test_client.get("/api/v1/users/me", headers=auth_headers_simple)
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["data"]["age"] == 30
    assert data["data"]["height_cm"] is None  # No incluido en el perfil
    assert data["data"]["weight_kg"] is None   # No incluido en el perfil
    assert data["data"]["goal"] == "maintain"
    assert data["data"]["activity_level"] == "moderate"
    assert data["data"]["profile_completed"] is False  # Faltan height_cm y weight_kg


def test_get_me_without_profile_simple(test_client: TestClient, user_without_profile_simple):
    """Test GET /users/me without profile"""
    user = user_without_profile_simple
    
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


def test_get_me_unauthorized_simple(test_client: TestClient):
    """Test GET /users/me without token"""
    response = test_client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_put_me_profile_validation_errors_simple(test_client: TestClient, user_without_profile_simple):
    """Test PUT /users/me/profile validation errors"""
    user = user_without_profile_simple
    
    from app.auth.services import create_access_token
    token = create_access_token({"sub": str(user.id), "token_type": "access"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test invalid age
    payload = {
        "age": 5,  # Too young
        "height_cm": 180,
        "weight_kg": 75.5,
        "goal": "gain_muscle",
        "activity_level": "active"
    }
    
    response = test_client.put("/api/v1/users/me/profile", json=payload, headers=headers)
    assert response.status_code == 422
    
    # Test invalid goal
    payload = {
        "age": 25,
        "height_cm": 180,
        "weight_kg": 75.5,
        "goal": "invalid_goal",
        "activity_level": "active"
    }
    
    response = test_client.put("/api/v1/users/me/profile", json=payload, headers=headers)
    assert response.status_code == 422


def test_put_me_profile_unauthorized_simple(test_client: TestClient):
    """Test PUT /users/me/profile without token"""
    payload = {
        "age": 25,
        "height_cm": 180,
        "weight_kg": 75.5,
        "goal": "gain_muscle",
        "activity_level": "active"
    }
    
    response = test_client.put("/api/v1/users/me/profile", json=payload)
    assert response.status_code == 401
