from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.user_profile import models, schemas
from app.auth.models import User

def get_profile_by_user_id(db: Session, user_id: int) -> models.UserProfile | None:
    return db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()

def create_user_profile(db: Session, user: User, profile_data: schemas.UserProfileCreate) -> models.UserProfile:
    profile = models.UserProfile(**profile_data.dict(), user_id=user.id)
    db.add(profile)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists for this user.",
        )
    db.refresh(profile)
    return profile

def update_user_profile(db: Session, profile: models.UserProfile, profile_data: schemas.UserProfileUpdate) -> models.UserProfile:
    update_data = profile_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile

def delete_user_profile(db: Session, profile: models.UserProfile):
    db.delete(profile)
    db.commit()
