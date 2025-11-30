from app.core.database import engine, Base
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy.orm import sessionmaker

# Create all tables
print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Tables created")

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Create demo user
print("Creating demo user...")
demo_user = User(
    user_id="user_demo_001",
    email="demo@electrohub.com",
    password_hash=get_password_hash("password123"),
    name="Demo User",
    city="Denver",
    state="CO",
    zip_code=80202,
    phone="555-0001",
    profile_picture="https://via.placeholder.com/200"
)

db.add(demo_user)
db.commit()
print("✅ Demo user created: demo@electrohub.com / password123")
db.close()
