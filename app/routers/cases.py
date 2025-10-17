from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models, schemas
from ..dependencies.auth import require_roles
from ..services import audit as audit_service
from ..services import boxes as box_service
from ..services import cases as case_service

router = APIRouter(
    prefix="/api/v1/admin/cases",
    tags=["admin-cases"],
    dependencies=[Depends(require_roles("admin", "staff"))],
)

CaseSortField = Literal["found_id", "created_at", "status", "case_close_at"]
SortOrder = Literal["asc", "desc"]


def _get_case(
    db: Session, found_id: int, *, include_deleted: bool = False
) -> models.Case:
    case = db.get(models.Case, found_id)
    if not case or (case.deleted_at and not include_deleted):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case


@router.post("/", response_model=schemas.CaseRead, status_code=status.HTTP_201_CREATED)
def create_case(
    case: schemas.CaseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("admin", "staff")),
):
    if not case_service.is_valid_status(case.status):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    payload = case.model_dump(exclude_unset=True)
    payload.setdefault("status", case_service.DEFAULT_STATUS)
    db_case = models.Case(**payload)
    db.add(db_case)
    db.flush()
    audit_service.log_case_event(
        db,
        actor_id=current_user.user_id,
        action="create",
        case_id=db_case.found_id,
        metadata={"status": db_case.status},
    )
    db.commit()
    db.refresh(db_case)
    return db_case


@router.get("/", response_model=schemas.CaseListResponse)
def list_cases(
    db: Session = Depends(get_db),
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    box_id: Annotated[int | None, Query()] = None,
    item_id: Annotated[int | None, Query()] = None,
    reciver_id: Annotated[int | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    sort_by: Annotated[CaseSortField, Query()] = "found_id",
    sort_order: Annotated[SortOrder, Query()] = "desc",
):
    query = db.query(models.Case).filter(models.Case.deleted_at.is_(None))

    if status_filter is not None:
        if not case_service.is_valid_status(status_filter):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status filter"
            )
        query = query.filter(models.Case.status == status_filter)
    if box_id is not None:
        query = query.filter(models.Case.box_id == box_id)
    if item_id is not None:
        query = query.filter(models.Case.item_id == item_id)
    if reciver_id is not None:
        query = query.filter(models.Case.reciver_id == reciver_id)

    total = query.count()

    sort_map = {
        "found_id": models.Case.found_id,
        "created_at": models.Case.created_at,
        "status": models.Case.status,
        "case_close_at": models.Case.case_close_at,
    }
    order_column = sort_map[sort_by]
    if sort_order == "desc":
        order_column = order_column.desc()
    else:
        order_column = order_column.asc()

    items = (
        query.order_by(order_column).offset(offset).limit(limit).all()
    )
    return schemas.CaseListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{found_id}", response_model=schemas.CaseRead)
def get_case(found_id: int, db: Session = Depends(get_db)):
    return _get_case(db, found_id)


@router.put("/{found_id}", response_model=schemas.CaseRead)
def update_case(
    found_id: int,
    payload: schemas.CaseUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("admin", "staff")),
):
    case = _get_case(db, found_id)
    update_data = payload.model_dump(exclude_unset=True)
    changes: dict[str, tuple[object, object]] = {}

    if "remarks" in update_data and update_data["remarks"] != case.remarks:
        changes["remarks"] = (case.remarks, update_data["remarks"])
        case.remarks = update_data["remarks"]

    if not changes:
        return case

    audit_service.log_case_event(
        db,
        actor_id=current_user.user_id,
        action="update",
        case_id=case.found_id,
        metadata={
            "changes": {k: {"from": v[0], "to": v[1]} for k, v in changes.items()}
        },
    )
    db.commit()
    db.refresh(case)
    return case


@router.delete("/{found_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(
    found_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("admin", "staff")),
):
    case = _get_case(db, found_id, include_deleted=True)
    if case.deleted_at:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    case.deleted_at = datetime.utcnow()
    audit_service.log_case_event(
        db,
        actor_id=current_user.user_id,
        action="delete",
        case_id=case.found_id,
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _open_box(case: models.Case) -> None:
    if not case.box:
        return
    if case.box.status is False:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Box is disabled"
        )
    case.box.last_accessed = datetime.utcnow()
    result = await box_service.open_door(case.box)
    case.box.door_status = result.get("door_status", case.box.door_status)


async def _close_box(case: models.Case) -> None:
    if not case.box:
        return
    case.box.last_accessed = datetime.utcnow()
    result = await box_service.close_door(case.box)
    case.box.door_status = result.get("door_status", case.box.door_status)


def _apply_transition(case: models.Case, new_status: str) -> None:
    if not case_service.is_allowed_transition(case.status, new_status):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transition not allowed",
        )
    case.status = new_status
    if case_service.is_terminal(new_status):
        case.case_close_at = datetime.utcnow()
    else:
        case.case_close_at = None


def _apply_common_updates(
    case: models.Case, *, remarks: str | None = None, reciver_id: int | None = None
) -> None:
    if remarks is not None:
        case.remarks = remarks
    if reciver_id is not None:
        case.reciver_id = reciver_id


@router.post("/{found_id}:claim", response_model=schemas.CaseRead)
async def claim_case(
    found_id: int,
    payload: schemas.CaseClaimRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("admin", "staff")),
):
    case = _get_case(db, found_id)
    _apply_transition(case, "claimed")
    _apply_common_updates(
        case,
        remarks=payload.remarks,
        reciver_id=payload.reciver_id,
    )
    case.reciver_image_url = payload.reciver_image_url

    await _open_box(case)

    audit_service.log_case_event(
        db,
        actor_id=current_user.user_id,
        action="claim",
        case_id=case.found_id,
        metadata={
            "reciver_id": case.reciver_id,
            "box_id": case.box_id,
        },
    )
    db.commit()
    db.refresh(case)
    return case


@router.post("/{found_id}:retrieve", response_model=schemas.CaseRead)
async def retrieve_case(
    found_id: int,
    payload: schemas.CaseRetrieveRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("admin", "staff")),
):
    case = _get_case(db, found_id)
    _apply_transition(case, "retrieved")
    _apply_common_updates(
        case,
        remarks=payload.remarks,
        reciver_id=payload.reciver_id,
    )

    await _close_box(case)

    audit_service.log_case_event(
        db,
        actor_id=current_user.user_id,
        action="retrieve",
        case_id=case.found_id,
        metadata={
            "reciver_id": case.reciver_id,
            "box_id": case.box_id,
        },
    )
    db.commit()
    db.refresh(case)
    return case


@router.post("/{found_id}:expire", response_model=schemas.CaseRead)
async def expire_case(
    found_id: int,
    payload: schemas.CaseExpireRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("admin", "staff")),
):
    case = _get_case(db, found_id)
    _apply_transition(case, "expired")
    _apply_common_updates(case, remarks=payload.remarks)

    await _close_box(case)

    audit_service.log_case_event(
        db,
        actor_id=current_user.user_id,
        action="expire",
        case_id=case.found_id,
        metadata={"box_id": case.box_id},
    )
    db.commit()
    db.refresh(case)
    return case


@router.post("/{found_id}:forfeit", response_model=schemas.CaseRead)
async def forfeit_case(
    found_id: int,
    payload: schemas.CaseForfeitRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("admin", "staff")),
):
    case = _get_case(db, found_id)
    _apply_transition(case, "forfeited")
    _apply_common_updates(case, remarks=payload.remarks)

    await _close_box(case)

    audit_service.log_case_event(
        db,
        actor_id=current_user.user_id,
        action="forfeit",
        case_id=case.found_id,
        metadata={"box_id": case.box_id},
    )
    db.commit()
    db.refresh(case)
    return case
