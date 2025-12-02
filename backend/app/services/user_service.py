from app.models.models import User
from sqlalchemy.orm import Session
from app.core.database import get_db

def verify_user(email: str, password: str):
    db: Session = next(get_db())
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None

    # VERY SIMPLE — plain text compare
    return user if user.password == password else None
