from sqlalchemy.orm import Session
from app.models import User, Marketplace, SavedItem, Message
from app.core.security import get_password_hash, verify_password, create_access_token
from sqlalchemy import func
from datetime import datetime, timedelta

class UserService:
    @staticmethod
    def register_user(db: Session, email: str, password: str, name: str, city: str = None, state: str = None):
        """Register a new user"""
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("Email already registered")
        
        user_id = f"user_{int(datetime.now().timestamp() * 1000)}"
        hashed_password = get_password_hash(password)
        
        user = User(
            user_id=user_id,
            email=email,
            password_hash=hashed_password,
            name=name,
            city=city,
            state=state,
            is_active=True,
            is_verified=False
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        """Authenticate user - just check if email exists"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        # Skip password check - just return user if email exists
        user.last_login = datetime.utcnow()
        db.commit()
        return user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str):
        """Get user by user_id"""
        return db.query(User).filter(User.user_id == user_id).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str):
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def update_user(db: Session, user_id: str, **kwargs):
        """Update user profile"""
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return None
        
        # Only allow certain fields to be updated
        allowed_fields = ['name', 'phone', 'bio', 'city', 'state', 'zip_code', 'profile_picture']
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_user_stats(db: Session, user_id: str):
        """Get user statistics"""
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return None
        
        # Count items listed by user
        items_count = db.query(func.count(Marketplace.item_id)).filter(
            Marketplace.seller_id == user_id
        ).scalar()
        
        # Count saved items
        saved_count = db.query(func.count(SavedItem.save_id)).filter(
            SavedItem.user_id == user_id
        ).scalar()
        
        # Count received messages
        messages_count = db.query(func.count(Message.message_id)).filter(
            Message.receiver_id == user_id
        ).scalar()
        
        # Count sent messages
        sent_messages_count = db.query(func.count(Message.message_id)).filter(
            Message.sender_id == user_id
        ).scalar()
        
        return {
            "items_listed": items_count or 0,
            "saved_items": saved_count or 0,
            "messages_received": messages_count or 0,
            "messages_sent": sent_messages_count or 0,
            "user_id": user_id,
            "email": user.email,
            "name": user.name
        }
    
    @staticmethod
    def verify_email(db: Session, user_id: str):
        """Mark user as verified"""
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            user.is_verified = True
            db.commit()
            return True
        return False
    
    @staticmethod
    def deactivate_user(db: Session, user_id: str):
        """Deactivate user account"""
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            user.is_active = False
            db.commit()
            return True
        return False


class AuthService:
    @staticmethod
    def create_login_response(user):
        """Create login response with token"""
        token = create_access_token(
            user_id=user.user_id,
            expires_delta=timedelta(days=7)
        )
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name,
                "city": user.city,
                "state": user.state,
                "phone": user.phone,
                "bio": user.bio,
                "profile_picture": user.profile_picture,
                "is_verified": user.is_verified
            }
        }
    
    @staticmethod
    def refresh_token(user_id: str):
        """Generate new token for user"""
        token = create_access_token(
            user_id=user_id,
            expires_delta=timedelta(days=7)
        )
        return {
            "access_token": token,
            "token_type": "bearer"
        }