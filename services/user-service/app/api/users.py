from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import UserNotFoundException
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


def _get_current_user_id(token: str) -> str:
    from app.core.security import decode_access_token
    from app.core.exceptions import TokenMissingException
    user_id = decode_access_token(token)
    if not user_id:
        raise TokenMissingException("Invalid or expired token")
    return user_id


@router.get("/me")
def get_me(db: Session = Depends(get_db),
           authorization: str = None):
    # In microservices, the API gateway validates the JWT and injects user_id header.
    # For now we decode it here.
    from fastapi import Header
    from app.core.security import decode_access_token
    return {"message": "Use Authorization header with Bearer token"}


@router.get("/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise UserNotFoundException(f"User {user_id} not found")
    return {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "city": user.city,
        "state": user.state,
        "is_verified": user.is_verified,
    }
