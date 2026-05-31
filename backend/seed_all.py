#!/usr/bin/env python3
"""
seed_all.py — fills every table with realistic data for local development.

Run inside Docker:
    docker exec electrohub-backend python3 seed_all.py

Tables seeded:
    user_accounts         100 users  (including demo user)
    marketplace_items     500 items
    item_images           1-3 images per item
    item_interactions     3000 view/save/click events
    item_saved            saved items per user
    marketplace_messages  buyer→seller conversations
    user_activity         activity log rows
"""

import os, random, hashlib
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

fake = Faker("en_US")

DB_URL = (
    f"postgresql://{os.getenv('DB_USER','postgres')}:"
    f"{os.getenv('DB_PASSWORD','password')}@"
    f"{os.getenv('DB_HOST','localhost')}:"
    f"{os.getenv('DB_PORT','5432')}/"
    f"{os.getenv('DB_NAME','electrohub')}"
)

engine = create_engine(DB_URL, echo=False)
Session = sessionmaker(bind=engine)
db = Session()

def h(pw): return hashlib.sha256(pw.encode()).hexdigest()

# ── Electronics-focused category catalogue ────────────────────────────── #
CATEGORIES = {
    "Phones & Tablets": {
        "products": [
            "iPhone 15 Pro", "iPhone 14", "Samsung Galaxy S24 Ultra",
            "Samsung Galaxy A54", "Google Pixel 8 Pro", "Google Pixel 7a",
            "iPad Pro M2", "iPad Air", "Samsung Galaxy Tab S9",
            "OnePlus 12", "Xiaomi 14 Pro", "Nothing Phone 2",
        ],
        "images": [
            "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=400",
            "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400",
            "https://images.unsplash.com/photo-1585386959984-a4155224a1ad?w=400",
            "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=400",
        ],
    },
    "Computers & Laptops": {
        "products": [
            "MacBook Pro M3", "MacBook Air M2", "Dell XPS 15",
            "Lenovo ThinkPad X1 Carbon", "HP Spectre x360", "ASUS ROG Zephyrus",
            "Microsoft Surface Pro 9", "iMac 24-inch M3", "Mac Mini M2",
            "Razer Blade 16", "LG UltraFine 27-inch Monitor", "Samsung Odyssey G7",
        ],
        "images": [
            "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400",
            "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=400",
            "https://images.unsplash.com/photo-1593642632315-676ce68b786b?w=400",
            "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=400",
        ],
    },
    "Audio & Sound": {
        "products": [
            "Sony WH-1000XM5", "AirPods Pro 2nd Gen", "Bose QuietComfort 45",
            "Sony WF-1000XM5", "Jabra Evolve2 85", "Sennheiser HD 650",
            "Sonos Era 300", "Bose SoundLink Max", "JBL Charge 5",
            "Apple HomePod mini", "Sonos Move 2", "Bang & Olufsen Beosound A1",
        ],
        "images": [
            "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400",
            "https://images.unsplash.com/photo-1545127398-14699f92334b?w=400",
            "https://images.unsplash.com/photo-1606220838315-056192d5e927?w=400",
            "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400",
        ],
    },
    "Gaming": {
        "products": [
            "PlayStation 5", "Xbox Series X", "Nintendo Switch OLED",
            "Steam Deck", "PS5 DualSense Controller", "Xbox Elite Controller",
            "Razer DeathAdder V3", "Corsair K70 Keyboard", "LG OLED Gaming TV 55\"",
            "Meta Quest 3", "HyperX Cloud III Headset", "Elgato 4K60 Pro Capture Card",
        ],
        "images": [
            "https://images.unsplash.com/photo-1606144042614-b2417e99c4e3?w=400",
            "https://images.unsplash.com/photo-1593305841991-05c297ba4575?w=400",
            "https://images.unsplash.com/photo-1612287220310-f6e73d13e64a?w=400",
            "https://images.unsplash.com/photo-1536240478700-b869ad10e128?w=400",
        ],
    },
    "Smart Home": {
        "products": [
            "Amazon Echo Show 10", "Google Nest Hub Max", "Apple TV 4K",
            "Philips Hue Starter Kit", "Ring Video Doorbell Pro 2",
            "Nest Learning Thermostat", "Eufy RoboVac X9 Pro", "iRobot Roomba j7+",
            "Arlo Pro 5S Camera", "Amazon Echo Dot 5th Gen", "TP-Link Kasa Smart Plug",
            "Nanoleaf Shapes Panels",
        ],
        "images": [
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400",
            "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400",
            "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400",
            "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=400",
        ],
    },
    "Cameras & Drones": {
        "products": [
            "Sony A7 IV", "Canon EOS R6 Mark II", "Nikon Z6 III",
            "Fujifilm X-T5", "DJI Mini 4 Pro", "DJI Air 3",
            "GoPro Hero 12 Black", "Sony ZV-E10", "Canon EOS M50 Mark II",
            "DJI Osmo Pocket 3", "Insta360 X4", "Sony RX100 VII",
        ],
        "images": [
            "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=400",
            "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=400",
            "https://images.unsplash.com/photo-1606986628253-81e4e26e5b13?w=400",
            "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=400",
        ],
    },
}

LOCATIONS = [
    ("Denver", "CO", 80202), ("Boulder", "CO", 80301),
    ("New York", "NY", 10001), ("Los Angeles", "CA", 90001),
    ("Chicago", "IL", 60601), ("Austin", "TX", 78701),
    ("Seattle", "WA", 98101), ("Miami", "FL", 33101),
    ("Boston", "MA", 2101), ("San Francisco", "CA", 94102),
]

CONDITIONS = ["brand new", "like new", "excellent", "good", "fair"]

# ──────────────────────────────────────────────────────────────────────── #
#  1. Users                                                                #
# ──────────────────────────────────────────────────────────────────────── #
print("\n👥  Seeding users...")

db.execute(text("""
    INSERT INTO user_accounts
        (user_id, email, password_hash, name, phone, profile_picture,
         bio, city, state, zip_code, is_active, is_verified)
    VALUES
        ('user_demo_001', 'demo@electrohub.com', :pw, 'Demo User',
         '555-0100', 'https://ui-avatars.com/api/?name=Demo+User&size=200',
         'Demo account for testing.', 'Denver', 'CO', 80202, true, true)
    ON CONFLICT (email) DO NOTHING
"""), {"pw": h("password123")})

user_ids = ["user_demo_001"]
for i in range(2, 101):
    uid = f"user_{i:06d}"
    name = fake.name()
    city, state, zip_code = random.choice(LOCATIONS)
    db.execute(text("""
        INSERT INTO user_accounts
            (user_id, email, password_hash, name, phone, profile_picture,
             bio, city, state, zip_code, is_active, is_verified)
        VALUES
            (:uid, :email, :pw, :name, :phone, :pic, :bio,
             :city, :state, :zip, true, :verified)
        ON CONFLICT (email) DO NOTHING
    """), {
        "uid": uid,
        "email": f"{uid}@example.com",
        "pw": h("password123"),
        "name": name,
        "phone": fake.phone_number()[:15],
        "pic": f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&size=200",
        "bio": fake.sentence() if random.random() > 0.5 else None,
        "city": city, "state": state, "zip": zip_code,
        "verified": random.random() > 0.3,
    })
    user_ids.append(uid)

db.commit()
print(f"   ✅ {len(user_ids)} users ready")

# ──────────────────────────────────────────────────────────────────────── #
#  2. Marketplace items + images                                           #
# ──────────────────────────────────────────────────────────────────────── #
print("\n📦  Seeding marketplace items + images...")

item_ids = []
for _ in range(500):
    cat = random.choice(list(CATEGORIES.keys()))
    product = random.choice(CATEGORIES[cat]["products"])
    condition = random.choice(CONDITIONS)
    city, state, zip_code = random.choice(LOCATIONS)
    created_at = datetime.now() - timedelta(days=random.randint(1, 90))

    row = db.execute(text("""
        INSERT INTO marketplace_items
            (seller_id, title, description, category, price, city, state,
             zip_code, condition, views_count, saves_count, created_at, is_active)
        VALUES
            (:seller, :title, :desc, :cat, :price, :city, :state,
             :zip, :cond, :views, :saves, :created, true)
        RETURNING item_id
    """), {
        "seller": random.choice(user_ids),
        "title": f"{product} — {condition.title()}",
        "desc": fake.paragraph(nb_sentences=3),
        "cat": cat,
        "price": round(random.uniform(20, 3000), 2),
        "city": city, "state": state, "zip": zip_code,
        "cond": condition,
        "views": random.randint(0, 500),
        "saves": random.randint(0, 50),
        "created": created_at,
    })
    item_id = row.fetchone()[0]
    item_ids.append(item_id)

    # 1-3 images per item
    images = random.sample(CATEGORIES[cat]["images"], min(random.randint(1, 3), len(CATEGORIES[cat]["images"])))
    for j, url in enumerate(images):
        db.execute(text("""
            INSERT INTO item_images (item_id, image_url, is_thumbnail, upload_order)
            VALUES (:iid, :url, :thumb, :order)
        """), {"iid": item_id, "url": url, "thumb": j == 0, "order": j})

    if len(item_ids) % 100 == 0:
        db.commit()
        print(f"   {len(item_ids)}/500 items...")

db.commit()
print(f"   ✅ {len(item_ids)} items + images ready")

# ──────────────────────────────────────────────────────────────────────── #
#  3. Item interactions (views, saves, clicks)                             #
# ──────────────────────────────────────────────────────────────────────── #
print("\n👁   Seeding item interactions...")

for i in range(3000):
    db.execute(text("""
        INSERT INTO item_interactions
            (user_id, item_id, event_type, event_time, session_id)
        VALUES (:uid, :iid, :event, :time, :session)
    """), {
        "uid": random.choice(user_ids),
        "iid": random.choice(item_ids),
        "event": random.choices(["view", "save", "click"], weights=[0.7, 0.2, 0.1])[0],
        "time": datetime.now() - timedelta(days=random.randint(0, 30),
                                           hours=random.randint(0, 23)),
        "session": f"sess_{random.randint(1,9999):06d}",
    })
    if (i + 1) % 1000 == 0:
        db.commit()
        print(f"   {i+1}/3000 interactions...")

db.commit()
print("   ✅ 3000 interactions ready")

# ──────────────────────────────────────────────────────────────────────── #
#  4. Saved items (wishlist)                                               #
# ──────────────────────────────────────────────────────────────────────── #
print("\n❤️   Seeding saved items...")

saved_count = 0
for uid in random.sample(user_ids, 30):
    for iid in random.sample(item_ids, random.randint(2, 8)):
        try:
            db.execute(text("""
                INSERT INTO item_saved (user_id, item_id, saved_at)
                VALUES (:uid, :iid, :at)
                ON CONFLICT DO NOTHING
            """), {
                "uid": uid, "iid": iid,
                "at": datetime.now() - timedelta(days=random.randint(0, 20)),
            })
            saved_count += 1
        except Exception:
            db.rollback()

db.commit()
print(f"   ✅ {saved_count} saved items ready")

# ──────────────────────────────────────────────────────────────────────── #
#  5. Marketplace messages (buyer → seller conversations)                  #
# ──────────────────────────────────────────────────────────────────────── #
print("\n💬  Seeding messages...")

msg_count = 0
for _ in range(200):
    iid = random.choice(item_ids)
    item_row = db.execute(
        text("SELECT seller_id FROM marketplace_items WHERE item_id = :id"),
        {"id": iid}
    ).fetchone()
    if not item_row:
        continue
    seller_id = item_row[0]
    buyer_id = random.choice([u for u in user_ids if u != seller_id])

    db.execute(text("""
        INSERT INTO marketplace_messages
            (sender_id, receiver_id, item_id, message_text, sent_at, is_read)
        VALUES (:sender, :receiver, :iid, :msg, :sent, :read)
    """), {
        "sender": buyer_id,
        "receiver": seller_id,
        "iid": iid,
        "msg": fake.sentence(nb_words=random.randint(8, 20)),
        "sent": datetime.now() - timedelta(days=random.randint(0, 14)),
        "read": random.random() > 0.4,
    })
    msg_count += 1

db.commit()
print(f"   ✅ {msg_count} messages ready")

# ──────────────────────────────────────────────────────────────────────── #
#  6. User activity log                                                    #
# ──────────────────────────────────────────────────────────────────────── #
print("\n📊  Seeding user activity...")

activity_types = ["login", "view_item", "search", "save_item", "send_message"]
act_count = 0
for _ in range(1000):
    act_type = random.choice(activity_types)
    db.execute(text("""
        INSERT INTO user_activity
            (user_id, item_id, activity_type, action, session_id,
             ip_address, created_at)
        VALUES (:uid, :iid, :type, :action, :session, :ip, :created)
    """), {
        "uid": random.choice(user_ids),
        "iid": random.choice(item_ids) if act_type != "login" else None,
        "type": act_type,
        "action": act_type.replace("_", " ").title(),
        "session": f"sess_{random.randint(1,9999):06d}",
        "ip": fake.ipv4(),
        "created": datetime.now() - timedelta(days=random.randint(0, 30),
                                              hours=random.randint(0, 23)),
    })
    act_count += 1
    if act_count % 500 == 0:
        db.commit()

db.commit()
print(f"   ✅ {act_count} activity rows ready")

# ──────────────────────────────────────────────────────────────────────── #
#  Summary                                                                 #
# ──────────────────────────────────────────────────────────────────────── #
counts = {
    "users":        db.execute(text("SELECT COUNT(*) FROM user_accounts")).scalar(),
    "items":        db.execute(text("SELECT COUNT(*) FROM marketplace_items")).scalar(),
    "images":       db.execute(text("SELECT COUNT(*) FROM item_images")).scalar(),
    "interactions": db.execute(text("SELECT COUNT(*) FROM item_interactions")).scalar(),
    "saved":        db.execute(text("SELECT COUNT(*) FROM item_saved")).scalar(),
    "messages":     db.execute(text("SELECT COUNT(*) FROM marketplace_messages")).scalar(),
    "activity":     db.execute(text("SELECT COUNT(*) FROM user_activity")).scalar(),
}

db.close()

print("\n" + "="*50)
print("✅  ALL TABLES SEEDED")
print("="*50)
for table, count in counts.items():
    print(f"   {table:<15} {count:>6} rows")
print("\n🔑  Login: demo@electrohub.com / password123")
print("="*50)
