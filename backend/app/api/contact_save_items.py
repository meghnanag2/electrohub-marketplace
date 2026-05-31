import redis
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import (
    ItemNotFoundException,
    RateLimitException,
    ValidationException,
    EmailServiceException,
)
from app.core.metrics import messages_sent, items_saved
from app.core.pubsub import publish_event
from app.core.redis_client import get_redis_client
from app.models.models import User
from app.services.email_service import EmailService
from app.services.save_items_service import SaveItemsService
from pydantic import BaseModel

log = structlog.get_logger()
router = APIRouter(prefix="/api", tags=["contact-save"])


class ContactMessage(BaseModel):
    subject: str
    message: str


@router.post("/listings/{item_id}/contact-seller")
def contact_seller(
    item_id: int,
    contact: ContactMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    if len(contact.subject) < 5:
        raise ValidationException("Subject must be at least 5 characters")
    if len(contact.message) < 20:
        raise ValidationException("Message must be at least 20 characters")

    item = db.execute(text("""
        SELECT m.seller_id, m.title, u.email, u.name
        FROM marketplace_items m
        JOIN user_accounts u ON m.seller_id = u.user_id
        WHERE m.item_id = :item_id AND m.is_active = true
    """), {"item_id": item_id}).first()

    if not item:
        raise ItemNotFoundException(f"Listing {item_id} not found or inactive")

    rate_key = f"contact:{current_user.user_id}:{item_id}:{datetime.now().strftime('%Y-%m-%d')}"
    count = redis_client.incr(rate_key)
    if count == 1:
        redis_client.expire(rate_key, 86400)
    if count > 5:
        raise RateLimitException("Too many contact attempts today. Try again tomorrow.", retry_after=86400)

    success = EmailService().send_contact_seller_email(
        to_email=item[2],
        from_email=current_user.email,
        from_name=current_user.name,
        subject=contact.subject,
        message=contact.message,
        item_title=item[1],
    )
    if not success:
        redis_client.decr(rate_key)
        raise EmailServiceException("Failed to send email. Please try again later.")

    db.execute(text("""
        INSERT INTO marketplace_messages (sender_id, receiver_id, item_id, message_text, sent_at)
        VALUES (:sender, :receiver, :item_id, :msg, NOW())
    """), {
        "sender": current_user.user_id,
        "receiver": item[0],
        "item_id": item_id,
        "msg": f"Subject: {contact.subject}\n\n{contact.message}",
    })
    db.commit()

    messages_sent.inc()
    publish_event("message_sent", {
        "buyer_id": current_user.user_id,
        "seller_id": item[0],
        "item_id": item_id,
    })
    log.info("contact_seller_success", buyer=current_user.user_id, item=item_id)
    return {"success": True, "message": "Message sent! Seller will contact you soon."}


@router.post("/users/saved-items")
def save_item(
    item_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    exists = db.execute(
        text("SELECT 1 FROM marketplace_items WHERE item_id = :id AND is_active = true"),
        {"id": item_id},
    ).first()
    if not exists:
        raise ItemNotFoundException(f"Item {item_id} not found")

    service = SaveItemsService(redis_client)
    success = service.save_item(current_user.user_id, item_id)

    if success:
        items_saved.inc()
        publish_event("item_saved", {"user_id": current_user.user_id, "item_id": item_id})

    return {"success": success, "message": "Item saved to wishlist!" if success else "Already saved"}


@router.delete("/users/saved-items")
def unsave_item(
    item_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    service = SaveItemsService(redis_client)
    success = service.unsave_item(current_user.user_id, item_id)
    return {"success": success, "message": "Removed from saved" if success else "Not saved"}


@router.get("/users/saved-items")
def get_saved_items(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis_client),
    db: Session = Depends(get_db),
):
    service = SaveItemsService(redis_client)
    item_ids = service.get_saved_items(current_user.user_id)
    if not item_ids:
        return {"total": 0, "items": []}

    placeholders = ",".join([f":{i}" for i in range(len(item_ids))])
    params = {str(i): int(iid) for i, iid in enumerate(item_ids)}
    params.update({"limit": limit, "skip": skip})

    rows = db.execute(
        text(f"""
            SELECT item_id, title, price, city, state, category, created_at
            FROM marketplace_items
            WHERE item_id IN ({placeholders})
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :skip
        """),
        params,
    ).fetchall()

    return {
        "total": len(item_ids),
        "skip": skip,
        "limit": limit,
        "items": [
            {
                "item_id": r[0], "title": r[1], "price": float(r[2]),
                "city": r[3], "state": r[4], "category": r[5],
                "created_at": str(r[6]),
            }
            for r in rows
        ],
    }


@router.get("/listings/{item_id}/is-saved")
def is_item_saved(
    item_id: int,
    current_user: User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    return {"is_saved": SaveItemsService(redis_client).is_saved(current_user.user_id, item_id)}


@router.get("/users/saved-items/count")
def get_saved_count(
    current_user: User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    return {"count": SaveItemsService(redis_client).get_saved_count(current_user.user_id)}
