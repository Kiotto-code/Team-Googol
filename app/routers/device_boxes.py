"""Device-facing endpoints for coordinating smart box hardware."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..services import audit as audit_service
from ..services import telemetry as telemetry_service


router = APIRouter(prefix="/api/v1/boxes", tags=["device-boxes"])

DEVICE_ACTOR_EMAIL = "device@system.localdomain"
DEVICE_ACTOR_NAME = "Smart Box Device"


def _get_box(db: Session, box_id: int) -> models.Box:
    box = db.get(models.Box, box_id)
    if not box:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Box not found")
    return box


def _get_device_actor(db: Session) -> models.User:
    # Try current canonical email first
    actor = (
        db.query(models.User)
        .filter(models.User.email == DEVICE_ACTOR_EMAIL)
        .one_or_none()
    )
    if actor:
        return actor
    # Back-compat: migrate legacy device email if present
    legacy = (
        db.query(models.User)
        .filter(models.User.email == "device@system.local")
        .one_or_none()
    )
    if legacy:
        legacy.email = DEVICE_ACTOR_EMAIL
        db.add(legacy)
        db.flush()
        return legacy
    actor = models.User(
        name=DEVICE_ACTOR_NAME,
        email=DEVICE_ACTOR_EMAIL,
        role="staff",
        password=None,
        is_disabled=False,
    )
    db.add(actor)
    db.flush()
    return actor


def _record_action(
    db: Session,
    *,
    box: models.Box,
    action: str,
    telemetry_payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    user_id: int | None = None,
) -> schemas.DeviceBoxActionResponse:
    telemetry_entry = telemetry_service.record_telemetry(
        db, box=box, payload=telemetry_payload
    )
    actor = _get_device_actor(db)
    audit_service.log_box_event(
        db,
        actor_id=actor.user_id,
        action=action,
        box_id=box.box_id,
        metadata=metadata or {},
    )
    db.flush()
    return schemas.DeviceBoxActionResponse(
        box_id=box.box_id,
        action=action,
        box_status=box.status,
        door_status=box.door_status,
        telemetry_id=telemetry_entry.telemetry_id,
        user_id=user_id,
        metadata=metadata or {},
    )


@router.post(
    "/{box_id}/deposit/unlock",
    response_model=schemas.DeviceBoxActionResponse,
)
def request_deposit_unlock(
    box_id: int,
    payload: schemas.BoxDepositUnlockRequest,
    db: Session = Depends(get_db),
):
    box = _get_box(db, box_id)
    if box.status is not True:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Box is not available for deposit",
        )
    if box.door_status is True:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Door already open",
        )

    box.door_status = True
    box.last_accessed = datetime.now(timezone.utc)

    response = _record_action(
        db,
        box=box,
        action="deposit_unlock",
        telemetry_payload={
            "event": "deposit_unlock",
            "request_id": payload.request_id,
            "device_id": payload.device_id,
            "door_status": True,
            "box_status": box.status,
        },
        metadata={
            "request_id": payload.request_id,
            "device_id": payload.device_id,
        },
    )
    db.commit()
    db.refresh(box)
    response.box_status = box.status
    response.door_status = box.door_status
    return response


@router.post(
    "/{box_id}/deposit/complete",
    response_model=bool,
)
def complete_deposit(
    box_id: int,
    payload: schemas.BoxDepositCompleteRequest,
    db: Session = Depends(get_db),
):
    box = _get_box(db, box_id)
    if box.status is not True:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Box is not ready for deposit completion",
        )
    if box.door_status is not True:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Door must be open before completing deposit",
        )

    box.status = True
    box.load = payload.load if payload.load is not None else box.load
    box.door_status = not payload.door_closed
    box.last_accessed = datetime.now(timezone.utc)

    _record_action(
        db,
        box=box,
        action="deposit_complete",
        telemetry_payload={
            "event": "deposit_complete",
            "request_id": payload.request_id,
            "load": payload.load,
            "door_closed": payload.door_closed,
            "box_status": box.status,
            "door_status": box.door_status,
        },
        metadata={
            "request_id": payload.request_id,
            "load": payload.load,
            "door_closed": payload.door_closed,
        },
    )
    db.commit()
    db.refresh(box)

    # Link deposit completion to case lifecycle: set latest pending case for this box to 'stored'
    pending_case = (
        db.query(models.Case)
        .filter(models.Case.box_id == box.box_id, models.Case.status == "pending")
        .order_by(models.Case.created_at.desc())
        .first()
    )
    if pending_case:
        pending_case.status = "stored"
        pending_case.case_close_at = None
        # If the case has an item, ensure item is 'active' in storage
        if pending_case.item_id:
            item = db.query(models.Item).get(pending_case.item_id)
            if item:
                item.status = "active"
                db.add(item)
        db.add(pending_case)
        db.commit()
        db.refresh(pending_case)

    return True


@router.post(
    "/{box_id}/pickup/validate",
    response_model=bool,
)
def validate_pickup(
    box_id: int,
    payload: schemas.BoxPickupValidationRequest,
    db: Session = Depends(get_db),
):
    box = _get_box(db, box_id)
    if box.load is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Box is not holding an item for pickup",
        )
    if box.door_status is True:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Door already open",
        )
    case_rec = (
        db.query(models.Case)
        .filter((models.Case.box_id == 1) & (models.Case.status == "claimed"))
        .one_or_none()
    )
    user_id = case_rec.reciver_id if case_rec else None
    user = (
        db.query(models.User)
    .filter((models.User.rfid_tag == payload.rfid_uid) & (models.User.user_id == user_id))
        .one_or_none()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RFID UID not recognized",
        )

    box.door_status = True
    box.last_accessed = datetime.now(timezone.utc)

    _record_action(
        db,
        box=box,
        action="pickup_validate",
        telemetry_payload={
            "event": "pickup_validate",
            "request_id": payload.request_id,
            "rfid_uid": payload.rfid_uid,
            "user_id": user.user_id,
            "door_status": box.door_status,
            "box_status": box.status,
        },
        metadata={
            "request_id": payload.request_id,
            "rfid_uid": payload.rfid_uid,
            "user_id": user.user_id,
        },
        user_id=user.user_id,
    )
    db.commit()
    db.refresh(box)
    return True


@router.post(
    "/{box_id}/pickup/complete",
    response_model=schemas.DeviceBoxActionResponse,
)
def complete_pickup(
    box_id: int,
    payload: schemas.BoxPickupCompleteRequest,
    db: Session = Depends(get_db),
):
    box = _get_box(db, box_id)
    if box.door_status is not True:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Door must be open to complete pickup",
        )

    user_id: int | None = None
    if payload.rfid_uid:
        user = (
            db.query(models.User)
            .filter(models.User.rfid_tag == payload.rfid_uid)
            .one_or_none()
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="RFID UID not recognized",
            )
        user_id = user.user_id

    box.status = True
    box.door_status = False
    box.load = 0
    box.last_accessed = datetime.now(timezone.utc)

    response = _record_action(
        db,
        box=box,
        action="pickup_complete",
        telemetry_payload={
            "event": "pickup_complete",
            "request_id": payload.request_id,
            "rfid_uid": payload.rfid_uid,
            "photo_url": payload.photo_url,
            "photo_taken_at": (
                payload.photo_taken_at.isoformat()
                if payload.photo_taken_at
                else None
            ),
            "box_status": box.status,
            "door_status": box.door_status,
        },
        metadata={
            "request_id": payload.request_id,
            "rfid_uid": payload.rfid_uid,
            "photo_url": payload.photo_url,
            "photo_taken_at": (
                payload.photo_taken_at.isoformat()
                if payload.photo_taken_at
                else None
            ),
        },
        user_id=user_id,
    )
    db.commit()
    db.refresh(box)
    response.box_status = box.status
    response.door_status = box.door_status
    response.user_id = user_id
    return response


@router.post(
    "/{box_id}/door-timeout",
    response_model=schemas.DeviceBoxActionResponse,
)
def log_door_timeout(
    box_id: int,
    payload: schemas.BoxDoorTimeoutRequest,
    db: Session = Depends(get_db),
):
    box = _get_box(db, box_id)

    box.door_status = payload.door_open
    box.last_accessed = datetime.now(timezone.utc)

    response = _record_action(
        db,
        box=box,
        action="door_timeout",
        telemetry_payload={
            "event": "door_timeout",
            "request_id": payload.request_id,
            "duration_seconds": payload.duration_seconds,
            "door_open": payload.door_open,
            "box_status": box.status,
        },
        metadata={
            "request_id": payload.request_id,
            "duration_seconds": payload.duration_seconds,
            "door_open": payload.door_open,
        },
    )
    db.commit()
    db.refresh(box)
    response.box_status = box.status
    response.door_status = box.door_status
    return response


@router.post(
    "/{box_id}/activity",
    response_model=schemas.DeviceBoxActionResponse,
)
def log_infrared_activity(
    box_id: int,
    payload: schemas.BoxInfraredActivityRequest,
    db: Session = Depends(get_db),
):
    box = _get_box(db, box_id)
    box.last_accessed = datetime.now(timezone.utc)

    response = _record_action(
        db,
        box=box,
        action="infrared_activity",
        telemetry_payload={
            "event": "infrared_activity",
            "request_id": payload.request_id,
            "triggered": payload.triggered,
            "sensor_value": payload.sensor_value,
            "box_status": box.status,
            "door_status": box.door_status,
        },
        metadata={
            "request_id": payload.request_id,
            "triggered": payload.triggered,
            "sensor_value": payload.sensor_value,
        },
    )
    db.commit()
    db.refresh(box)
    response.box_status = box.status
    response.door_status = box.door_status
    return response
