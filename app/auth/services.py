from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from jwt import PyJWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.config import settings

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_ctx.verify(password, hashed)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str, password: str) -> User:
    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(data: dict) -> str:
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_token({**data, "token_type": "access"}, expires)


def create_refresh_token(data: dict) -> str:
    expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_token({**data, "token_type": "refresh"}, expires)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except PyJWTError:
        return None
