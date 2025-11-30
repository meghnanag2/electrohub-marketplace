from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.services.email_service import EmailService
from app.services.save_items_service import SaveItemsService
from pydantic import BaseModel, EmailStr
import redis
import json
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/api", tags=["contact-save"])

# Database models
class ContactMessage(BaseModel):
    subject: str
    message: str

class SaveItemRequest(BaseModel):
    item_id: int

# ==================== CONTACT SELLER ====================

@router.post("/listings/{item_id}/contact-seller")
def contact_seller(
    item_id: int,
    contact: ContactMessage,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(lambda: redis.Redis(host='localhost', port=6379, decode_responses=True))
):
    """
    Contact seller about a listing
    
    Datacenter Scaling:
    - Rate limiting (Redis)
    - Async email (background worker)
    - Validation + error handling
    """
    
    # Get current user (mock - use JWT in production)
    user_id = "user_demo_001"
    
    try:
        # 1. GET USER & VALIDATE
        user_result = db.execute(text("""
            SELECT user_id, email, name FROM user_accounts WHERE user_id = :user_id
        """), {"user_id": user_id})
        
        user = user_result.first()
        if not user:
            raise HTTPException(401, "User not found")
        
        # 2. GET SELLER & ITEM
        item_result = db.execute(text("""
            SELECT m.seller_id, m.title, u.email, u.name
            FROM marketplace_items m
            JOIN user_accounts u ON m.seller_id = u.user_id
            WHERE m.item_id = :item_id AND m.is_active = true
        """), {"item_id": item_id})
        
        item = item_result.first()
        if not item:
            raise HTTPException(404, "Listing not found")
        
        # 3. RATE LIMITING (Redis)
        rate_key = f"contact:{user_id}:{item_id}:{datetime.now().strftime('%Y-%m-%d')}"
        email_count = redis_client.get(rate_key)
        
        if email_count and int(email_count) >= 5:
            raise HTTPException(429, "Too many contact attempts today. Try again tomorrow.")
        
        # 4. VALIDATE MESSAGE
        if len(contact.subject) < 5 or len(contact.message) < 20:
            raise HTTPException(400, "Subject (5+ chars) and message (20+ chars) required")
        
        # 5. SEND EMAIL (in production, use Pub/Sub)
        email_service = EmailService()
        success = email_service.send_contact_email(
            from_email=user[1],  # user email
            from_name=user[2],   # user name
            to_email=item[2],    # seller email
            subject=contact.subject,
            message=contact.message,
            item_title=item[1]   # item title
        )
        
        if not success:
            raise HTTPException(500, "Failed to send email. Try again later.")
        
        # 6. INCREMENT RATE LIMIT
        redis_client.incr(rate_key)
        redis_client.expire(rate_key, 86400)  # 24 hours
        
        # 7. LOG TO DATABASE (for analytics)
        db.execute(text("""
            INSERT INTO contact_messages (from_user_id, to_user_id, item_id, subject, message, created_at)
            VALUES (:from_user, :to_user, :item_id, :subject, :message, NOW())
        """), {
            'from_user': user_id,
            'to_user': item[0],
            'item_id': item_id,
            'subject': contact.subject,
            'message': contact.message
        })
        db.commit()
        
        return {
            "success": True,
            "message": "✅ Message sent! Seller will contact you soon."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(500, "An error occurred. Please try again.")

# ==================== SAVE ITEMS ====================

@router.post("/users/saved-items")
def save_item(
    item_id: int = Query(...),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(lambda: redis.Redis(host='localhost', port=6379, decode_responses=True))
):
    """Save item to wishlist"""
    
    user_id = "user_demo_001"  # Get from JWT in production
    
    # Validate item exists
    result = db.execute(text("SELECT item_id FROM marketplace_items WHERE item_id = :id AND is_active = true"), {"id": item_id})
    if not result.first():
        raise HTTPException(404, "Item not found")
    
    service = SaveItemsService(redis_client)
    success = service.save_item(user_id, item_id)
    
    if success:
        return {"success": True, "message": "❤️ Item saved to wishlist!"}
    else:
        return {"success": False, "message": "Already saved"}

@router.delete("/users/saved-items")
def unsave_item(
    item_id: int = Query(...),
    redis_client: redis.Redis = Depends(lambda: redis.Redis(host='localhost', port=6379, decode_responses=True))
):
    """Remove from wishlist"""
    
    user_id = "user_demo_001"
    service = SaveItemsService(redis_client)
    
    success = service.unsave_item(user_id, item_id)
    
    return {
        "success": success,
        "message": "Removed from saved" if success else "Not saved"
    }

@router.get("/users/saved-items")
def get_saved_items(
    skip: int = 0,
    limit: int = 20,
    redis_client: redis.Redis = Depends(lambda: redis.Redis(host='localhost', port=6379, decode_responses=True)),
    db: Session = Depends(get_db)
):
    """Get user's saved items with details"""
    
    user_id = "user_demo_001"
    service = SaveItemsService(redis_client)
    
    # Get saved item IDs from Redis
    item_ids = service.get_saved_items(user_id)
    
    if not item_ids:
        return {"total": 0, "items": []}
    
    # Fetch full details from database
    placeholders = ','.join([f':{i}' for i in range(len(item_ids))])
    params = {str(i): int(item_id) for i, item_id in enumerate(item_ids)}
    
    query = f"""
        SELECT item_id, title, price, city, state, category, created_at
        FROM marketplace_items
        WHERE item_id IN ({placeholders})
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :skip
    """
    params['limit'] = limit
    params['skip'] = skip
    
    result = db.execute(text(query), params)
    items = [
        {
            "item_id": row[0],
            "title": row[1],
            "price": float(row[2]),
            "city": row[3],
            "state": row[4],
            "category": row[5],
            "created_at": str(row[6])
        }
        for row in result
    ]
    
    return {
        "total": len(item_ids),
        "items": items,
        "skip": skip,
        "limit": limit
    }

@router.get("/listings/{item_id}/is-saved")
def is_item_saved(
    item_id: int,
    redis_client: redis.Redis = Depends(lambda: redis.Redis(host='localhost', port=6379, decode_responses=True))
):
    """Check if item is saved"""
    
    user_id = "user_demo_001"
    service = SaveItemsService(redis_client)
    
    is_saved = service.is_saved(user_id, item_id)
    
    return {"is_saved": is_saved}

@router.get("/users/saved-items/count")
def get_saved_count(
    redis_client: redis.Redis = Depends(lambda: redis.Redis(host='localhost', port=6379, decode_responses=True))
):
    """Get number of saved items"""
    
    user_id = "user_demo_001"
    service = SaveItemsService(redis_client)
    
    count = service.get_saved_count(user_id)
    
    return {"count": count}
