from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.user_profile.models import UserProfile
from app.user_profile.schemas import UserProfileCreate, UserProfileUpdate
from app.auth.models import User


def get_profile_by_user_id(db: Session, user_id: int) -> UserProfile | None:
    return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()


def get_profile(db: Session, profile_id: int, current_user: User) -> UserProfile | None:
    return (
        db.query(UserProfile)
        .filter(UserProfile.id == profile_id, UserProfile.user_id == current_user.id)
        .first()
    )


def list_my_profiles(db: Session, current_user: User) -> list[UserProfile]:
    return db.query(UserProfile).filter(UserProfile.user_id == current_user.id).all()


def create_profile(db: Session, data: UserProfileCreate, current_user: User) -> UserProfile:
    obj = UserProfile(**data.model_dump())
    obj.user_id = current_user.id
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists for this user.",
        )
    db.refresh(obj)
    return obj


def update_profile(
    db: Session, profile_id: int, data: UserProfileUpdate, current_user: User
) -> UserProfile | None:
    obj = get_profile(db, profile_id, current_user)
    if not obj:
        return None
    update_data = data.model_dump(exclude_unset=True)
    update_data.pop("user_id", None)
    for field, value in update_data.items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_profile(db: Session, profile_id: int, current_user: User) -> bool:
    obj = get_profile(db, profile_id, current_user)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
