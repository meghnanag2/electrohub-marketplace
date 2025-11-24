from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import verify_password, create_access_token

# 24 hours token expiry
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Fetch a user by email from user_accounts table.
    """
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Verify that the user exists and the password is correct.
    Returns the User object if authentication succeeds, otherwise None.
    """
    user = get_user_by_email(db, email)
    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def create_login_response(user: User) -> dict:
    """
    Build the JSON response for a successful login, including JWT and basic user info.
    """
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": getattr(user, "user_id", None),
            "email": user.email,
            "name": getattr(user, "name", None),
            "city": getattr(user, "city", None),
            "state": getattr(user, "state", None),
        },
    }
