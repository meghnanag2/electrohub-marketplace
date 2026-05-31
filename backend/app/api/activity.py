from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import User
from app.services.activity_service import ActivityService

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("/")
def get_my_activity(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activities = ActivityService.get_recent_activity(
        db, user_id=current_user.user_id, limit=limit
    )
    return {"activities": activities}
