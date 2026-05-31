import os
import structlog
import redis
from fastapi import APIRouter, Depends, Query, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.exceptions import ItemNotFoundException
from app.grpc.user_client import verify_token

from app.core.kafka_client import publish as kafka_publish

log = structlog.get_logger()
router = APIRouter(prefix="/marketplace", tags=["marketplace"])

_redis = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True,
)


def _current_user(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    valid, user_id = verify_token(authorization[7:])
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id


@router.get("/items")
def list_items(
    category: str | None = None,
    search: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    condition: str | None = None,
    city: str | None = None,
    skip: int = 0,
    limit: int = Query(default=20, le=200),
    db: Session = Depends(get_db),
):
    filters = ["i.is_active = true"]
    params: dict = {"limit": limit, "skip": skip}

    if category:
        filters.append("i.category = :category")
        params["category"] = category
    if search:
        filters.append("(i.title ILIKE :search OR i.description ILIKE :search)")
        params["search"] = f"%{search}%"
    if min_price is not None:
        filters.append("i.price >= :min_price")
        params["min_price"] = min_price
    if max_price is not None:
        filters.append("i.price <= :max_price")
        params["max_price"] = max_price
    if condition:
        filters.append("i.condition = :condition")
        params["condition"] = condition
    if city:
        filters.append("i.city ILIKE :city")
        params["city"] = f"%{city}%"

    where = " AND ".join(filters)
    rows = db.execute(text(f"""
        SELECT i.item_id, i.title, i.price, i.category, i.condition,
               i.city, i.state, i.views_count, i.saves_count, i.created_at,
               img.image_url
        FROM marketplace_items i
        LEFT JOIN item_images img ON i.item_id = img.item_id AND img.is_thumbnail = true
        WHERE {where}
        ORDER BY i.created_at DESC
        LIMIT :limit OFFSET :skip
    """), params).fetchall()

    total = db.execute(text(
        f"SELECT COUNT(*) FROM marketplace_items i WHERE {where}"),
        {k: v for k, v in params.items() if k not in ("limit", "skip")}
    ).scalar()

    log.info("items_listed", count=len(rows), filters=params)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            {
                "item_id": r[0], "title": r[1], "price": float(r[2]),
                "category": r[3], "condition": r[4], "city": r[5],
                "state": r[6], "views_count": r[7], "saves_count": r[8],
                "created_at": str(r[9]), "thumbnail": r[10],
            }
            for r in rows
        ],
    }


@router.get("/items/{item_id}")
def get_item(item_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("""
        SELECT i.item_id, i.seller_id, i.title, i.description, i.category,
               i.price, i.condition, i.city, i.state, i.views_count,
               i.saves_count, i.created_at,
               ARRAY_AGG(img.image_url ORDER BY img.upload_order) FILTER (WHERE img.image_url IS NOT NULL) AS images
        FROM marketplace_items i
        LEFT JOIN item_images img ON i.item_id = img.item_id
        WHERE i.item_id = :id AND i.is_active = true
        GROUP BY i.item_id
    """), {"id": item_id}).first()

    if not row:
        raise ItemNotFoundException(f"Item {item_id} not found")

    db.execute(text(
        "UPDATE marketplace_items SET views_count = views_count + 1 WHERE item_id = :id"),
        {"id": item_id})
    db.commit()

    kafka_publish("item_viewed", {"item_id": item_id, "seller_id": row[1]}, key=str(item_id))

    return {
        "item_id": row[0], "seller_id": row[1], "title": row[2],
        "description": row[3], "category": row[4], "price": float(row[5]),
        "condition": row[6], "city": row[7], "state": row[8],
        "views_count": row[9], "saves_count": row[10],
        "created_at": str(row[11]), "images": row[12] or [],
    }


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT category, COUNT(*) as count
        FROM marketplace_items WHERE is_active = true
        GROUP BY category ORDER BY count DESC
    """)).fetchall()
    return [{"category": r[0], "count": r[1]} for r in rows]


# ── Wishlist / Save ────────────────────────────────────────────────────────────

@router.get("/items/{item_id}/saved")
def check_saved(
    item_id: int,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = _current_user(authorization)
    saved = bool(_redis.sismember(f"wishlist:{user_id}", item_id))
    return {"saved": saved}


@router.post("/items/{item_id}/save")
def save_item(
    item_id: int,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = _current_user(authorization)

    # Check item exists
    exists = db.execute(
        text("SELECT 1 FROM marketplace_items WHERE item_id = :id AND is_active = true"),
        {"id": item_id},
    ).first()
    if not exists:
        raise HTTPException(status_code=404, detail="Item not found")

    already = bool(_redis.sismember(f"wishlist:{user_id}", item_id))
    if already:
        return {"saved": True, "saves_count": None}

    # Redis SET
    _redis.sadd(f"wishlist:{user_id}", item_id)

    # Persist to PostgreSQL
    db.execute(text("""
        INSERT INTO item_saved (user_id, item_id, saved_at)
        VALUES (:uid, :iid, NOW())
        ON CONFLICT DO NOTHING
    """), {"uid": user_id, "iid": item_id})
    db.execute(text(
        "UPDATE marketplace_items SET saves_count = saves_count + 1 WHERE item_id = :id"
    ), {"id": item_id})
    db.commit()

    row = db.execute(
        text("SELECT saves_count FROM marketplace_items WHERE item_id = :id"),
        {"id": item_id},
    ).first()
    return {"saved": True, "saves_count": row[0] if row else None}


@router.delete("/items/{item_id}/save")
def unsave_item(
    item_id: int,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = _current_user(authorization)

    was_saved = bool(_redis.sismember(f"wishlist:{user_id}", item_id))
    if not was_saved:
        return {"saved": False}

    _redis.srem(f"wishlist:{user_id}", item_id)

    db.execute(text(
        "DELETE FROM item_saved WHERE user_id = :uid AND item_id = :iid"
    ), {"uid": user_id, "iid": item_id})
    db.execute(text("""
        UPDATE marketplace_items
        SET saves_count = GREATEST(saves_count - 1, 0)
        WHERE item_id = :id
    """), {"id": item_id})
    db.commit()

    row = db.execute(
        text("SELECT saves_count FROM marketplace_items WHERE item_id = :id"),
        {"id": item_id},
    ).first()
    return {"saved": False, "saves_count": row[0] if row else None}


@router.get("/users/me/saved")
def get_saved_items(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = _current_user(authorization)

    # Pull saved item IDs from Redis; fall back to DB if cache is cold
    redis_ids = _redis.smembers(f"wishlist:{user_id}")
    if redis_ids:
        item_ids = [int(x) for x in redis_ids]
    else:
        rows = db.execute(
            text("SELECT item_id FROM item_saved WHERE user_id = :uid"),
            {"uid": user_id},
        ).fetchall()
        item_ids = [r[0] for r in rows]
        if item_ids:
            _redis.sadd(f"wishlist:{user_id}", *item_ids)

    if not item_ids:
        return {"items": []}

    placeholders = ", ".join(str(i) for i in item_ids)
    rows = db.execute(text(f"""
        SELECT i.item_id, i.title, i.price, i.category, i.condition,
               i.city, i.state, i.views_count, i.saves_count, i.created_at,
               img.image_url
        FROM marketplace_items i
        LEFT JOIN item_images img ON i.item_id = img.item_id AND img.is_thumbnail = true
        WHERE i.item_id IN ({placeholders}) AND i.is_active = true
    """)).fetchall()

    return {
        "items": [
            {
                "item_id": r[0], "title": r[1], "price": float(r[2]),
                "category": r[3], "condition": r[4], "city": r[5],
                "state": r[6], "views_count": r[7], "saves_count": r[8],
                "created_at": str(r[9]), "thumbnail": r[10],
            }
            for r in rows
        ]
    }
