# backend/app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models.user import User  # you already have this model


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    user: dict


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user.user_id)

    user_dict = {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "city": user.city,
        "state": user.state,
        "profile_picture": user.profile_picture,
    }

    return {"access_token": token, "user": user_dict}


@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        user_id=f"user_{request.email}",
        email=request.email,
        password_hash=get_password_hash(request.password),
        name=request.name,
        is_active=True,
        is_verified=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.user_id)

    return {
        "access_token": token,
        "user": {
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
        },
    }
