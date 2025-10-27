from datetime import datetime
from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import engine, SessionLocal
from app.models import Base, User

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def seed_user(*, name: str, email: str | None, student_id: int, password: str) -> None:
    # Ensure tables and minimal columns
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(users)"))
        cols = [row[1] for row in result.fetchall()]
        if "items_lost" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN items_lost INTEGER DEFAULT 0"))
        if "items_found" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN items_found INTEGER DEFAULT 0"))

    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.student_id == student_id).first()
        hashed = pwd_context.hash(password)
        if user:
            user.name = name
            user.email = email
            user.password = hashed
            user.role = "user"
            if user.items_found is None:
                user.items_found = 0
            if user.items_lost is None:
                user.items_lost = 0
            db.commit()
            print(f"✅ Updated user {student_id}")
        else:
            user = User(
                name=name,
                email=email,
                student_id=student_id,
                password=hashed,
                role="user",
                items_found=0,
                items_lost=0,
                created_at=datetime.utcnow(),
            )
            db.add(user)
            db.commit()
            print(f"✅ Created user {student_id}")
    finally:
        db.close()


if __name__ == "__main__":
    # Default demo user
    seed_user(name="Test User", email="user@example.com", student_id=2001001, password="user1234")
