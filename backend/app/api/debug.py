from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password
from app.models.user import User

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/check-db")
def check_database(db: Session = Depends(get_db)):
    """Check database connection and users"""
    try:
        user_count = db.query(User).count()
        print(f"\n=== DATABASE CHECK ===")
        print(f"Total users in database: {user_count}")
        
        users = db.query(User).all()
        user_list = []
        for user in users:
            print(f"User: {user.email} (ID: {user.user_id})")
            user_list.append({
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name
            })
        
        return {
            "status": "ok",
            "total_users": user_count,
            "users": user_list
        }
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {"status": "error", "error": str(e)}

@router.get("/test-password")
def test_password(db: Session = Depends(get_db)):
    """Test if password123 matches the demo user's hash"""
    try:
        user = db.query(User).filter(User.email == "demo@electrohub.com").first()
        
        if not user:
            return {"status": "error", "error": "Demo user not found"}
        
        print(f"\n=== PASSWORD TEST ===")
        print(f"User: {user.email}")
        print(f"Hash in DB: {user.password_hash}")
        
        is_valid = verify_password("password123", user.password_hash)
        print(f"Password 'password123' matches: {is_valid}")
        
        return {
            "status": "ok",
            "email": user.email,
            "password_matches": is_valid,
            "message": "✅ Password is correct!" if is_valid else "❌ Password does NOT match"
        }
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return {"status": "error", "error": str(e)}
