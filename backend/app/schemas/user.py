from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    name: str
    password: str

class UserLogin(UserBase):
    password: str

class UserOut(BaseModel):
    user_id: str
    email: EmailStr
    name: str
    profile_picture: Optional[str] = None

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
