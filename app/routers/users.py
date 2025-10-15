from __future__ import annotations

from datetime import datetime
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from ..db import get_db
from .. import models, schemas
from ..dependencies.auth import require_roles
from ..services import audit as audit_service

admin_access = require_roles("admin", "staff")


def get_current_admin_user(user: models.User = Depends(admin_access)) -> models.User:
    return user


admin_router = APIRouter(
    prefix="/api/v1/admin/users",
    tags=["admin-users"],
    dependencies=[Depends(admin_access)],
)
public_router = APIRouter(prefix="/api/v1/users", tags=["users"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _get_user_or_404(db: Session, user_id: int) -> models.User:
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _ensure_unique_fields(
    db: Session,
    *,
    email: str | None = None,
    rfid_tag: str | None = None,
    exclude_user_id: int | None = None,
) -> None:
    if email:
        query = db.query(models.User).filter(models.User.email == email)
        if exclude_user_id:
            query = query.filter(models.User.user_id != exclude_user_id)
        if query.first():
            raise HTTPException(status_code=400, detail="Email already registered")
    if rfid_tag:
        query = db.query(models.User).filter(models.User.rfid_tag == rfid_tag)
        if exclude_user_id:
            query = query.filter(models.User.user_id != exclude_user_id)
        if query.first():
            raise HTTPException(status_code=400, detail="RFID tag already registered")


@admin_router.post("/", response_model=schemas.UserRead)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
):
    _ensure_unique_fields(db, email=user.email, rfid_tag=user.rfid_tag)

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
    db.flush()

    audit_service.log_user_event(
        db,
        actor_id=current_admin.user_id,
        action="create",
        user_id=db_user.user_id,
        metadata={"email": user.email, "rfid_tag": user.rfid_tag},
    )
    db.commit()
    db.refresh(db_user)
    return db_user


@admin_router.get("/", response_model=schemas.PaginatedUsers)
def list_users(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    sort: str = Query("-created_at"),
    q: str | None = Query(None),
    role: str | None = Query(None),
    rfid_tag: str | None = Query(None),
    email: str | None = Query(None),
):
    query = db.query(models.User).filter(models.User.deleted_at.is_(None))

    if q:
        like_pattern = f"%{q.lower()}%"
        query = query.filter(
            or_(
                func.lower(models.User.name).like(like_pattern),
                func.lower(models.User.email).like(like_pattern),
                func.lower(models.User.rfid_tag).like(like_pattern),
                cast(models.User.student_id, String).like(f"%{q}%"),
            )
        )

    if role:
        if role not in {"user", "admin", "staff"}:
            raise HTTPException(status_code=400, detail="Invalid role filter")
        query = query.filter(models.User.role == role)

    if rfid_tag:
        query = query.filter(models.User.rfid_tag == rfid_tag)

    if email:
        query = query.filter(func.lower(models.User.email) == email.lower())

    sortable_columns = {
        "created_at": models.User.created_at,
        "name": models.User.name,
        "email": models.User.email,
        "role": models.User.role,
        "items_found": models.User.items_found,
        "items_find": models.User.items_find,
    }

    sort_key = sort.lstrip("+-")
    column = sortable_columns.get(sort_key)
    if not column:
        raise HTTPException(status_code=400, detail="Invalid sort field")
    order_clause = column.desc() if sort.startswith("-") else column.asc()

    total = query.count()
    total_pages = (total + limit - 1) // limit if total else 0
    if page > 1 and (page - 1) * limit >= total and total != 0:
        raise HTTPException(status_code=400, detail="Page out of range")

    users = (
        query.order_by(order_clause)
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return schemas.PaginatedUsers(
        data=users,
        meta=schemas.PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
        ),
    )


@admin_router.get("/{user_id}", response_model=schemas.UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin_user),
):
    return _get_user_or_404(db, user_id)


@admin_router.put("/{user_id}", response_model=schemas.UserRead)
def update_user(
    user_id: int,
    payload: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
):
    user = _get_user_or_404(db, user_id)

    updates = payload.model_dump(exclude_unset=True)

    if "email" in updates:
        _ensure_unique_fields(db, email=updates["email"], exclude_user_id=user_id)
    if "rfid_tag" in updates:
        _ensure_unique_fields(db, rfid_tag=updates["rfid_tag"], exclude_user_id=user_id)
    if "role" in updates and current_admin.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins may change roles")

    for field, value in updates.items():
        setattr(user, field, value)

    audit_service.log_user_event(
        db,
        actor_id=current_admin.user_id,
        action="update",
        user_id=user.user_id,
        metadata=updates,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@admin_router.delete("/{user_id}", response_model=schemas.UserRead)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
):
    user = _get_user_or_404(db, user_id)

    if user.deleted_at:
        raise HTTPException(status_code=400, detail="User already deleted")

    user.deleted_at = datetime.utcnow()
    user.is_disabled = True

    audit_service.log_user_event(
        db,
        actor_id=current_admin.user_id,
        action="soft_delete",
        user_id=user.user_id,
        metadata={"deleted_at": user.deleted_at.isoformat()},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@admin_router.post(
    "/{user_id}/reset-password", response_model=schemas.PasswordResetResponse
)
def reset_user_password(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
):
    user = _get_user_or_404(db, user_id)

    temporary_password = secrets.token_urlsafe(12)
    user.password = get_password_hash(temporary_password)

    audit_service.log_user_event(
        db,
        actor_id=current_admin.user_id,
        action="reset_password",
        user_id=user.user_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return schemas.PasswordResetResponse(
        user_id=user.user_id,
        temporary_password=temporary_password,
    )


@admin_router.get("/{user_id}/stats", response_model=schemas.UserStats)
def get_user_stats(
    user_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin_user),
):
    _get_user_or_404(db, user_id)

    total_found_items = (
        db.query(func.count(models.Item.item_id))
        .filter(models.Item.finder_user_id == user_id)
        .scalar()
        or 0
    )

    total_cases_received = (
        db.query(func.count(models.Case.found_id))
        .filter(models.Case.reciver_id == user_id)
        .scalar()
        or 0
    )

    status_lower = func.lower(models.Case.status)

    open_cases = (
        db.query(func.count(models.Case.found_id))
        .filter(models.Case.reciver_id == user_id)
        .filter(or_(status_lower.is_(None), status_lower != "closed"))
        .scalar()
        or 0
    )

    closed_cases = (
        db.query(func.count(models.Case.found_id))
        .filter(models.Case.reciver_id == user_id)
        .filter(status_lower == "closed")
        .scalar()
        or 0
    )

    last_found_item_at = (
        db.query(func.max(models.Item.created_at))
        .filter(models.Item.finder_user_id == user_id)
        .scalar()
    )

    last_case_received_at = (
        db.query(func.max(models.Case.created_at))
        .filter(models.Case.reciver_id == user_id)
        .scalar()
    )

    return schemas.UserStats(
        user_id=user_id,
        total_found_items=total_found_items,
        total_cases_received=total_cases_received,
        open_cases=open_cases,
        closed_cases=closed_cases,
        last_found_item_at=last_found_item_at,
        last_case_received_at=last_case_received_at,
    )


@admin_router.post("/{user_id}/role", response_model=schemas.UserRead)
def update_user_role(
    user_id: int,
    payload: schemas.UserRoleUpdate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(require_roles("admin")),
):
    user = _get_user_or_404(db, user_id)
    if user.deleted_at:
        raise HTTPException(status_code=400, detail="Cannot update deleted user")

    user.role = payload.role
    db.add(user)
    audit_service.log_user_event(
        db,
        actor_id=current_admin.user_id,
        action="update_role",
        user_id=user.user_id,
        metadata={"role": payload.role},
    )
    db.commit()
    db.refresh(user)
    return user


# Public endpoints
@public_router.post("/register", response_model=schemas.UserRead)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.student_id == user.student_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student ID already registered",
        )

    if user.email:
        existing_email = db.query(models.User).filter(models.User.email == user.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")

    if user.rfid_tag:
        existing_rfid = db.query(models.User).filter(models.User.rfid_tag == user.rfid_tag).first()
        if existing_rfid:
            raise HTTPException(status_code=400, detail="RFID tag already registered")

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

    if (
        not user
        or user.deleted_at is not None
        or user.is_disabled
        or user.password is None
        or not verify_password(credentials.password, user.password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid student ID or password",
        )

    return {
        "message": "Login successful",
        "user_id": user.user_id,
    }
