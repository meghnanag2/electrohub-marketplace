# backend/app/api/routes.py

"""
API routes: authentication + basic health/status.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)

router = APIRouter()


# ---------- Pydantic models ----------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    city: Optional[str] = None
    state: Optional[str] = None


# ---------- Helper ----------

def _get_user_by_email(db: Session, email: str):
    sql = text(
        """
        SELECT user_id, email, password_hash, name, city, state
        FROM user_accounts
        WHERE email = :email
        """
    )
    return db.execute(sql, {"email": email}).mappings().first()


# ---------- Endpoints ----------

@router.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Log a user in using email + password.
    Returns JWT + basic user info.
    """
    user = _get_user_by_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = create_access_token(subject=user["user_id"])

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user.get("name"),
            "city": user.get("city"),
            "state": user.get("state"),
        },
    }


@router.post("/auth/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user in user_accounts.
    """
    existing = _get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    from uuid import uuid4

    user_id = f"user_{uuid4().hex[:12]}"
    hashed_password = get_password_hash(payload.password)

    insert_sql = text(
        """
        INSERT INTO user_accounts
            (user_id, email, password_hash, name, city, state,
             created_at, is_active, is_verified)
        VALUES
            (:user_id, :email, :password_hash, :name, :city, :state,
             :created_at, TRUE, FALSE)
        """
    )

    db.execute(
        insert_sql,
        {
            "user_id": user_id,
            "email": payload.email,
            "password_hash": hashed_password,
            "name": payload.name,
            "city": payload.city,
            "state": payload.state,
            "created_at": datetime.utcnow(),
        },
    )
    db.commit()

    access_token = create_access_token(subject=user_id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user_id,
            "email": payload.email,
            "name": payload.name,
            "city": payload.city,
            "state": payload.state,
        },
    }


@router.get("/health")
def health(db: Session = Depends(get_db)):
    """
    Simple DB health check.
    """
    from sqlalchemy import text as _text

    try:
        db.execute(_text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as exc:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(exc),
        }


@router.get("/status")
def status():
    """
    API status endpoint.
    """
    return {
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
    }
