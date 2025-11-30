# backend/app/api/marketplace.py

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


@router.get("/items")
def get_marketplace_items(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
):
    """
    List marketplace items with filters + pagination, shaped to match the React UI.
    """

    where_clauses = ["mi.is_active = TRUE"]
    params: dict = {}

    if category:
        where_clauses.append("mi.category = :category")
        params["category"] = category
    if city:
        where_clauses.append("mi.city = :city")
        params["city"] = city
    if state:
        where_clauses.append("mi.state = :state")
        params["state"] = state
    if search:
        where_clauses.append(
            "(LOWER(mi.title) LIKE :search OR LOWER(mi.description) LIKE :search)"
        )
        params["search"] = f"%{search.lower()}%"
    if min_price is not None:
        where_clauses.append("mi.price >= :min_price")
        params["min_price"] = min_price
    if max_price is not None:
        where_clauses.append("mi.price <= :max_price")
        params["max_price"] = max_price

    where_sql = " AND ".join(where_clauses)

    # Total count for pagination
    count_sql = text(
        f"SELECT COUNT(*) FROM marketplace_items mi WHERE {where_sql}"
    )
    total = db.execute(count_sql, params).scalar() or 0

    # Actual items
    items_sql = text(
        f"""
        SELECT
            mi.item_id,
            mi.title,
            mi.description,
            mi.category,
            mi.price,
            mi.city,
            mi.state,
            mi.seller_id,
            ua.name  AS seller_name,
            ua.city  AS seller_city,
            ua.state AS seller_state,
            (
                SELECT image_url
                FROM marketplace_images img
                WHERE img.item_id = mi.item_id
                ORDER BY img.is_thumbnail DESC,
                         img.upload_order ASC,
                         img.image_id ASC
                LIMIT 1
            ) AS image_url
        FROM marketplace_items mi
        LEFT JOIN user_accounts ua
            ON ua.user_id = mi.seller_id
        WHERE {where_sql}
        ORDER BY mi.created_at DESC
        OFFSET :skip
        LIMIT :limit
        """
    )

    params_with_paging = dict(params)
    params_with_paging["skip"] = skip
    params_with_paging["limit"] = limit

    rows = db.execute(items_sql, params_with_paging).mappings().all()

    items = []
    for row in rows:
        items.append(
            {
                "item_id": row["item_id"],
                "title": row["title"],
                "description": row["description"],
                "category": row["category"],
                "price": float(row["price"]) if row["price"] is not None else None,
                "city": row["city"],
                "state": row["state"],
                "seller": (
                    {
                        "user_id": row["seller_id"],
                        "name": row["seller_name"],
                        "city": row["seller_city"],
                        "state": row["seller_state"],
                    }
                    if row["seller_id"] is not None
                    else None
                ),
                "images": (
                    [{"image_url": row["image_url"]}]
                    if row["image_url"]
                    else []
                ),
            }
        )

    return {"total": total, "items": items}


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """
    Return categories and counts for the sidebar filter.
    """
    sql = text(
        """
        SELECT category, COUNT(*) AS count
        FROM marketplace_items
        WHERE is_active = TRUE
        GROUP BY category
        ORDER BY count DESC
        """
    )
    rows = db.execute(sql).all()
    return {"categories": [{"name": r[0], "count": r[1]} for r in rows]}


@router.get("/locations")
def get_locations(db: Session = Depends(get_db)):
    """
    Distinct (city, state) for location filters.
    """
    sql = text(
        """
        SELECT DISTINCT city, state
        FROM marketplace_items
        WHERE is_active = TRUE
        ORDER BY city, state
        """
    )
    rows = db.execute(sql).all()
    return {"locations": [{"city": r[0], "state": r[1]} for r in rows]}
