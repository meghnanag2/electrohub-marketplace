```python
#!/usr/bin/env python3
"""
Generate synthetic marketplace data for ElectroHub.

This script is designed to work in:
- Local Mac/dev environment
- Docker containers
- Kubernetes / GKE Jobs

DB configuration is read from environment variables:

    DB_HOST        default: 127.0.0.1
    DB_PORT        default: 5432
    DB_NAME        default: electrohub
    DB_USER        default: postgres
    DB_PASSWORD    default: password

Make sure the schema is already created (01_schema.sql, 02_indexes.sql)
before running this script.
"""

import os
import random
import hashlib
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import execute_values
from faker import Faker

fake = Faker("en_US")


def get_db_config():
    """Read DB config from environment variables with sensible defaults."""
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "electrohub"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "password"),
    }


# --- Data templates ---------------------------------------------------------

CATEGORIES = {
    "Phones": {
        "items": [
            "iPhone 13",
            "iPhone 14 Pro",
            "Samsung Galaxy S22",
            "Google Pixel 7",
            "OnePlus 11",
        ]
    },
    "Laptops": {
        "items": [
            "MacBook Air M1",
            "MacBook Pro M2",
            "Dell XPS 13",
            "Lenovo ThinkPad X1",
            "HP Spectre x360",
        ]
    },
    "Consoles": {
        "items": [
            "PlayStation 5",
            "Xbox Series X",
            "Nintendo Switch OLED",
            "Steam Deck",
        ]
    },
    "Accessories": {
        "items": [
            "AirPods Pro",
            "Sony WH-1000XM5",
            "Logitech MX Master 3",
            "Mechanical Keyboard",
            "4K Monitor",
        ]
    },
}

US_LOCATIONS = [
    ("Boulder", "CO", "80301"),
    ("Denver", "CO", "80202"),
    ("Seattle", "WA", "98101"),
    ("San Francisco", "CA", "94103"),
    ("Austin", "TX", "73301"),
    ("New York", "NY", "10001"),
]


# --- Helper functions ------------------------------------------------------


def hash_password(password: str) -> str:
    """Simple password hashing (demo only)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_demo_user(conn):
    """
    Create a single demo user if not already present.

    Email: demo@electrohub.com
    Password (plain): password123
    """
    demo_email = "demo@electrohub.com"
    demo_password = "password123"

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT user_id FROM user_accounts
            WHERE email = %s
            """,
            (demo_email,),
        )
        row = cur.fetchone()
        if row:
            print(f"👤 Demo user already exists: {demo_email} (user_id={row[0]})")
            return row[0]

        user_id = f"user_demo_001"
        password_hash = hash_password(demo_password)

        cur.execute(
            """
            INSERT INTO user_accounts (
                user_id,
                email,
                password_hash,
                name,
                is_active,
                created_at,
                last_login
            )
            VALUES (%s, %s, %s, %s, true, NOW(), NULL)
            """,
            (user_id, demo_email, password_hash, "Demo User"),
        )

        print(f"✅ Created demo user: {demo_email} (user_id={user_id})")
        return user_id


def create_users(conn, count: int = 200) -> list[str]:
    """Create additional synthetic users and return their IDs."""
    print(f"👥 Creating {count} users...")

    users = []
    for i in range(count):
        user_id = f"user_{i+1:04d}"
        email = f"{user_id}@example.com"
        name = fake.name()
        password_hash = hash_password("password123")

        users.append(
            (
                user_id,
                email,
                password_hash,
                name,
            )
        )

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO user_accounts (
                user_id,
                email,
                password_hash,
                name,
                is_active,
                created_at,
                last_login
            )
            VALUES %s
            ON CONFLICT (user_id) DO NOTHING
            """,
            [(u[0], u[1], u[2], u[3]) for u in users],
        )

    conn.commit()
    print("✅ Users created.")
    return [u[0] for u in users]


def create_items(conn, user_ids: list[str], count: int = 500) -> list[str]:
    """Create marketplace items."""
    print(f"📦 Creating {count} items...")

    items = []
    for i in range(count):
        seller_id = random.choice(user_ids)
        category = random.choice(list(CATEGORIES.keys()))
        item_name = random.choice(CATEGORIES[category]["items"])

        title = f"{item_name} - {random.choice(['Like New', 'Excellent', 'Good', 'Brand New'])}"
        description = fake.paragraph(nb_sentences=3)
        price = round(random.uniform(20, 2000), 2)
        city, state, zip_code = random.choice(US_LOCATIONS)
        condition = random.choice(["new", "like new", "good", "fair"])
        status = random.choice(["available", "reserved", "sold"])

        item_id = f"item_{i+1:05d}"

        items.append(
            (
                item_id,
                seller_id,
                title,
                description,
                category,
                price,
                condition,
                status,
                city,
                state,
                zip_code,
            )
        )

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO marketplace_items (
                item_id,
                seller_id,
                title,
                description,
                category,
                price,
                condition,
                status,
                city,
                state,
                zip_code,
                created_at
            )
            VALUES %s
            ON CONFLICT (item_id) DO NOTHING
            """,
            [
                (
                    i[0],
                    i[1],
                    i[2],
                    i[3],
                    i[4],
                    i[5],
                    i[6],
                    i[7],
                    i[8],
                    i[9],
                    i[10],
                    datetime.utcnow() - timedelta(days=random.randint(0, 60)),
                )
                for i in items
            ],
        )

    conn.commit()
    print("✅ Items created.")
    return [i[0] for i in items]


def create_interactions(
    conn,
    user_ids: list[str],
    item_ids: list[str],
    count: int = 2000,
) -> None:
    """Create synthetic user-item interactions for activity feeds / analytics."""
    print(f"🔄 Creating {count} interactions...")

    actions = ["view", "favorite", "message_seller", "purchase"]
    interactions = []

    for _ in range(count):
        user_id = random.choice(user_ids)
        item_id = random.choice(item_ids)
        action = random.choices(actions, weights=[0.6, 0.2, 0.15, 0.05])[0]
        ts = datetime.utcnow() - timedelta(days=random.randint(0, 60))

        interactions.append((user_id, item_id, action, ts))

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO user_item_interactions (
                user_id,
                item_id,
                action,
                created_at
            )
            VALUES %s
            """,
            interactions,
        )

    conn.commit()
    print("✅ Interactions created.")


def main():
    print("🚀 Starting data generation...")

    cfg = get_db_config()
    print(
        f"🔌 Connecting to DB {cfg['database']} at {cfg['host']}:{cfg['port']} "
        f"as {cfg['user']}"
    )

    try:
        conn = psycopg2.connect(**cfg)
    except psycopg2.OperationalError as e:
        print("❌ Failed to connect to the database.")
        print(str(e))
        raise SystemExit(1)

    try:
        # demo user
        demo_user_id = create_demo_user(conn)

        # synthetic users
        user_ids = create_users(conn, count=200)
        user_ids.append(demo_user_id)

        # items
        item_ids = create_items(conn, user_ids=user_ids, count=500)

        # interactions
        create_interactions(conn, user_ids=user_ids, item_ids=item_ids, count=2000)

    finally:
        conn.close()

    print("\n" + "=" * 50)
    print("✅ DATA GENERATION COMPLETE!")
    print("=" * 50)
    print("\n🔐 Demo Credentials:")
    print("   Email: demo@electrohub.com")
    print("   Password: password123")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
```