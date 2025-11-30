#!/usr/bin/env python3
import os, random
from datetime import datetime
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

fake = Faker('en_US')
DB_HOST = os.getenv("DB_HOST", "localhost")
DATABASE_URL = f"postgresql://postgres:password@{DB_HOST}:5432/electrohub"

CATEGORIES = {"Electronics": ["iPhone 15", "Samsung Galaxy S24", "MacBook Pro", "iPad"], "Furniture": ["Sofa", "Table", "Bed"], "Vehicles": ["Honda Civic", "Toyota Camry"], "Home": ["Grill", "Tools"]}
US_LOCATIONS = [("Denver", "CO"), ("Boulder", "CO"), ("New York", "NY"), ("Los Angeles", "CA")]

def main():
    print("\n🚀 GENERATING MARKETPLACE DATA...\n")
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        users_result = session.execute("SELECT user_id FROM user_accounts")
        user_ids = [row[0] for row in users_result]
        if not user_ids:
            print("❌ No users found!")
            return
        
        print(f"📦 Generating 1000 items...")
        for i in range(1000):
            category = random.choice(list(CATEGORIES.keys()))
            product = random.choice(CATEGORIES[category])
            seller_id = random.choice(user_ids)
            city, state = random.choice(US_LOCATIONS)
            price = round(random.uniform(20, 5000), 2)
            
            sql = "INSERT INTO marketplace_items (seller_id, title, description, category, price, city, state, created_at, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            session.execute(sql, (seller_id, f"{product} - Item {i}", f"Nice {product}", category, price, city, state, datetime.now(), True))
            
            if (i+1) % 100 == 0:
                session.commit()
                print(f"  {i+1}/1000 created...")
        
        session.commit()
        print("✅ 1000 items created!")
        
        print(f"🖼️  Generating images...")
        items = session.execute("SELECT item_id FROM marketplace_items ORDER BY item_id DESC LIMIT 1000")
        for item_id in items:
            for j in range(2):
                sql = "INSERT INTO item_images (item_id, image_url, is_thumbnail) VALUES (%s, %s, %s)"
                session.execute(sql, (item_id[0], f"https://picsum.photos/400/300?random={item_id[0]}_{j}", j==0))
        session.commit()
        print("✅ Images created!")
        
        print("\n✅ DATA GENERATION COMPLETE!\n")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
