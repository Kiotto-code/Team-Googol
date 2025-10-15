from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..dependencies.auth import require_roles
from ..services import auth as auth_service

router = APIRouter(prefix="/api/v1/admin/auth", tags=["admin-auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ADMIN_ALLOWED_ROLES = {"admin", "staff"}


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    if not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def _permissions_for_role(role: str) -> list[str]:
    if role == "admin":
        return [
            "users:manage",
            "items:manage",
            "boxes:manage",
            "cases:manage",
        ]
    if role == "staff":
        return [
            "users:view",
            "items:manage",
            "cases:manage",
        ]
    return []


@router.post("/login", response_model=schemas.AdminAuthResponse)
def admin_login(
    credentials: schemas.AdminLoginRequest,
    db: Session = Depends(get_db),
):
    identifier = credentials.identifier.strip()
    user = None
    if "@" in identifier:
        user = db.query(models.User).filter(models.User.email == identifier).first()
    else:
        user = db.query(models.User).filter(models.User.student_id == identifier).first()

    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if user.role not in ADMIN_ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    access_token = auth_service.create_access_token(user.user_id, user.role)
    refresh_token = auth_service.create_refresh_token()
    token_entry = models.RefreshToken(
        user_id=user.user_id,
        token_hash=auth_service.hash_token(refresh_token),
        expires_at=auth_service.refresh_expiration(),
        revoked=False,
    )
    db.add(token_entry)
    db.commit()
    db.refresh(user)

    return schemas.AdminAuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
        roles=[user.role],
    )


@router.post("/refresh", response_model=schemas.AdminAuthResponse)
def refresh_tokens(
    payload: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    hashed = auth_service.hash_token(payload.refresh_token)
    token_entry = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.token_hash == hashed)
        .first()
    )

    if (
        not token_entry
        or token_entry.revoked
        or token_entry.expires_at <= datetime.utcnow()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user = db.get(models.User, token_entry.user_id)
    if not user or user.role not in ADMIN_ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    new_refresh_token = auth_service.create_refresh_token()
    token_entry.token_hash = auth_service.hash_token(new_refresh_token)
    token_entry.expires_at = auth_service.refresh_expiration()
    token_entry.revoked = False
    token_entry.created_at = datetime.utcnow()
    db.add(token_entry)

    access_token = auth_service.create_access_token(user.user_id, user.role)
    db.commit()

    return schemas.AdminAuthResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
        roles=[user.role],
    )


@router.post("/logout")
def admin_logout(
    payload: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles("admin", "staff")),
):
    hashed = auth_service.hash_token(payload.refresh_token)
    token_entry = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.token_hash == hashed)
        .first()
    )

    if token_entry and not token_entry.revoked:
        token_entry.revoked = True
        db.add(token_entry)
        db.commit()

    return {"detail": "Logged out"}


@router.get("/me", response_model=schemas.AdminMeResponse)
def read_current_admin(
    current_user: models.User = Depends(require_roles("admin", "staff")),
):
    return schemas.AdminMeResponse(
        user=current_user,
        roles=[current_user.role],
        permissions=_permissions_for_role(current_user.role),
    )
