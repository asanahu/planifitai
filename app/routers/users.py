import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import UserContext, get_current_user
from app.core.database import get_db
from app.core.errors import ok
from app.user_profile import models as profile_models
from app.user_profile import schemas as profile_schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


def _map_goal_api_to_db(value: str) -> profile_models.Goal:
    mapping = {
        "lose_weight": profile_models.Goal.LOSE_WEIGHT,
        "maintain": profile_models.Goal.MAINTAIN_WEIGHT,
        "gain_muscle": profile_models.Goal.GAIN_WEIGHT,
    }
    if value not in mapping:
        raise ValueError("invalid goal")
    return mapping[value]


def _map_activity_api_to_db(value: str) -> profile_models.ActivityLevel:
    mapping = {
        "sedentary": profile_models.ActivityLevel.SEDENTARY,
        "light": profile_models.ActivityLevel.LIGHTLY_ACTIVE,
        "moderate": profile_models.ActivityLevel.MODERATELY_ACTIVE,
        "active": profile_models.ActivityLevel.VERY_ACTIVE,
        "very_active": profile_models.ActivityLevel.EXTRA_ACTIVE,
    }
    if value not in mapping:
        raise ValueError("invalid activity_level")
    return mapping[value]


def _map_goal_db_to_api(value: profile_models.Goal | None) -> str | None:
    if value is None:
        return None
    reverse = {
        profile_models.Goal.LOSE_WEIGHT: "lose_weight",
        profile_models.Goal.MAINTAIN_WEIGHT: "maintain",
        profile_models.Goal.GAIN_WEIGHT: "gain_muscle",
    }
    return reverse.get(value)


def _map_activity_db_to_api(
    value: profile_models.ActivityLevel | None,
) -> str | None:
    if value is None:
        return None
    reverse = {
        profile_models.ActivityLevel.SEDENTARY: "sedentary",
        profile_models.ActivityLevel.LIGHTLY_ACTIVE: "light",
        profile_models.ActivityLevel.MODERATELY_ACTIVE: "moderate",
        profile_models.ActivityLevel.VERY_ACTIVE: "active",
        profile_models.ActivityLevel.EXTRA_ACTIVE: "very_active",
    }
    return reverse.get(value)


def _is_completed(p: profile_models.UserProfile | None) -> bool:
    if not p:
        return False
    return (
        isinstance(p.age, int)
        and 14 <= p.age <= 100
        and isinstance(p.height_cm, (int, float))
        and 120 <= float(p.height_cm) <= 220
        and isinstance(p.weight_kg, (int, float))
        and 30 <= float(p.weight_kg) <= 300
        and p.goal is not None
        and p.activity_level is not None
    )


@router.get("/me", response_model=profile_schemas.MeProfileOut)
def get_me(
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    profile = (
        db.query(profile_models.UserProfile)
        .filter(profile_models.UserProfile.user_id == current_user.id)
        .first()
    )
    completed = _is_completed(profile)
    if profile and profile.profile_completed != completed:
        profile.profile_completed = completed
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return ok(
        profile_schemas.MeProfileOut(
            age=profile.age if profile else None,
            height_cm=(
                float(profile.height_cm)
                if profile and profile.height_cm is not None
                else None
            ),
            weight_kg=(
                float(profile.weight_kg)
                if profile and profile.weight_kg is not None
                else None
            ),
            goal=_map_goal_db_to_api(profile.goal) if profile else None,
            activity_level=(
                _map_activity_db_to_api(profile.activity_level) if profile else None
            ),
            profile_completed=completed,
        )
    )


@router.put("/me/profile", response_model=profile_schemas.MeProfileOut)
def put_me_profile(
    payload: profile_schemas.MeProfileIn,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    profile = (
        db.query(profile_models.UserProfile)
        .filter(profile_models.UserProfile.user_id == current_user.id)
        .first()
    )
    try:
        goal_db = _map_goal_api_to_db(payload.goal)
        activity_db = _map_activity_api_to_db(payload.activity_level)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )

    if not profile:
        profile = profile_models.UserProfile(
            user_id=current_user.id,
        )

    profile.age = payload.age
    profile.height_cm = float(payload.height_cm)
    profile.weight_kg = float(payload.weight_kg)
    profile.goal = goal_db
    profile.activity_level = activity_db
    profile.profile_completed = _is_completed(profile)

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return ok(
        profile_schemas.MeProfileOut(
            age=profile.age,
            height_cm=(
                float(profile.height_cm) if profile.height_cm is not None else None
            ),
            weight_kg=(
                float(profile.weight_kg) if profile.weight_kg is not None else None
            ),
            goal=_map_goal_db_to_api(profile.goal),
            activity_level=_map_activity_db_to_api(profile.activity_level),
            profile_completed=profile.profile_completed,
        )
    )
