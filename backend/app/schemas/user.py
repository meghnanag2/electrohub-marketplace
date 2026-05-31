from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    name: str
    password: str


class UserLogin(UserBase):
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email: EmailStr
    name: str
    profile_picture: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
