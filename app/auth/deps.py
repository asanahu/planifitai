from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.auth import services
from app.auth.models import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


class UserContext(BaseModel):
    id: int
    email: str | None = None
    is_active: bool = True


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> UserContext:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = services.decode_token(token)
    if not payload:
        raise cred_exc
    if payload.get("token_type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type for this operation",
            headers={"WWW-Authenticate": "Bearer"},
        )
    sub = payload.get("sub")
    user = db.query(User).filter(User.id == int(sub)).first() if sub is not None else None
    if not user:
        raise cred_exc
    return UserContext(id=user.id, email=user.email, is_active=True)

