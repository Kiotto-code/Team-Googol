from __future__ import annotations

import json
from datetime import datetime
from typing import Annotated, Any, Awaitable, Callable, Literal

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.orm import Session
from jose import JWTError

from ..db import get_db
from .. import models, schemas
from ..dependencies.auth import require_roles
from ..services import audit as audit_service
from ..services import boxes as box_service
from ..services import idempotency as idempotency_service
from ..services import telemetry as telemetry_service
from ..services import auth as auth_service

router = APIRouter(
    prefix="/api/v1/admin/boxes",
    tags=["admin-boxes"],
)
ws_router = APIRouter(tags=["admin-boxes"])


SortField = Literal["box_id", "location", "status", "door_status", "last_accessed"]
SortOrder = Literal["asc", "desc"]


def _get_box(db: Session, box_id: int) -> models.Box:
    box = db.get(models.Box, box_id)
    if not box:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Box not found")
    return box


@router.post("/", response_model=schemas.BoxRead, status_code=status.HTTP_201_CREATED)
def create_box(
    box: schemas.BoxCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("admin", "staff")),
):
    db_box = models.Box(**box.model_dump(exclude_unset=True))
    db.add(db_box)
    db.flush()
    audit_service.log_box_event(
        db,
        actor_id=current_user.user_id,
        action="create",
        box_id=db_box.box_id,
    )
    db.commit()
    db.refresh(db_box)
    return db_box


@router.get("/", response_model=schemas.BoxListResponse)
def list_boxes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("admin", "staff")),
    *,
    location: Annotated[str | None, Query(description="Filter by location substring")] = None,
    status_filter: Annotated[bool | None, Query(alias="status")] = None,
    door_status: Annotated[bool | None, Query(description="Filter by door status")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum records to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    sort_by: Annotated[SortField, Query()] = "box_id",
    sort_order: Annotated[SortOrder, Query()] = "desc",
):
    query = db.query(models.Box)
    if location:
        query = query.filter(models.Box.location.ilike(f"%{location}%"))
    if status_filter is not None:
        query = query.filter(models.Box.status == status_filter)
    if door_status is not None:
        query = query.filter(models.Box.door_status == door_status)

    total = query.count()

    sort_map = {
        "box_id": models.Box.box_id,
        "location": models.Box.location,
        "status": models.Box.status,
        "door_status": models.Box.door_status,
        "last_accessed": models.Box.last_accessed,
    }
    order_column = sort_map[sort_by]
    if sort_order == "desc":
        order_column = order_column.desc()
    else:
        order_column = order_column.asc()

    items = (
        query.order_by(order_column).offset(offset).limit(limit).all()
    )
    return schemas.BoxListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{box_id}", response_model=schemas.BoxRead)
def get_box(
    box_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("admin", "staff")),
):
    return _get_box(db, box_id)


@router.put("/{box_id}", response_model=schemas.BoxRead)
def update_box(
    box_id: int,
    updates: schemas.BoxUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("admin", "staff")),
):
    box = _get_box(db, box_id)
    update_data = updates.model_dump(exclude_unset=True)
    changed_fields: dict[str, tuple[object, object]] = {}

    if "status" in update_data and update_data["status"] is False:
        box.door_status = False
    for field, value in update_data.items():
        previous = getattr(box, field)
        if previous != value:
            changed_fields[field] = (previous, value)
            setattr(box, field, value)

    if not changed_fields:
        return box

    box.last_accessed = datetime.utcnow()

    audit_service.log_box_event(
        db,
        actor_id=current_user.user_id,
        action="update",
        box_id=box.box_id,
        metadata={
            "changes": {k: {"from": v[0], "to": v[1]} for k, v in changed_fields.items()}
        },
    )
    db.commit()
    db.refresh(box)
    return box


@router.get(
    "/{box_id}/telemetry",
    response_model=schemas.BoxTelemetryList,
)
def get_box_telemetry(
    box_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("admin", "staff")),
    *,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    _get_box(db, box_id)
    query = db.query(models.BoxTelemetry).filter(models.BoxTelemetry.box_id == box_id)
    total = query.count()
    items = (
        query.order_by(models.BoxTelemetry.recorded_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return schemas.BoxTelemetryList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


async def _handle_idempotent_action(
    *,
    db: Session,
    box: models.Box,
    box_id: int,
    action: str,
    idempotency_key: str,
    perform_action: Callable[[models.Box], Awaitable[dict[str, Any]]],
    audit_actor: models.User,
    precondition: Callable[[], None] | None = None,
) -> schemas.BoxActionResponse:
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required",
        )

    scope = idempotency_service.build_scope(box_id, action)
    existing = idempotency_service.find_entry(db, scope=scope, key=idempotency_key)
    if existing and existing.response_code is not None:
        body = json.loads(existing.response_body or "{}")
        return schemas.BoxActionResponse(**body)
    if existing and existing.response_code is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another request with the same idempotency key is in progress",
        )

    if precondition is not None:
        precondition()

    entry = idempotency_service.claim_key(db, scope=scope, key=idempotency_key)

    try:
        result = await perform_action(box)
    except Exception:
        db.delete(entry)
        db.flush()
        raise

    telemetry_entry = telemetry_service.record_telemetry(
        db,
        box=box,
        payload={"action": action, **result},
    )

    response_model = schemas.BoxActionResponse(
        box_id=box.box_id,
        action=action,
        message=result.get("message", ""),
        status=box.status,
        door_status=box.door_status,
        telemetry=schemas.BoxTelemetryRead.model_validate(telemetry_entry).model_dump(),
    )

    idempotency_service.finalize_key(
        entry,
        response_code=status.HTTP_200_OK,
        response_body=response_model.model_dump(),
    )

    audit_service.log_box_event(
        db,
        actor_id=audit_actor.user_id,
        action=action,
        box_id=box.box_id,
        metadata={"result": result},
    )
    db.commit()

    await telemetry_service.telemetry_manager.broadcast(
        {
            "type": "telemetry",
            "box_id": box.box_id,
            "telemetry": response_model.telemetry,
        }
    )
    return response_model


@router.post(
    "/{box_id}:open-door",
    response_model=schemas.BoxActionResponse,
)
async def open_box_door(
    box_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("admin", "staff")),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    box = _get_box(db, box_id)

    def ensure_enabled() -> None:
        if box.status is False:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Box is disabled",
            )

    async def perform(target: models.Box) -> dict[str, Any]:
        target.last_accessed = datetime.utcnow()
        target.door_status = True
        return await box_service.open_door(target)

    return await _handle_idempotent_action(
        db=db,
        box=box,
        box_id=box_id,
        action="open-door",
        idempotency_key=idempotency_key or "",
        perform_action=perform,
        audit_actor=current_user,
        precondition=ensure_enabled,
    )


@router.post(
    "/{box_id}:close-door",
    response_model=schemas.BoxActionResponse,
)
async def close_box_door(
    box_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("admin", "staff")),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    box = _get_box(db, box_id)

    def ensure_enabled() -> None:
        if box.status is False:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Box is disabled",
            )

    async def perform(target: models.Box) -> dict[str, Any]:
        target.last_accessed = datetime.utcnow()
        target.door_status = False
        return await box_service.close_door(target)

    return await _handle_idempotent_action(
        db=db,
        box=box,
        box_id=box_id,
        action="close-door",
        idempotency_key=idempotency_key or "",
        perform_action=perform,
        audit_actor=current_user,
        precondition=ensure_enabled,
    )


@router.post(
    "/{box_id}:ping",
    response_model=schemas.BoxActionResponse,
)
async def ping_box(
    box_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("admin", "staff")),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    box = _get_box(db, box_id)

    def ensure_enabled() -> None:
        if box.status is False:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Box is disabled",
            )

    async def perform(target: models.Box) -> dict[str, Any]:
        target.last_accessed = datetime.utcnow()
        return await box_service.ping_box(target)

    return await _handle_idempotent_action(
        db=db,
        box=box,
        box_id=box_id,
        action="ping",
        idempotency_key=idempotency_key or "",
        perform_action=perform,
        audit_actor=current_user,
        precondition=ensure_enabled,
    )


@router.post(
    "/{box_id}:mark-empty",
    response_model=schemas.BoxActionResponse,
)
async def mark_box_empty(
    box_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("admin", "staff")),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    box = _get_box(db, box_id)

    async def perform(target: models.Box) -> dict[str, Any]:
        target.last_accessed = datetime.utcnow()
        target.load = 0
        return await box_service.mark_empty(target)

    return await _handle_idempotent_action(
        db=db,
        box=box,
        box_id=box_id,
        action="mark-empty",
        idempotency_key=idempotency_key or "",
        perform_action=perform,
        audit_actor=current_user,
    precondition=None,
    )


@ws_router.websocket("/api/v1/admin/ws/boxes")
async def boxes_ws(
    websocket: WebSocket,
    token: Annotated[str, Query(description="Bearer access token")],
    db: Session = Depends(get_db),
):
    try:
        payload = auth_service.decode_token(token)
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if payload.get("type") != "access":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user = db.get(models.User, int(user_id))
    if not user or user.role not in {"admin", "staff"}:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await telemetry_service.telemetry_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await telemetry_service.telemetry_manager.disconnect(websocket)


__all__ = ["router", "ws_router"]
