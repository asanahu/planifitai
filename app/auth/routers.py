from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth import schemas, services, models
from app.auth.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = services.create_user(db, payload.email, payload.password)
    return user

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = services.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = services.create_access_token({"sub": str(user.id)})
    refresh_token = services.create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post("/refresh", response_model=schemas.Token)
def refresh_token(refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    payload = services.decode_token(refresh_token)
    if not payload or payload.get("token_type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user_id = payload.get("sub")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    access_token = services.create_access_token({"sub": str(user.id)})
    new_refresh_token = services.create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }

@router.get("/me", response_model=schemas.UserRead)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user