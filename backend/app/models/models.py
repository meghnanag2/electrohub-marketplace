from sqlalchemy import Column, String, Integer, TIMESTAMP, Boolean, Float, Text, ForeignKey, BigInteger
from app.core.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "user_accounts"
    
    user_id = Column(String(255), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(500))
    name = Column(String(255))
    phone = Column(String(50))
    profile_picture = Column(Text)
    bio = Column(Text)
    city = Column(String(100), index=True)
    state = Column(String(100), index=True)
    zip_code = Column(Integer)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    last_login = Column(TIMESTAMP)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

class Marketplace(Base):
    __tablename__ = "marketplace_items"
    
    item_id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(String(255), ForeignKey("user_accounts.user_id", ondelete="CASCADE"), index=True)
    title = Column(String(255), index=True)
    description = Column(Text)
    category = Column(String(100), index=True)
    price = Column(Float)
    city = Column(String(100), index=True)
    state = Column(String(100), index=True)
    zip_code = Column(Integer)
    condition = Column(String(50), default="new")
    views_count = Column(Integer, default=0)
    saves_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)
    is_active = Column(Boolean, default=True, index=True)

class ItemImage(Base):
    __tablename__ = "item_images"
    
    image_id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("marketplace_items.item_id", ondelete="CASCADE"), index=True)
    image_url = Column(Text)
    is_thumbnail = Column(Boolean, default=False)
    upload_order = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "marketplace_messages"
    
    message_id = Column(BigInteger, primary_key=True)
    sender_id = Column(String(255), ForeignKey("user_accounts.user_id", ondelete="CASCADE"), index=True)
    receiver_id = Column(String(255), ForeignKey("user_accounts.user_id", ondelete="CASCADE"), index=True)
    item_id = Column(Integer, ForeignKey("marketplace_items.item_id", ondelete="CASCADE"), index=True)
    subject = Column(String(255))
    message_text = Column(Text)
    sent_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    is_read = Column(Boolean, default=False, index=True)

class SavedItem(Base):
    __tablename__ = "item_saved"
    
    save_id = Column(Integer, primary_key=True)
    user_id = Column(String(255), ForeignKey("user_accounts.user_id", ondelete="CASCADE"), index=True)
    item_id = Column(Integer, ForeignKey("marketplace_items.item_id", ondelete="CASCADE"), index=True)
    saved_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)

class UserActivity(Base):
    __tablename__ = "user_activity"
    
    activity_id = Column(BigInteger, primary_key=True)
    user_id = Column(String(255), ForeignKey("user_accounts.user_id", ondelete="CASCADE"), index=True)
    item_id = Column(Integer, ForeignKey("marketplace_items.item_id", ondelete="SET NULL"), nullable=True)
    activity_type = Column(String(50), index=True)
    action = Column(String(255))
    activity_metadata = Column(Text)
    session_id = Column(String(255))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)

class Interaction(Base):
    __tablename__ = "item_interactions"
    
    interaction_id = Column(BigInteger, primary_key=True)
    user_id = Column(String(255), ForeignKey("user_accounts.user_id", ondelete="CASCADE"), index=True)
    item_id = Column(Integer, ForeignKey("marketplace_items.item_id", ondelete="CASCADE"), index=True)
    event_type = Column(String(20), index=True)
    event_time = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    session_id = Column(String(255))
