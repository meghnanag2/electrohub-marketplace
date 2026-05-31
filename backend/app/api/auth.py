from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import authenticate_user, create_login_response
from app.core.rate_limit import login_bucket

router = APIRouter(prefix="/auth")


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    # Tight rate limit on login — prevents brute force (5 attempts/min per IP)
    allowed, wait = login_bucket.consume(f"ip:{request.client.host}")
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Retry after {wait} seconds.",
            headers={"Retry-After": str(wait)},
        )
    user = authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return create_login_response(user)
