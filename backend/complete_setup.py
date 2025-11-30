#!/usr/bin/env python3
import os, random
from datetime import datetime
from faker import Faker
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

fake = Faker('en_US')

DB_HOST = os.getenv("DB_HOST", "localhost")
DATABASE_URL = f"postgresql://postgres:password@{DB_HOST}:5432/electrohub"

PRODUCT_CATEGORIES = {
    "Electronics": ["iPhone 15 Pro", "Samsung Galaxy S24", "MacBook Pro M3", "iPad Air", "Sony WH-1000XM5", "Apple Watch Series 9", "DJI Mini 4 Pro", "Canon EOS R6", "Samsung OLED TV 55\"", "Dell XPS 15", "Google Pixel 8", "AirPods Pro 2", "Beats Studio 4", "OnePlus 12", "Gaming Monitor 4K"],
    "Furniture": ["Modern Sofa Set", "Dining Table", "Queen Bed Frame", "Office Desk", "Bookshelf", "Coffee Table", "Gaming Chair", "Recliner", "TV Stand", "Nightstand"],
    "Vehicles": ["2020 Honda Civic", "2019 Toyota Camry", "2021 Tesla Model 3", "Mountain Bike", "Electric Scooter", "Road Bike", "BMX Bike", "Skateboard"],
    "Home & Garden": ["Lawn Mower", "Garden Tools", "BBQ Grill", "Patio Furniture", "Air Purifier", "Pressure Washer", "Leaf Blower"],
    "Fashion": ["Nike Air Max", "Adidas Ultraboost", "Winter Jacket", "Designer Handbag", "Leather Backpack", "Business Suit"],
    "Books & Media": ["Harry Potter Series", "The Great Gatsby", "Python Book", "4K Blu-ray Player", "Vinyl Records", "Photography Book"]
}

LOCATIONS = [("Denver", "CO"), ("Boulder", "CO"), ("NYC", "NY"), ("LA", "CA"), ("Chicago", "IL"), ("Houston", "TX"), ("Phoenix", "AZ"), ("Philly", "PA"), ("SF", "CA"), ("Seattle", "WA"), ("Boston", "MA"), ("Miami", "FL")]
CONDITIONS = ["brand new", "like new", "excellent", "good"]

print("\n" + "="*60)
print("🚀 COMPLETE ELECTROHUB SETUP")
print("="*60 + "\n")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

try:
    print("📋 Creating tables...")
    
    sqls = [
        """CREATE TABLE IF NOT EXISTS user_accounts (
            account_id SERIAL PRIMARY KEY, user_id VARCHAR(255) UNIQUE NOT NULL, email VARCHAR(255) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, name VARCHAR(255) NOT NULL, phone VARCHAR(50), 
            profile_picture TEXT DEFAULT 'https://ui-avatars.com/api/?name=User&size=200',
            bio TEXT, city VARCHAR(100), state VARCHAR(100), zip_code INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_login TIMESTAMP, is_active BOOLEAN DEFAULT true)""",
        
        """CREATE TABLE IF NOT EXISTS marketplace_items (
            item_id SERIAL PRIMARY KEY, seller_id VARCHAR(255) NOT NULL, title VARCHAR(255) NOT NULL,
            description TEXT, category VARCHAR(100), price DECIMAL(10,2), city VARCHAR(100), state VARCHAR(100),
            zip_code INT, condition VARCHAR(50), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT true, FOREIGN KEY (seller_id) REFERENCES user_accounts(user_id))""",
        
        """CREATE TABLE IF NOT EXISTS item_images (
            image_id SERIAL PRIMARY KEY, item_id INT NOT NULL, image_url TEXT NOT NULL,
            is_thumbnail BOOLEAN DEFAULT false, FOREIGN KEY (item_id) REFERENCES marketplace_items(item_id))""",
        
        """CREATE TABLE IF NOT EXISTS item_interactions (
            interaction_id BIGSERIAL PRIMARY KEY, user_id VARCHAR(255) NOT NULL, item_id INT NOT NULL,
            event_type VARCHAR(20), event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_accounts(user_id),
            FOREIGN KEY (item_id) REFERENCES marketplace_items(item_id))""",
        
        """CREATE TABLE IF NOT EXISTS item_saved (
            save_id SERIAL PRIMARY KEY, user_id VARCHAR(255) NOT NULL, item_id INT NOT NULL,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_accounts(user_id),
            FOREIGN KEY (item_id) REFERENCES marketplace_items(item_id))""",
        
        """CREATE TABLE IF NOT EXISTS marketplace_messages (
            message_id BIGSERIAL PRIMARY KEY, sender_id VARCHAR(255), receiver_id VARCHAR(255),
            item_id INT, message_text TEXT, sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
    ]
    
    for sql in sqls:
        session.execute(text(sql))
    session.commit()
    print("✅ Tables created!")
    
    print("\n👥 Generating 500 users...")
    demo_check = session.execute(text("SELECT COUNT(*) FROM user_accounts WHERE email='demo@electrohub.com'")).scalar()
    if demo_check == 0:
        session.execute(text(
            "INSERT INTO user_accounts (user_id, email, password_hash, name, city, state, zip_code, is_active) VALUES ('user_demo_001', 'demo@electrohub.com', 'password123', 'Demo User', 'Denver', 'CO', 80202, true)"
        ))
    
    for i in range(2, 501):
        uid = f"user_{i:06d}"
        city, state = random.choice(LOCATIONS)
        session.execute(text(
            "INSERT INTO user_accounts (user_id, email, password_hash, name, city, state, is_active) VALUES (:uid, :email, :password, :name, :city, :state, true) ON CONFLICT DO NOTHING"
        ), {"uid": uid, "email": f"{uid}@example.com", "password": "password123", "name": fake.name(), "city": city, "state": state})
        if i % 100 == 0:
            session.commit()
            print(f"  {i}/500 users...")
    session.commit()
    print("✅ 500 users created!")
    
    users = session.execute(text("SELECT user_id FROM user_accounts")).fetchall()
    user_ids = [r[0] for r in users]
    
    print("\n📦 Generating 1000 items...")
    for i in range(1, 1001):
        cat = random.choice(list(PRODUCT_CATEGORIES.keys()))
        prod = random.choice(PRODUCT_CATEGORIES[cat])
        seller = random.choice(user_ids)
        city, state = random.choice(LOCATIONS)
        price = round(random.uniform(20, 5000), 2)
        cond = random.choice(CONDITIONS)
        
        session.execute(text(
            "INSERT INTO marketplace_items (seller_id, title, description, category, price, city, state, condition, is_active) VALUES (:sid, :title, :desc, :cat, :price, :city, :state, :cond, true)"
        ), {"sid": seller, "title": f"{prod} - {cond.title()}", "desc": f"{prod} in {cond} condition", "cat": cat, "price": price, "city": city, "state": state, "cond": cond})
        
        if i % 100 == 0:
            session.commit()
            print(f"  {i}/1000 items...")
    session.commit()
    print("✅ 1000 items created!")
    
    print("\n🖼️  Generating 3000+ images...")
    items = session.execute(text("SELECT item_id FROM marketplace_items")).fetchall()
    img_count = 0
    for item_id in items:
        for j in range(1, random.randint(2, 4)):
            session.execute(text("INSERT INTO item_images (item_id, image_url, is_thumbnail) VALUES (:iid, :url, :thumb)"),
                {"iid": item_id[0], "url": f"https://picsum.photos/400/300?random={item_id[0]}_{j}", "thumb": j==1})
            img_count += 1
            if img_count % 1000 == 0:
                session.commit()
                print(f"  {img_count} images...")
    session.commit()
    print(f"✅ {img_count} images created!")
    
    print("\n👀 Generating 5000+ interactions...")
    items = [r[0] for r in session.execute(text("SELECT item_id FROM marketplace_items")).fetchall()]
    for i in range(1, 5001):
        user = random.choice(user_ids)
        item = random.choice(items)
        event = random.choices(['view', 'save', 'message'], weights=[0.7, 0.2, 0.1], k=1)[0]
        session.execute(text("INSERT INTO item_interactions (user_id, item_id, event_type) VALUES (:uid, :iid, :event)"),
            {"uid": user, "iid": item, "event": event})
        if i % 1000 == 0:
            session.commit()
            print(f"  {i}/5000 interactions...")
    session.commit()
    print("✅ 5000+ interactions created!")
    
    u_count = session.execute(text("SELECT COUNT(*) FROM user_accounts")).scalar()
    i_count = session.execute(text("SELECT COUNT(*) FROM marketplace_items")).scalar()
    img_count = session.execute(text("SELECT COUNT(*) FROM item_images")).scalar()
    inter_count = session.execute(text("SELECT COUNT(*) FROM item_interactions")).scalar()
    
    print("\n" + "="*60)
    print("✅ COMPLETE SETUP FINISHED!")
    print("="*60)
    print(f"👥 Users: {u_count}")
    print(f"📦 Items: {i_count}")
    print(f"🖼️  Images: {img_count}")
    print(f"👀 Interactions: {inter_count}")
    print("\n🔑 Demo Login: demo@electrohub.com / password123")
    print("="*60 + "\n")
    
    session.close()

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
