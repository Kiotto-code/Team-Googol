from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from ..db import get_db
from .. import models, schemas

admin_router = APIRouter(prefix="/api/v1/admin/users", tags=["admin-users"])
public_router = APIRouter(prefix="/api/v1/users", tags=["users"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


@admin_router.post("/", response_model=schemas.UserRead)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check unique constraints
    if user.email:
        existing = db.query(models.User).filter(models.User.email == user.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
    if user.rfid_tag:
        existing = db.query(models.User).filter(models.User.rfid_tag == user.rfid_tag).first()
        if existing:
            raise HTTPException(status_code=400, detail="RFID tag already registered")

    db_user = models.User(
        name=user.name,
        phone_number=user.phone_number,
        email=user.email,
        student_id=user.student_id,
        rfid_tag=user.rfid_tag,
        items_found=user.items_found or 0,
        items_find=user.items_find or 0,
        role=user.role if hasattr(user, "role") and user.role else "user",
        password=get_password_hash(user.password) if user.password else None,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@admin_router.get("/", response_model=list[schemas.UserRead])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.user_id.desc()).all()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# /register endpoint
@public_router.post("/register", response_model=schemas.UserRead)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if student ID already registered
    existing = db.query(models.User).filter(models.User.student_id == user.student_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student ID already registered"
        )

    # Check if email or RFID already registered (optional, if you want stricter checks)
    if user.email:
        existing_email = db.query(models.User).filter(models.User.email == user.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")

    if user.rfid_tag:
        existing_rfid = db.query(models.User).filter(models.User.rfid_tag == user.rfid_tag).first()
        if existing_rfid:
            raise HTTPException(status_code=400, detail="RFID tag already registered")

    # Hash password before saving
    hashed_password = get_password_hash(user.password)

    db_user = models.User(
        name=user.name,
        phone_number=user.phone_number,
        email=user.email,
        student_id=user.student_id,
        rfid_tag=user.rfid_tag,
        items_found=user.items_found or 0,
        items_find=user.items_find or 0,
        role=user.role if hasattr(user, "role") and user.role else "user",
        password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@public_router.post("/login")
def login_user(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.student_id == credentials.student_id).first()

    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid student ID or password"
        )
    
    return {
        "message": "Login successful",
        "user_id": user.user_id,        # include user ID
        # "user": schemas.UserRead.from_orm(user) # Optional
    }
