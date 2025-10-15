from datetime import datetime
from typing import Any
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .db import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('user','admin','staff')",
            name="ck_users_role_allowed",
        ),
    )

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    password: Mapped[str | None] = mapped_column(String, nullable=True)
    phone_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    email: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    student_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rfid_tag: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    items_found: Mapped[int | None] = mapped_column(Integer, default=0)
    items_find: Mapped[int | None] = mapped_column(Integer, default=0)
    # 'user', 'admin', or 'staff'
    role: Mapped[str] = mapped_column(String, nullable=False, default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    found_items: Mapped[list["Item"]] = relationship(
        back_populates="finder", cascade="all, delete-orphan"
    )


class Item(Base):
    __tablename__ = "items"

    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    image_embedding: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_embedding: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    finder_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=True
    )
    finder_img_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    finder: Mapped[User | None] = relationship(back_populates="found_items")
    cases: Mapped[list["Case"]] = relationship(back_populates="item")


class Box(Base):
    __tablename__ = "boxes"

    box_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    status: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    load: Mapped[int | None] = mapped_column(Integer, nullable=True)
    door_status: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_accessed: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    cases: Mapped[list["Case"]] = relationship(back_populates="box")
    telemetry_entries: Mapped[list["BoxTelemetry"]] = relationship(
        back_populates="box", cascade="all, delete-orphan"
    )


class Case(Base):
    __tablename__ = "cases"

    found_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    box_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("boxes.box_id"))
    reciver_image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    reciver_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.user_id"))
    item_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("items.item_id"), nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    case_close_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    box: Mapped[Box | None] = relationship(back_populates="cases")
    item: Mapped[Item | None] = relationship(back_populates="cases")
    receiver: Mapped[User | None] = relationship()


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    token_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), index=True)
    token_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    actor_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False)
    target_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=True)
    action: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    actor: Mapped[User] = relationship(foreign_keys=[actor_user_id])
    target: Mapped[User | None] = relationship(foreign_keys=[target_user_id])


class BoxTelemetry(Base):
    __tablename__ = "box_telemetry"

    telemetry_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    box_id: Mapped[int] = mapped_column(Integer, ForeignKey("boxes.box_id"), index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    box: Mapped[Box] = relationship(back_populates="telemetry_entries")


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint("scope", "key", name="uq_idempotency_scope_key"),
    )

    idempotency_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scope: Mapped[str] = mapped_column(String, nullable=False, index=True)
    key: Mapped[str] = mapped_column(String, nullable=False)
    response_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
