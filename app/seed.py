# app/seed.py
import os
import random
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

# Password hashing function (same as in your router)
def get_password_hash(password: str) -> str:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    return pwd_context.hash(password)

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
            password=get_password_hash("admin123"),  # Hashed password
            role="admin",
            created_at=datetime.utcnow(),
        )
        db.add(admin)
        db.commit()
        print("✅ Admin user created: admin@example.com / admin123")

    # ✅ Seed Ethan Law user
    ethan_student_id = 1234
    existing_ethan = db.query(User).filter(User.student_id == ethan_student_id).first()
    
    if existing_ethan:
        print("Ethan Law user already exists.")
    else:
        ethan = User(
            user_id=1234,  # Explicitly set user_id
            name="Ethan Law",
            email="ethan.law@example.com",
            student_id=ethan_student_id,
            password=get_password_hash("1234"),  # Hashed password
            role="user",
            items_found=15,  # Random value between 1-30
            items_lost=8,    # Random value between 1-30
            created_at=datetime.utcnow(),
        )
        db.add(ethan)
        db.commit()
        print("✅ Ethan Law user created: student_id=1234 / password=1234")

    # ✅ Generate 30 random users
    first_names = ["Alex", "Taylor", "Jordan", "Casey", "Riley", "Morgan", "Avery", "Quinn", "Blake", "Hayden",
                  "Cameron", "Dakota", "Skyler", "Peyton", "Drew", "Rowan", "Sage", "Finley", "Emerson", "Sawyer",
                  "Kai", "Charlie", "Harper", "River", "Phoenix", "Reese", "Zion", "Arden", "Oakley", "Lennon"]
    
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                 "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
                 "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]
    
    existing_users_count = db.query(User).filter(User.student_id.like("122%")).count()
    
    if existing_users_count >= 30:
        print("Random users already exist — skipping.")
    else:
        # Clear existing random users if any (optional)
        db.query(User).filter(User.student_id.like("122%")).delete()
        
        random_users = []
        used_student_ids = set()
        
        for i in range(30):
            # Generate unique student ID starting with 122
            while True:
                student_id = 1220000 + random.randint(1000, 9999)
                if student_id not in used_student_ids and student_id != 1234:
                    used_student_ids.add(student_id)
                    break
            
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            user = User(
                name=f"{first_name} {last_name}",
                email=f"{first_name.lower()}.{last_name.lower()}{i}@example.com",
                student_id=student_id,
                password=get_password_hash("password123"),  # Default password for all random users
                role="user",
                items_found=random.randint(1, 30),
                items_lost=random.randint(1, 30),
                phone_number=f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                created_at=datetime.utcnow(),
            )
            random_users.append(user)
        
        db.add_all(random_users)
        db.commit()
        print(f"✅ 30 random users created with student IDs starting with 122")

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

    # Print summary
    total_users = db.query(User).count()
    print(f"\n📊 Database Summary:")
    print(f"   Total Users: {total_users}")
    print(f"   - Admin: 1")
    print(f"   - Ethan Law: 1")
    print(f"   - Random Users: 30")
    
    # Show some sample users
    sample_users = db.query(User).order_by(User.created_at.desc()).limit(5).all()
    print(f"\n👤 Sample Users:")
    for user in sample_users:
        print(f"   - {user.name} (ID: {user.student_id}) - Found: {user.items_found}, Lost: {user.items_lost}")

finally:
    db.close()
    print("Database session closed.")