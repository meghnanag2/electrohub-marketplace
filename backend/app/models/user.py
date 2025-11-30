from sqlalchemy import Column, String, Integer, TIMESTAMP, Boolean
from app.core.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "user_accounts"

    user_id = Column(String(255), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    name = Column(String(255))
    phone = Column(String(20))
    profile_picture = Column(String(500))
    bio = Column(String(500))
    city = Column(String(100))
    state = Column(String(100))
    zip_code = Column(Integer)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    last_login = Column(TIMESTAMP)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
