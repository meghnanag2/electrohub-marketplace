from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import UserActivity, Marketplace


class ActivityService:
    """
    Service helpers for writing and reading user activity.

    This is intentionally thin so it can be reused both by API routes and
    internal services (e.g., contact / save item flows).
    """

    @staticmethod
    def log_activity(
        db: Session,
        *,
        user_id: str,
        activity_type: str,
        action: Optional[str] = None,
        item_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserActivity:
        """
        Insert a single row into user_activity.

        Parameters largely mirror the table columns; `metadata` will be stored
        as a JSON string for flexibility.
        """
        activity = UserActivity(
            user_id=user_id,
            item_id=item_id,
            activity_type=activity_type,
            action=action or activity_type,
            activity_metadata=json.dumps(metadata) if metadata else None,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
        )

        db.add(activity)
        db.commit()
        db.refresh(activity)
        return activity

    @staticmethod
    def get_recent_activity(
        db: Session,
        *,
        user_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Return the most recent activity for a given user.

        We join to `marketplace_items` when an item_id is present so the UI
        can show human-friendly context like the item title and price.
        """
        query = (
            db.query(UserActivity, Marketplace)
            .outerjoin(Marketplace, UserActivity.item_id == Marketplace.item_id)
            .filter(UserActivity.user_id == user_id)
            .order_by(desc(UserActivity.created_at))
            .limit(limit)
        )

        results: List[Dict[str, Any]] = []
        for activity, item in query:
            results.append(
                {
                    "activity_id": activity.activity_id,
                    "user_id": activity.user_id,
                    "item_id": activity.item_id,
                    "activity_type": activity.activity_type,
                    "action": activity.action,
                    "metadata": json.loads(activity.activity_metadata)
                    if activity.activity_metadata
                    else None,
                    "session_id": activity.session_id,
                    "ip_address": activity.ip_address,
                    "user_agent": activity.user_agent,
                    "created_at": activity.created_at.isoformat()
                    if activity.created_at
                    else None,
                    "item": {
                        "item_id": item.item_id,
                        "title": item.title,
                        "price": float(item.price)
                        if getattr(item, "price", None) is not None
                        else None,
                        "city": item.city,
                        "state": item.state,
                        "category": item.category,
                    }
                    if item
                    else None,
                }
            )

        return results
