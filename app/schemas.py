from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


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
    items_lost: Optional[int] = None
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
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ItemUpdate(BaseModel):
    gemini_description: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    finder_user_id: Optional[int] = None
    finder_img_url: Optional[str] = None
    status: Optional[str] = None

class CaseCreatePayload(BaseModel):
    item_id: int
    reciver_id: int
    box_id: int

class CaseCancelPayload(BaseModel):
    case_id: int
    item_id: int
    
class CaseCollectPayload(BaseModel):
    case_id: int
    item_id: int
    box_id: int

class CaseCollectedPayload(BaseModel):
    case_id: int
    item_id: int
    box_id: int
    
class PaginatedItems(BaseModel):
    data: List[ItemRead]
    meta: PaginationMeta


class SimilarItemResult(BaseModel):
    item: ItemRead
    score: float


class SimilarItemSearchRequest(BaseModel):
    item_id: Optional[int] = None
    description: Optional[str] = None
    use_image: bool = False
    include_deleted: bool = False
    max_results: int = Field(10, ge=1, le=100)
    generate_if_missing: bool = True

    @model_validator(mode="after")
    def validate_query(cls, values: "SimilarItemSearchRequest"):
        if not values.item_id and not values.description:
            raise ValueError("Either item_id or description must be provided")
        return values


class SimilarItemsResponse(BaseModel):
    query_item_id: Optional[int] = None
    results: List[SimilarItemResult]


class BulkStatusUpdateRequest(BaseModel):
    item_ids: List[int] = Field(..., min_length=1)
    status: str


class BulkStatusUpdateResult(BaseModel):
    updated_ids: List[int]
    already_in_status: List[int]
    not_found_ids: List[int]


class BulkStatusUpdateResponse(BaseModel):
    status: str
    result: BulkStatusUpdateResult


# Reporting schemas
class OverviewUsersMetrics(BaseModel):
    total: int
    active: int
    disabled: int
    deleted: int


class OverviewItemsMetrics(BaseModel):
    total: int
    deleted: int
    by_status: dict[str, int]


class OverviewCasesMetrics(BaseModel):
    total: int
    open: int
    closed: int
    closed_last_30_days: int
    average_resolution_hours: float | None = None


class OverviewBoxesMetrics(BaseModel):
    total: int
    available: int
    unavailable: int
    unknown: int
    with_active_cases: int
    average_load: float | None = None
    doors_open: int


class OverviewReport(BaseModel):
    generated_at: datetime
    users: OverviewUsersMetrics
    items: OverviewItemsMetrics
    cases: OverviewCasesMetrics
    boxes: OverviewBoxesMetrics


class BoxUtilizationEntry(BaseModel):
    box_id: int
    location: Optional[str] = None
    status: Optional[bool] = None
    load: Optional[int] = None
    door_status: Optional[bool] = None
    last_accessed: Optional[datetime] = None
    total_cases: int
    active_cases: int
    utilization_rate: Optional[float] = None


class BoxUtilizationTotals(BaseModel):
    total_boxes: int
    active_boxes: int
    doors_open: int
    total_cases: int
    active_cases: int
    average_load: Optional[float] = None


class BoxUtilizationReport(BaseModel):
    generated_at: datetime
    totals: BoxUtilizationTotals
    boxes: list[BoxUtilizationEntry]


# Box Schemas
class BoxBase(BaseModel):
    status: Optional[bool] = None
    location: Optional[str] = None
    load: Optional[int] = None
    door_status: Optional[bool] = None
    last_accessed: Optional[datetime] = None


class BoxCreate(BoxBase):
    pass


class BoxUpdate(BaseModel):
    status: Optional[bool] = None
    location: Optional[str] = None
    load: Optional[int] = None

    @model_validator(mode="after")
    def validate_payload(self):
        if not any(value is not None for value in self.model_dump().values()):
            raise ValueError("At least one field must be provided for update")
        return self


class BoxRead(BoxBase):
    box_id: int

    class Config:
        from_attributes = True


class BoxListResponse(BaseModel):
    items: List[BoxRead]
    total: int
    limit: int
    offset: int


class BoxActionResponse(BaseModel):
    box_id: int
    action: str
    message: str
    status: Optional[bool] = None
    door_status: Optional[bool] = None
    telemetry: Optional[dict[str, Any]] = None


class BoxTelemetryRead(BaseModel):
    telemetry_id: int
    box_id: int
    recorded_at: datetime
    payload: dict[str, Any]

    class Config:
        from_attributes = True


class BoxTelemetryList(BaseModel):
    items: List[BoxTelemetryRead]
    total: int
    limit: int
    offset: int


# Case Schemas
class CaseBase(BaseModel):
    box_id: Optional[int] = None
    reciver_image_url: Optional[str] = None
    reciver_id: Optional[int] = None
    item_id: Optional[int] = None
    status: Optional[str] = None
    case_close_at: Optional[datetime] = None
    remarks: Optional[str] = None


class CaseCreate(CaseBase):
    pass


class CaseRead(CaseBase):
    found_id: int
    created_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    items: List[CaseRead]
    total: int
    limit: int
    offset: int


class CaseUpdate(BaseModel):
    remarks: Optional[str] = None


class CaseClaimRequest(BaseModel):
    reciver_id: int
    reciver_image_url: Optional[str] = None
    remarks: Optional[str] = None


class CaseRetrieveRequest(BaseModel):
    remarks: Optional[str] = None
    reciver_id: Optional[int] = None


class CaseExpireRequest(BaseModel):
    remarks: Optional[str] = None


class CaseForfeitRequest(BaseModel):
    remarks: Optional[str] = None


class AuditLogRead(BaseModel):
    audit_id: int
    actor_user_id: int
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_")
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedAuditLogs(BaseModel):
    data: List[AuditLogRead]
    meta: PaginationMeta
