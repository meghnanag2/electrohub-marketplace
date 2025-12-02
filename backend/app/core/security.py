# backend/app/core/security.py
from datetime import datetime, timedelta
import hashlib
import jwt
import os
from typing import Optional
from jose import JWTError, jwt  # you probably already have this import
from app.core.config import settings  # or wherever SECRET_KEY/ALGORITHM live


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "electrohub-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 60 * 24 * 7))


def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, stored_password: str) -> bool:
    return get_password_hash(plain_password) == stored_password


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": str(subject), "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# backend/app/core/security.py


def decode_token(token: str) -> dict | None:
    """
    Decode a JWT access token.
    Returns payload dict or None if invalid/expired.
    Never raises, so routes can safely call it.
    """
    if not token:
        return None

    # Strip "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1]

    # Try to be flexible about where the secret/algorithm are stored
    secret = (
        getattr(settings, "SECRET_KEY", None)
        or getattr(settings, "JWT_SECRET_KEY", None)
        or getattr(settings, "JWT_SECRET", None)
        or "changeme"
    )
    algorithm = getattr(settings, "ALGORITHM", "HS256")

    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        return payload
    except JWTError:
        return None