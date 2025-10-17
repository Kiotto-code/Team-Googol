# app/seed.py
import os
from datetime import datetime
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from app.db import engine
from app.models import Base, User, Box

# Explicit DB path — force into app/app.db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

print(f"Seeding database: {DB_PATH}")
Base.metadata.create_all(bind=engine)
db = SessionLocal()
print(f"Using database: {DB_PATH}")
print("Creating tables (if not exist)...")

# --- Create tables if they don't exist ---
Base.metadata.create_all(bind=engine)

# --- Open a session ---
SessionLocal = sessionmaker(bind=engine)
db: Session = SessionLocal()

try:
    # ✅ Seed Admin User
    admin_email = "admin@example.com"
    existing_admin = db.query(User).filter(User.email == admin_email).first()

    if existing_admin:
        print("Admin user already exists.")
    else:
        admin = User(
            name="Admin",
            email=admin_email,
            password="admin123",  # ⚠️ Plaintext for testing only
            role="admin",
            created_at=datetime.utcnow(),
        )
        db.add(admin)
        db.commit()
        print("✅ Admin user created: admin@example.com / admin123")

    # ✅ Seed Boxes
    if db.query(Box).count() == 0:
        boxes = [
            Box(status=True, location="Front Desk", load=0, door_status=False),
            Box(status=False, location="Storage Room", load=0, door_status=False),
        ]
        db.add_all(boxes)
        db.commit()
        print("✅ Boxes seeded successfully.")
    else:
        print("Boxes already exist — skipping.")

finally:
    db.close()
    print("Database session closed.")
