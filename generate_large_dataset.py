#!/usr/bin/env python3
import os, sys, random, bcrypt, psycopg2
from psycopg2.extras import execute_batch

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_NAME = os.getenv('DB_NAME', 'electrohub')

NUM_USERS = 200
NUM_PRODUCTS = 500
NUM_INTERACTIONS = 10000
NUM_MESSAGES = 500
NUM_SAVED_ITEMS = 1000

CATEGORIES = ["Smartphone", "Laptop", "Tablet", "Smartwatch", "Headphones", "Camera", "Drone", "Gaming", "Audio", "Accessories"]
PRODUCTS = {
    "Smartphone": ["iPhone 14 Pro", "iPhone 13", "Samsung Galaxy S24", "Google Pixel 8", "OnePlus 12"],
    "Laptop": ["MacBook Pro 16", "MacBook Air M2", "Dell XPS 13", "HP Spectre x360", "Lenovo ThinkPad X1"],
    "Tablet": ["iPad Pro", "iPad Air", "Samsung Galaxy Tab S9", "Microsoft Surface Go"],
    "Smartwatch": ["Apple Watch 9", "Fitbit Versa 4", "Samsung Galaxy Watch", "Garmin Fenix 7"],
    "Headphones": ["Bose QC45", "AirPods Pro 2", "Sony WH-1000XM5", "Beats Studio Pro"],
    "Camera": ["Canon EOS R5", "Nikon Z9", "Sony A7 IV", "GoPro Hero 12"],
    "Drone": ["DJI Air 3S", "DJI Mini 4", "Autel EVO II"],
    "Gaming": ["PlayStation 5", "Xbox Series X", "Nintendo Switch OLED", "Steam Deck"],
    "Audio": ["JBL Charge 5", "UE Boom 3", "Marshall Stanmore III"],
    "Accessories": ["MagSafe Charger", "USB-C Hub", "Phone Stand", "Laptop Bag"]
}
CITIES = ["Denver", "Boulder", "Aurora", "Fort Collins", "Lakewood", "Littleton", "Thornton", "Broomfield", "Westminster", "Arvada"]
CONDITIONS = ["brand new", "like new", "excellent", "very good", "good"]

def hash_password(password):
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def generate_users(num_users):
    users = []
    first_names = ["John", "Sarah", "Mike", "Emma", "David", "Lisa", "James", "Jennifer", "Robert", "Mary", "William", "Patricia", "Richard", "Barbara"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    
    demo_users = [
        ("user_demo_001", "demo@electrohub.com", "password123"),
        ("user_demo_002", "seller@electrohub.com", "seller123"),
        ("user_demo_003", "buyer@electrohub.com", "buyer123"),
        ("user_demo_004", "alice@electrohub.com", "alice123"),
        ("user_demo_005", "bob@electrohub.com", "bob123"),
    ]
    
    for user_id, email, password in demo_users:
        users.append({
            'user_id': user_id,
            'email': email,
            'password_hash': hash_password(password),
            'name': email.split('@')[0],
            'phone': f'555-{random.randint(1000, 9999)}',
            'city': random.choice(CITIES),
            'state': 'CO',
            'is_active': True
        })
    
    for i in range(1, num_users - 4):
        first = random.choice(first_names)
        last = random.choice(last_names)
        user_id = f"user_{i:06d}"
        email = f"{first.lower()}.{last.lower()}@example.com"
        password = f"{first.lower()}_{i}"
        
        users.append({
            'user_id': user_id,
            'email': email,
            'password_hash': hash_password(password),
            'name': f"{first} {last}",
            'phone': f'555-{random.randint(1000, 9999)}',
            'city': random.choice(CITIES),
            'state': 'CO',
            'is_active': True
        })
    
    return users

def generate_products(num_products, num_users):
    products = []
    for i in range(1, num_products + 1):
        category = random.choice(CATEGORIES)
        product_name = random.choice(PRODUCTS[category])
        seller_idx = random.randint(1, num_users - 1)
        seller_id = f"user_demo_{seller_idx:03d}" if seller_idx < 5 else f"user_{seller_idx:06d}"
        condition = random.choice(CONDITIONS)
        price = round(random.uniform(50, 3000), 2)
        
        products.append({
            'seller_id': seller_id,
            'title': f"{product_name} - {condition.title()}",
            'description': f"{product_name} in {condition} condition. Available now!",
            'category': category,
            'price': price,
            'city': random.choice(CITIES),
            'state': 'CO',
            'condition': condition,
            'views_count': random.randint(0, 500),
            'saves_count': random.randint(0, 100),
            'is_active': True
        })
    return products

def generate_messages(num_messages, num_users, num_products):
    messages = []
    sample_texts = ["Hi, is this still available?", "What's the lowest you'll go?", "Can you ship this?", "Interested! When can we meet?", "Does it have all accessories?", "Great condition!", "Can you provide details?", "Is this negotiable?"]
    
    for _ in range(num_messages):
        sender_idx = random.randint(1, num_users - 1)
        receiver_idx = random.randint(1, num_users - 1)
        sender_id = f"user_demo_{sender_idx:03d}" if sender_idx < 5 else f"user_{sender_idx:06d}"
        receiver_id = f"user_demo_{receiver_idx:03d}" if receiver_idx < 5 else f"user_{receiver_idx:06d}"
        
        if sender_id == receiver_id:
            continue
        
        messages.append({
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'item_id': random.randint(1, num_products),
            'message_text': random.choice(sample_texts),
            'is_read': random.choice([True, False, False])
        })
    return messages

def generate_interactions(num_interactions, num_users, num_products):
    interactions = []
    event_types = ["view", "save", "message"]
    weights = [0.7, 0.2, 0.1]
    
    for _ in range(num_interactions):
        user_idx = random.randint(1, num_users - 1)
        user_id = f"user_demo_{user_idx:03d}" if user_idx < 5 else f"user_{user_idx:06d}"
        item_id = random.randint(1, num_products)
        event_type = random.choices(event_types, weights=weights)[0]
        
        interactions.append({
            'user_id': user_id,
            'item_id': item_id,
            'event_type': event_type
        })
    return interactions

def generate_saved_items(num_saved, num_users, num_products):
    saved = []
    for _ in range(num_saved):
        user_idx = random.randint(1, num_users - 1)
        user_id = f"user_demo_{user_idx:03d}" if user_idx < 5 else f"user_{user_idx:06d}"
        item_id = random.randint(1, num_products)
        saved.append({'user_id': user_id, 'item_id': item_id})
    return saved

def insert_data():
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        cursor = conn.cursor()
        
        print("🌱 Generating data...")
        print(f"  📝 {NUM_USERS} users...")
        users = generate_users(NUM_USERS)
        print(f"  🛍️  {NUM_PRODUCTS} products...")
        products = generate_products(NUM_PRODUCTS, NUM_USERS)
        print(f"  💬 {NUM_MESSAGES} messages...")
        messages = generate_messages(NUM_MESSAGES, NUM_USERS, NUM_PRODUCTS)
        print(f"  👀 {NUM_INTERACTIONS} interactions...")
        interactions = generate_interactions(NUM_INTERACTIONS, NUM_USERS, NUM_PRODUCTS)
        print(f"  ⭐ {NUM_SAVED_ITEMS} saved items...")
        saved_items = generate_saved_items(NUM_SAVED_ITEMS, NUM_USERS, NUM_PRODUCTS)
        
        print("\n💾 Inserting users...")
        user_query = "INSERT INTO user_accounts (user_id, email, password_hash, name, phone, city, state, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (email) DO NOTHING"
        user_data = [(u['user_id'], u['email'], u['password_hash'], u['name'], u['phone'], u['city'], u['state'], u['is_active']) for u in users]
        execute_batch(cursor, user_query, user_data)
        conn.commit()
        print(f"   ✅ {len(users)} users inserted")
        
        print("💾 Inserting products...")
        product_query = "INSERT INTO marketplace_items (seller_id, title, description, category, price, city, state, condition, views_count, saves_count, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"
        product_data = [(p['seller_id'], p['title'], p['description'], p['category'], p['price'], p['city'], p['state'], p['condition'], p['views_count'], p['saves_count'], p['is_active']) for p in products]
        execute_batch(cursor, product_query, product_data, page_size=100)
        conn.commit()
        print(f"   ✅ {len(products)} products inserted")
        
        print("💾 Inserting messages...")
        message_query = "INSERT INTO marketplace_messages (sender_id, receiver_id, item_id, message_text, is_read) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"
        message_data = [(m['sender_id'], m['receiver_id'], m['item_id'], m['message_text'], m['is_read']) for m in messages]
        execute_batch(cursor, message_query, message_data, page_size=100)
        conn.commit()
        print(f"   ✅ {len(messages)} messages inserted")
        
        print("💾 Inserting interactions...")
        interaction_query = "INSERT INTO item_interactions (user_id, item_id, event_type) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING"
        interaction_data = [(i['user_id'], i['item_id'], i['event_type']) for i in interactions]
        execute_batch(cursor, interaction_query, interaction_data, page_size=1000)
        conn.commit()
        print(f"   ✅ {len(interactions)} interactions inserted")
        
        print("💾 Inserting saved items...")
        saved_query = "INSERT INTO item_saved (user_id, item_id) VALUES (%s, %s) ON CONFLICT DO NOTHING"
        saved_data = [(s['user_id'], s['item_id']) for s in saved_items]
        execute_batch(cursor, saved_query, saved_data, page_size=500)
        conn.commit()
        print(f"   ✅ {len(saved_items)} saved items inserted")
        
        print("\n" + "="*60)
        print("✅ DATABASE SEEDING COMPLETE!")
        print("="*60)
        
        cursor.execute("SELECT COUNT(*) FROM user_accounts")
        user_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM marketplace_items")
        product_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM marketplace_messages")
        message_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM item_interactions")
        interaction_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM item_saved")
        saved_count = cursor.fetchone()[0]
        
        print(f"\n📊 Database Stats:")
        print(f"   👥 Users:        {user_count}")
        print(f"   🛍️  Products:     {product_count}")
        print(f"   �� Messages:     {message_count}")
        print(f"   👀 Interactions: {interaction_count}")
        print(f"   ⭐ Saved Items:  {saved_count}")
        
        print(f"\n🔑 Demo Logins (all work with UI):")
        print(f"   demo@electrohub.com / password123")
        print(f"   seller@electrohub.com / seller123")
        print(f"   buyer@electrohub.com / buyer123")
        print(f"   alice@electrohub.com / alice123")
        print(f"   bob@electrohub.com / bob123")
        
        print(f"\n�� Access at: http://localhost:3000")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    insert_data()
