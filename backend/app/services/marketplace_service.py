from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import Marketplace, ItemImage
import logging

logger = logging.getLogger(__name__)

class MarketplaceService:
    @staticmethod
    def create_item(db: Session, seller_id, title, description, category, price, city, state, zip_code=None, condition="new", images=None):
        item = Marketplace(
            seller_id=seller_id,
            title=title,
            description=description,
            category=category,
            price=price,
            city=city,
            state=state,
            zip_code=zip_code,
            condition=condition,
            is_active=True
        )
        db.add(item)
        db.flush()
        
        if images:
            for idx, img in enumerate(images):
                image = ItemImage(
                    item_id=item.item_id,
                    image_url=img.get('image_url'),
                    is_thumbnail=idx == 0,
                    upload_order=idx
                )
                db.add(image)
        
        db.commit()
        db.refresh(item)
        logger.info(f"✅ Item created: {title}")
        return item
    
    @staticmethod
    def get_item_by_id(db: Session, item_id: int):
        return db.query(Marketplace).filter(Marketplace.item_id == item_id).first()
    
    @staticmethod
    def update_item(db: Session, item_id: int, seller_id: str, **kwargs):
        item = db.query(Marketplace).filter(
            Marketplace.item_id == item_id,
            Marketplace.seller_id == seller_id
        ).first()
        
        if not item:
            return None
        
        for key, value in kwargs.items():
            if value is not None:
                setattr(item, key, value)
        
        db.commit()
        db.refresh(item)
        return item
    
    @staticmethod
    def delete_item(db: Session, item_id: int, seller_id: str):
        item = db.query(Marketplace).filter(
            Marketplace.item_id == item_id,
            Marketplace.seller_id == seller_id
        ).first()
        
        if not item:
            return False
        
        db.delete(item)
        db.commit()
        return True
    
    @staticmethod
    def list_items(db: Session, skip=0, limit=20, category=None, city=None, state=None, search=None, min_price=None, max_price=None):
        query = db.query(Marketplace).filter(Marketplace.is_active == True)
        
        if category:
            query = query.filter(Marketplace.category == category)
        if city:
            query = query.filter(Marketplace.city == city)
        if state:
            query = query.filter(Marketplace.state == state)
        if min_price is not None:
            query = query.filter(Marketplace.price >= min_price)
        if max_price is not None:
            query = query.filter(Marketplace.price <= max_price)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Marketplace.title.ilike(search_term)) |
                (Marketplace.description.ilike(search_term))
            )
        
        total = query.count()
        items = query.order_by(Marketplace.created_at.desc()).offset(skip).limit(limit).all()
        return total, items
    
    @staticmethod
    def get_categories(db: Session):
        result = db.execute(text("SELECT category, COUNT(*) as count FROM marketplace_items WHERE is_active = true GROUP BY category ORDER BY count DESC")).fetchall()
        return [{"name": row[0], "count": row[1]} for row in result]
    
    @staticmethod
    def get_locations(db: Session):
        result = db.execute(text("SELECT DISTINCT city, state FROM marketplace_items WHERE is_active = true ORDER BY city")).fetchall()
        return [{"city": row[0], "state": row[1]} for row in result]
    
    @staticmethod
    def increment_views(db: Session, item_id: int):
        db.execute(text("UPDATE marketplace_items SET views_count = views_count + 1 WHERE item_id = :iid"), {"iid": item_id})
        db.commit()
