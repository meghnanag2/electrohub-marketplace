from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import verify_password
from app.models.models import User

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/check-db")
def check_database(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        user_count = db.query(User).count()
        return {"status": "ok", "total_users": user_count}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/test-password")
def test_password(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        user = db.query(User).filter(User.email == "demo@electrohub.com").first()
        if not user:
            return {"status": "error", "error": "Demo user not found"}
        is_valid = verify_password("password123", user.password_hash)
        return {"status": "ok", "email": user.email, "password_matches": is_valid}
    except Exception as e:
        return {"status": "error", "error": str(e)}
