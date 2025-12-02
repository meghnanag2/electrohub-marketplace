#!/usr/bin/env python3
"""
Generate synthetic marketplace data
"""
import psycopg2
import hashlib
import random
import os
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('en_US')

DB_CONFIG = {
    'host': '127.0.0.1',
    'database': 'electrohub',
    'user': 'postgres',
    'password': os.getenv('DB_PASSWORD', 'password'),
    'port': 5432
}


CATEGORIES = {
    'Electronics': {
        'items': ['iPhone 14 Pro', 'Samsung Galaxy S23', 'MacBook Air M2', 'Dell XPS 15', 
                  'Sony WH-1000XM5', 'iPad Pro', 'AirPods Pro', 'Canon EOS R6'],
        'image': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400'
    },
    'Furniture': {
        'items': ['Modern Sofa', 'Dining Table Set', 'Office Chair', 'Queen Bed Frame', 
                  'Bookshelf', 'Coffee Table'],
        'image': 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400'
    },
    'Vehicles': {
        'items': ['2020 Honda Civic', '2019 Toyota Camry', '2021 Tesla Model 3', 
                  'Mountain Bike', 'Electric Scooter'],
        'image': 'https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=400'
    },
    'Home & Garden': {
        'items': ['Lawn Mower', 'Garden Tools Set', 'BBQ Grill', 'Patio Furniture'],
        'image': 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=400'
    }
}

US_LOCATIONS = [
    ('Denver', 'CO', 80202), ('Boulder', 'CO', 80301), ('Aurora', 'CO', 80010),
    ('New York', 'NY', 10001), ('Los Angeles', 'CA', 90001), ('Chicago', 'IL', 60601),
    ('Houston', 'TX', 77001), ('Phoenix', 'AZ', 85001), ('Philadelphia', 'PA', 19019)
]

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_users(conn, count=100):
    """Create user accounts"""
    cursor = conn.cursor()
    print(f"👥 Creating {count} users...")
    
    users = []
    # Create demo user first
    users.append((
        'user_demo_001',
        'demo@electrohub.com',
        hash_password('password123'),
        'Demo User',
        '555-0100',
        'https://ui-avatars.com/api/?name=Demo+User&size=200',
        'Demo account for testing ElectroHub Marketplace',
        'Denver', 'CO', 80202, True
    ))
    
    # Create random users
    for i in range(1, count):
        user_id = f"user_{i+1:06d}"
        name = fake.name()
        email = f"user{i+1}@example.com"
        password_hash = hash_password('password123')
        phone = fake.phone_number()[:15]
        city, state, zip_code = random.choice(US_LOCATIONS)
        is_verified = random.choice([True, False])
        
        users.append((
            user_id, email, password_hash, name, phone,
            f'https://ui-avatars.com/api/?name={name.replace(" ", "+")}&size=200',
            fake.sentence() if random.random() > 0.5 else None,
            city, state, zip_code, is_verified
        ))
    
    cursor.executemany("""
        INSERT INTO user_accounts 
        (user_id, email, password_hash, name, phone, profile_picture, bio, 
         city, state, zip_code, is_verified)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (email) DO NOTHING
    """, users)
    
    conn.commit()
    print(f"✅ Created {cursor.rowcount} users")
    cursor.close()
    return [u[0] for u in users]

def create_items(conn, user_ids, count=500):
    """Create marketplace items"""
    cursor = conn.cursor()
    print(f"📦 Creating {count} items...")
    
    items = []
    for i in range(count):
        seller_id = random.choice(user_ids)
        category = random.choice(list(CATEGORIES.keys()))
        item_name = random.choice(CATEGORIES[category]['items'])
        
        title = f"{item_name} - {random.choice(['Like New', 'Excellent', 'Good', 'Brand New'])}"
        description = fake.paragraph(nb_sentences=3)
        price = round(random.uniform(20, 2000), 2)
        city, state, zip_code = random.choice(US_LOCATIONS)
        condition = random.choice(['new', 'like new', 'good', 'fair'])
        views = random.randint(0, 500)
        saves = random.randint(0, 50)
        created_at = datetime.now() - timedelta(days=random.randint(1, 90))
        
        items.append((
            seller_id, title, description, category, price,
            city, state, zip_code, condition, views, saves, created_at
        ))
    
    cursor.executemany("""
        INSERT INTO marketplace_items 
        (seller_id, title, description, category, price, city, state, zip_code, 
         condition, views_count, saves_count, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, items)
    
    conn.commit()
    print(f"✅ Created {cursor.rowcount} items")
    
    # Add images for items
    cursor.execute("SELECT item_id, category FROM marketplace_items")
    items_with_category = cursor.fetchall()
    
    images = []
    for item_id, category in items_with_category:
        image_url = CATEGORIES.get(category, {}).get('image', 
                    'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400')
        images.append((item_id, image_url, True, 0))
    
    cursor.executemany("""
        INSERT INTO item_images (item_id, image_url, is_thumbnail, upload_order)
        VALUES (%s, %s, %s, %s)
    """, images)
    
    conn.commit()
    print(f"✅ Added {cursor.rowcount} images")
    cursor.close()

def create_interactions(conn, user_ids, count=2000):
    """Create user interactions"""
    cursor = conn.cursor()
    print(f"🔄 Creating {count} interactions...")
    
    cursor.execute("SELECT item_id FROM marketplace_items")
    item_ids = [row[0] for row in cursor.fetchall()]
    
    interactions = []
    for _ in range(count):
        user_id = random.choice(user_ids)
        item_id = random.choice(item_ids)
        event_type = random.choice(['view', 'view', 'view', 'save', 'click'])
        event_time = datetime.now() - timedelta(days=random.randint(0, 30))
        session_id = f"session_{random.randint(1, 500):06d}"
        
        interactions.append((user_id, item_id, event_type, event_time, session_id))
    
    cursor.executemany("""
        INSERT INTO item_interactions (user_id, item_id, event_type, event_time, session_id)
        VALUES (%s, %s, %s, %s, %s)
    """, interactions)
    
    conn.commit()
    print(f"✅ Created {cursor.rowcount} interactions")
    cursor.close()

def main():
    print("🚀 Starting data generation...\n")
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    # Create users
    user_ids = create_users(conn, 100)
    
    # Create items
    create_items(conn, user_ids, 500)
    
    # Create interactions
    create_interactions(conn, user_ids, 2000)
    
    conn.close()
    
    print("\n" + "="*50)
    print("✅ DATA GENERATION COMPLETE!")
    print("="*50)
    print("\n🔐 Demo Credentials:")
    print("   Email: demo@electrohub.com")
    print("   Password: password123")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
