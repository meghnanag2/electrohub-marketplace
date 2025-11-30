from app.core.database import engine, Base
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy.orm import sessionmaker

print("\n=== CREATING TABLES ===")

Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully!")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("\n=== ADDING DEMO USER ===")

demo = db.query(User).filter(User.email == "demo@electrohub.com").first()
if demo:
    print("⚠️  Demo user already exists")
else:
    demo_user = User(
        user_id="user_demo_001",
        email="demo@electrohub.com",
        password_hash=get_password_hash("password123"),
        name="Demo User",
        city="Denver",
        state="CO",
        zip_code=80202,
        phone="555-0001",
        is_active=True
    )
    db.add(demo_user)
    db.commit()
    print("✅ Demo user created!")

db.close()
print("\n✅ Database initialization complete!\n")
