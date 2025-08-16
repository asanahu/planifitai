import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import UserContext, get_current_user
from app.core.database import get_db
from app.user_profile import schemas, services

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/", response_model=list[schemas.UserProfileRead])
def list_profiles(
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    return services.list_my_profiles(db, current_user)


@router.get("/{profile_id}", response_model=schemas.UserProfileRead)
def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    obj = services.get_profile(db, profile_id, current_user)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )
    return obj


@router.post(
    "/", response_model=schemas.UserProfileRead, status_code=status.HTTP_201_CREATED
)
def create_profile(
    payload: schemas.UserProfileCreate,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    profile = services.create_profile(db, payload, current_user)
    logger.info("Profile created for user %s", current_user.id)
    return profile


@router.put("/{profile_id}", response_model=schemas.UserProfileRead)
def update_profile(
    profile_id: int,
    payload: schemas.UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    profile = services.update_profile(db, profile_id, payload, current_user)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )
    logger.info("Profile updated for user %s", current_user.id)
    return profile


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    ok = services.delete_profile(db, profile_id, current_user)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )
    logger.info("Profile deleted for user %s", current_user.id)
    return
