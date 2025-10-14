from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .db import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    password: Mapped[str | None] = mapped_column(String, nullable=True)
    phone_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    email: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    student_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rfid_tag: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    items_found: Mapped[int | None] = mapped_column(Integer, default=0)
    items_find: Mapped[int | None] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

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
