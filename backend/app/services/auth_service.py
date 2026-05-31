from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import User
from app.core.security import verify_password, create_access_token

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_login_response(user: User) -> dict:
    access_token = create_access_token(
        subject=user.user_id,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "email": user.email,
            "name": getattr(user, "name", None),
            "city": getattr(user, "city", None),
            "state": getattr(user, "state", None),
        },
    }
