import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException
from typing import Optional

from sqlmodel import Session, select
from app.models import AdminUser
from app.db import engine

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")  # override in production via env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 60 * 60 * 6  # 6 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def create_access_token(subject: str, expires_delta: int = ACCESS_TOKEN_EXPIRE_SECONDS) -> str:
    to_encode = {"sub": subject, "exp": datetime.utcnow() + timedelta(seconds=expires_delta)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub: str = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return sub
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# DB helpers
def get_admin_by_username(session: Session, username: str) -> Optional[AdminUser]:
    statement = select(AdminUser).where(AdminUser.username == username)
    result = session.exec(statement).first()
    return result

def authenticate_admin(session: Session, username: str, password: str) -> Optional[AdminUser]:
    user = get_admin_by_username(session, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_admin(session: Session, username: str, password: str, is_superuser: bool = True) -> AdminUser:
    existing = get_admin_by_username(session, username)
    if existing:
        return existing
    hashed = get_password_hash(password)
    user = AdminUser(username=username, hashed_password=hashed, is_superuser=is_superuser)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user