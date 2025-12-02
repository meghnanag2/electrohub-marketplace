from fastapi import APIRouter, Depends
from app.api import auth
from app.api import marketplace
from app.api import contact_save_items
from app.api import activity

router = APIRouter()
router.include_router(auth.router)
router.include_router(marketplace.router)
router.include_router(contact_save_items.router)
router.include_router(activity.router)
