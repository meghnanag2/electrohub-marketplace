from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import UserActivity, Message, Interaction, SavedItem
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class ActivityService:
    @staticmethod
    def log_activity(db: Session, user_id, activity_type, action, item_id=None, metadata=None, session_id=None, ip_address=None, user_agent=None):
        activity = UserActivity(
            user_id=user_id,
            item_id=item_id,
            activity_type=activity_type,
            action=action,
            metadata=json.dumps(metadata) if metadata else None,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(activity)
        db.commit()
        logger.info(f"📊 Activity logged: {activity_type}")
        return activity
    
    @staticmethod
    def get_user_activities(db: Session, user_id, skip=0, limit=100):
        return db.query(UserActivity).filter(UserActivity.user_id == user_id).order_by(UserActivity.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def log_item_view(db: Session, user_id, item_id, session_id, ip_address, user_agent):
        ActivityService.log_activity(db, user_id, "view", f"Viewed item {item_id}", item_id, session_id=session_id, ip_address=ip_address, user_agent=user_agent)
        
        interaction = Interaction(user_id=user_id, item_id=item_id, event_type="view", session_id=session_id)
        db.add(interaction)
        db.commit()
    
    @staticmethod
    def get_analytics(db: Session, days=7):
        result = db.execute(text("SELECT COUNT(DISTINCT user_id), COUNT(*) FROM user_activity WHERE created_at > NOW() - INTERVAL ':days days'"), {"days": days}).fetchall()
        return {"users": result[0][0] or 0, "activities": result[0][1] or 0}

class MessageService:
    @staticmethod
    def send_message(db: Session, sender_id, receiver_id, item_id, subject, message_text):
        msg = Message(sender_id=sender_id, receiver_id=receiver_id, item_id=item_id, subject=subject, message_text=message_text)
        db.add(msg)
        db.commit()
        db.refresh(msg)
        logger.info(f"💬 Message sent")
        return msg
    
    @staticmethod
    def get_user_messages(db: Session, user_id, skip=0, limit=50):
        return db.query(Message).filter(Message.receiver_id == user_id).order_by(Message.sent_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def mark_as_read(db: Session, message_id):
        msg = db.query(Message).filter(Message.message_id == message_id).first()
        if msg:
            msg.is_read = True
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_unread_count(db: Session, user_id):
        return db.query(Message).filter(Message.receiver_id == user_id, Message.is_read == False).count()

class SavedItemService:
    @staticmethod
    def save_item(db: Session, user_id, item_id):
        existing = db.query(SavedItem).filter(SavedItem.user_id == user_id, SavedItem.item_id == item_id).first()
        if existing:
            return False
        
        saved = SavedItem(user_id=user_id, item_id=item_id)
        db.add(saved)
        db.execute(text("UPDATE marketplace_items SET saves_count = saves_count + 1 WHERE item_id = :iid"), {"iid": item_id})
        db.commit()
        logger.info(f"❤️ Item saved")
        return True
    
    @staticmethod
    def unsave_item(db: Session, user_id, item_id):
        saved = db.query(SavedItem).filter(SavedItem.user_id == user_id, SavedItem.item_id == item_id).first()
        if not saved:
            return False
        
        db.delete(saved)
        db.execute(text("UPDATE marketplace_items SET saves_count = saves_count - 1 WHERE item_id = :iid"), {"iid": item_id})
        db.commit()
        return True
    
    @staticmethod
    def is_saved(db: Session, user_id, item_id):
        return db.query(SavedItem).filter(SavedItem.user_id == user_id, SavedItem.item_id == item_id).first() is not None
    
    @staticmethod
    def get_saved_items(db: Session, user_id, skip=0, limit=20):
        query = db.query(SavedItem).filter(SavedItem.user_id == user_id)
        total = query.count()
        items = query.order_by(SavedItem.saved_at.desc()).offset(skip).limit(limit).all()
        return total, items
