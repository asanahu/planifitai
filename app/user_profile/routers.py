import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.deps import get_current_user
from app.auth.models import User
from app.user_profile import schemas, services, models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])

@router.post("", response_model=schemas.UserProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(payload: schemas.UserProfileCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = services.create_user_profile(db, current_user, payload)
    logger.info("Profile created for user %s", current_user.id)
    return profile

@router.get("/me", response_model=schemas.UserProfileRead)
def get_my_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = services.get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile

@router.patch("", response_model=schemas.UserProfileRead)
def update_my_profile(payload: schemas.UserProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = services.get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    profile = services.update_user_profile(db, profile, payload)
    logger.info("Profile updated for user %s", current_user.id)
    return profile

@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = services.get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    services.delete_user_profile(db, profile)
    logger.info("Profile deleted for user %s", current_user.id)
    return
