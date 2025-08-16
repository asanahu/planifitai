import logging

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import models, schemas, services
from app.auth.deps import UserContext, get_current_user
from app.core.database import get_db
from app.core.errors import (
    AUTH_INVALID_CREDENTIALS,
    err,
    ok,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED
)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = services.create_user(db, payload.email, payload.password)
    return ok(user, status.HTTP_201_CREATED)


@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = services.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        return err(
            AUTH_INVALID_CREDENTIALS,
            "Incorrect email or password",
            status.HTTP_401_UNAUTHORIZED,
        )

    access_token = services.create_access_token({"sub": str(user.id)})
    refresh_token = services.create_refresh_token({"sub": str(user.id)})

    logger.info("User %s logged in", user.id)

    return ok(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    )


@router.post("/refresh", response_model=schemas.Token)
def refresh_token(
    refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)
):
    payload = services.decode_token(refresh_token)
    if not payload or payload.get("token_type") != "refresh":
        return err(
            AUTH_INVALID_CREDENTIALS,
            "Invalid refresh token",
            status.HTTP_401_UNAUTHORIZED,
        )

    user_id = payload.get("sub")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return err(
            AUTH_INVALID_CREDENTIALS,
            "Invalid refresh token",
            status.HTTP_401_UNAUTHORIZED,
        )

    access_token = services.create_access_token({"sub": str(user.id)})
    new_refresh_token = services.create_refresh_token({"sub": str(user.id)})

    logger.info("User %s refreshed token", user.id)

    return ok(
        {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
    )


@router.get("/me", response_model=schemas.UserRead)
def me(
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    user = db.get(models.User, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return ok(user)
