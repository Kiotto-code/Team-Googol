from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/users", tags=["users"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


@router.post("/", response_model=schemas.UserRead)
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
        password=get_password_hash(user.password) if user.password else None,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/", response_model=list[schemas.UserRead])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.user_id.desc()).all()
