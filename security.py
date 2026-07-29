import os
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import bcrypt

SECRET_KEY = "YOUR_SUPER_SECURE_RANDOM_SECRET_KEY"  # In production, use os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security_bearer = HTTPBearer()


def _normalize_password(password: str) -> str:
    return password.encode("utf-8")[:72].decode("utf-8", errors="ignore")


def hash_password(password: str) -> str:
    safe_password = _normalize_password(password)
    return bcrypt.hashpw(safe_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    safe_password = _normalize_password(plain_password)
    return bcrypt.checkpw(safe_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# Dependency to secure routes by validating the token and matching authorized roles
class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, credentials: HTTPAuthorizationCredentials = Depends(security_bearer)) -> dict:
        token = credentials.credentials
        payload = verify_token(token)
        user_role = payload.get("role")
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )
        return payload