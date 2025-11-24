from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt  # PyJWT
from app.core.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    Demo-only: compare plain text password.

    In production you would use a secure hash (bcrypt, argon2, etc.).
    """
    return plain_password == stored_password


def get_password_hash(password: str) -> str:
    """
    Demo-only: store plain text password as-is.
    """
    return password


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT token using the config secret.
    Tries JWT_SECRET_KEY first, then SECRET_KEY, otherwise falls back to a default.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})

    # Handle both possible config names
    secret = getattr(settings, "JWT_SECRET_KEY", None) or getattr(settings, "SECRET_KEY", None) or "change-me"

    encoded_jwt = jwt.encode(to_encode, secret, algorithm=ALGORITHM)
    return encoded_jwt
