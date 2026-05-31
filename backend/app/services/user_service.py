from app.models.models import User
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password


def verify_user(email: str, password: str):
    db: Session = next(get_db())
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        return user if verify_password(password, user.password_hash) else None
    finally:
        db.close()
