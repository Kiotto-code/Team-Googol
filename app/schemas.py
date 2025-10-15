from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional
from typing import Literal
from typing import List


# User Schemas
class UserBase(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[int] = None
    email: Optional[EmailStr] = None
    student_id: Optional[int] = None
    rfid_tag: Optional[str] = None
    items_found: Optional[int] = 0
    items_find: Optional[int] = 0
    role: Literal["user", "admin", "staff"] = "user"


class UserCreate(UserBase):
    password: Optional[str] = None
    

class UserLogin(BaseModel):
    student_id: str
    password: str


class UserRead(UserBase):
    user_id: int
    created_at: datetime
    is_disabled: bool
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserRoleUpdate(BaseModel):
    role: Literal["user", "admin", "staff"]


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[int] = None
    email: Optional[EmailStr] = None
    student_id: Optional[int] = None
    rfid_tag: Optional[str] = None
    items_found: Optional[int] = None
    items_find: Optional[int] = None
    role: Optional[Literal["user", "admin", "staff"]] = None
    is_disabled: Optional[bool] = None


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class PaginatedUsers(BaseModel):
    data: List[UserRead]
    meta: PaginationMeta


class PasswordResetResponse(BaseModel):
    user_id: int
    temporary_password: str


class UserStats(BaseModel):
    user_id: int
    total_found_items: int
    total_cases_received: int
    open_cases: int
    closed_cases: int
    last_found_item_at: Optional[datetime] = None
    last_case_received_at: Optional[datetime] = None


class AdminLoginRequest(BaseModel):
    identifier: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class AdminAuthResponse(TokenPair):
    user: UserRead
    roles: List[str]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AdminMeResponse(BaseModel):
    user: UserRead
    roles: List[str]
    permissions: List[str]


# Item Schemas
class ItemBase(BaseModel):
    gemini_description:Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    image_embedding: Optional[str] = None
    description_embedding: Optional[str] = None
    status: Optional[str] = None
    finder_user_id: Optional[int] = None
    finder_img_url: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class ItemRead(ItemBase):
    item_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Box Schemas
class BoxBase(BaseModel):
    status: Optional[bool] = None
    location: Optional[str] = None
    load: Optional[int] = None
    door_status: Optional[bool] = None
    last_accessed: Optional[datetime] = None


class BoxCreate(BoxBase):
    pass


class BoxRead(BoxBase):
    box_id: int

    class Config:
        from_attributes = True


# Case Schemas
class CaseBase(BaseModel):
    box_id: Optional[int] = None
    reciver_image_url: Optional[str] = None
    reciver_id: Optional[int] = None
    item_id: Optional[int] = None
    status: Optional[str] = None
    case_close_at: Optional[datetime] = None


class CaseCreate(CaseBase):
    pass


class CaseRead(CaseBase):
    found_id: int
    created_at: datetime

    class Config:
        from_attributes = True
