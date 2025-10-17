from __future__ import annotations

import os
from datetime import datetime
from typing import Iterable

import numpy as np
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session
from werkzeug.utils import secure_filename

from .. import models, schemas
from ..db import get_db
from ..dependencies.auth import require_roles
from ..services import audit as audit_service
from ..services import items as item_service
from ..utils.caption_utils import generate_caption_with_gemini
from ..utils.clip_utils import get_text_embedding, UPLOAD_FOLDER
from ..utils.upload_utils import is_lighting_good

admin_access = require_roles("admin", "staff")

admin_router = APIRouter(
    prefix="/api/v1/admin/items",
    tags=["admin-items"],
    dependencies=[Depends(admin_access)],
)
public_router = APIRouter(prefix="/api/v1/items", tags=["items"])

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_current_admin(user: models.User = Depends(admin_access)) -> models.User:
    return user


def _get_item_or_404(
    db: Session, item_id: int, *, include_deleted: bool = False
) -> models.Item:
    item = db.get(models.Item, item_id)
    if not item or (item.deleted_at and not include_deleted):
        raise HTTPException(status_code=404, detail="Item not found")
    return item


def _schedule_embedding_refresh(
    background_tasks: BackgroundTasks,
    item_id: int,
    *,
    refresh_image: bool = True,
    refresh_description: bool = True,
) -> None:
    if not (refresh_image or refresh_description):
        return
    background_tasks.add_task(
        item_service.refresh_item_embeddings,
        item_id,
        refresh_image=refresh_image,
        refresh_description=refresh_description,
    )


def _should_refresh_embeddings(fields: Iterable[str]) -> tuple[bool, bool]:
    refresh_image = any(field in {"image_url"} for field in fields)
    refresh_description = any(
        field in {"description", "gemini_description"} for field in fields
    )
    return refresh_image, refresh_description


@admin_router.post("/", response_model=schemas.ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(
    item: schemas.ItemCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin),
):
    db_item = models.Item(**item.model_dump(exclude_unset=True))
    if db_item.status and not item_service.is_valid_status(db_item.status):
        raise HTTPException(status_code=400, detail="Invalid status value")

    db.add(db_item)
    db.flush()

    audit_service.log_item_event(
        db,
        actor_id=current_admin.user_id,
        action="create",
        item_id=db_item.item_id,
        metadata={"status": db_item.status},
    )

    refresh_image, refresh_description = _should_refresh_embeddings(
        item.model_dump(exclude_unset=True).keys()
    )
    db.commit()
    db.refresh(db_item)

    _schedule_embedding_refresh(
        background_tasks,
        db_item.item_id,
        refresh_image=refresh_image,
        refresh_description=refresh_description or bool(db_item.description),
    )

    return db_item


def _base_item_query(db: Session, include_deleted: bool):
    query = db.query(models.Item)
    if not include_deleted:
        query = query.filter(models.Item.deleted_at.is_(None))
    return query


@admin_router.get("/", response_model=schemas.PaginatedItems)
def list_items(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    sort: str = Query("-created_at"),
    status: str | None = Query(None),
    finder_user_id: int | None = Query(None),
    created_from: datetime | None = Query(None),
    created_to: datetime | None = Query(None),
    updated_from: datetime | None = Query(None),
    updated_to: datetime | None = Query(None),
    include_deleted: bool = Query(False),
):
    query = _base_item_query(db, include_deleted)

    if status:
        if not item_service.is_valid_status(status):
            raise HTTPException(status_code=400, detail="Invalid status filter")
        query = query.filter(models.Item.status == status)

    if finder_user_id is not None:
        query = query.filter(models.Item.finder_user_id == finder_user_id)

    if created_from:
        query = query.filter(models.Item.created_at >= created_from)
    if created_to:
        query = query.filter(models.Item.created_at <= created_to)
    if updated_from:
        query = query.filter(models.Item.updated_at >= updated_from)
    if updated_to:
        query = query.filter(models.Item.updated_at <= updated_to)

    sortable_columns = {
        "created_at": models.Item.created_at,
        "updated_at": models.Item.updated_at,
        "status": models.Item.status,
        "finder_user_id": models.Item.finder_user_id,
        "item_id": models.Item.item_id,
    }

    sort_key = sort.lstrip("+-")
    column = sortable_columns.get(sort_key)
    if column is None:
        raise HTTPException(status_code=400, detail="Invalid sort field")
    order_clause = column.desc() if sort.startswith("-") else column.asc()

    total = query.count()
    total_pages = (total + limit - 1) // limit if total else 0
    if page > 1 and (page - 1) * limit >= total and total != 0:
        raise HTTPException(status_code=400, detail="Page out of range")

    items = (
        query.order_by(order_clause)
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return schemas.PaginatedItems(
        data=items,
        meta=schemas.PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
        ),
    )


@public_router.get("/", response_model=list[schemas.ItemRead])
def list_items_public(db: Session = Depends(get_db)):
    return (
        db.query(models.Item)
        .filter(models.Item.deleted_at.is_(None))
        .order_by(models.Item.item_id.desc())
        .all()
    )


@admin_router.get("/{item_id}", response_model=schemas.ItemRead)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    include_deleted: bool = Query(False),
):
    return _get_item_or_404(db, item_id, include_deleted=include_deleted)


@admin_router.put("/{item_id}", response_model=schemas.ItemRead)
def update_item(
    item_id: int,
    payload: schemas.ItemUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin),
):
    item = _get_item_or_404(db, item_id, include_deleted=True)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return item

    if "status" in updates:
        new_status = updates["status"]
        if not item_service.is_valid_status(new_status):
            raise HTTPException(status_code=400, detail="Invalid status value")
        if not item_service.is_allowed_transition(item.status, new_status):
            raise HTTPException(status_code=400, detail="Invalid status transition")

    for field, value in updates.items():
        setattr(item, field, value)
    item.updated_at = datetime.utcnow()

    audit_service.log_item_event(
        db,
        actor_id=current_admin.user_id,
        action="update",
        item_id=item.item_id,
        metadata={"changes": updates},
    )

    refresh_image, refresh_description = _should_refresh_embeddings(updates.keys())
    db.add(item)
    db.commit()
    db.refresh(item)

    _schedule_embedding_refresh(
        background_tasks,
        item.item_id,
        refresh_image=refresh_image,
        refresh_description=refresh_description,
    )

    return item


@admin_router.delete("/{item_id}", response_model=schemas.ItemRead)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin),
):
    item = _get_item_or_404(db, item_id, include_deleted=True)
    if item.deleted_at:
        return item

    item.deleted_at = datetime.utcnow()
    previous_status = item.status
    if previous_status != "archived":
        item.status = "archived"

    audit_service.log_item_event(
        db,
        actor_id=current_admin.user_id,
        action="delete",
        item_id=item.item_id,
        metadata={"previous_status": previous_status},
    )

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@admin_router.post(":search-similar", response_model=schemas.SimilarItemsResponse)
def search_similar_items(
    payload: schemas.SimilarItemSearchRequest,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin),
):
    embedding_field = (
        "image_embedding" if payload.use_image else "description_embedding"
    )

    query_vector: np.ndarray | None = None
    query_item_id: int | None = None

    if payload.item_id is not None:
        query_item = _get_item_or_404(
            db, payload.item_id, include_deleted=payload.include_deleted
        )
        query_item_id = query_item.item_id
        stored_embedding = getattr(query_item, embedding_field)
        query_vector = item_service.parse_embedding(stored_embedding)
        if query_vector is None and payload.generate_if_missing:
            item_service.refresh_item_embeddings(
                query_item.item_id,
                refresh_image=payload.use_image,
                refresh_description=not payload.use_image,
            )
            db.refresh(query_item)
            stored_embedding = getattr(query_item, embedding_field)
            query_vector = item_service.parse_embedding(stored_embedding)

    if payload.description:
        tensor = get_text_embedding(payload.description)
        vector = tensor.detach().cpu().numpy().flatten()
        norm = np.linalg.norm(vector)
        if norm:
            query_vector = vector / norm

    if query_vector is None:
        raise HTTPException(status_code=400, detail="Query embedding unavailable")

    candidate_query = _base_item_query(db, payload.include_deleted)
    if query_item_id:
        candidate_query = candidate_query.filter(models.Item.item_id != query_item_id)

    candidates = candidate_query.all()
    results: list[schemas.SimilarItemResult] = []

    for candidate in candidates:
        candidate_embedding = getattr(candidate, embedding_field)
        vector = item_service.parse_embedding(candidate_embedding)
        if vector is None:
            if payload.generate_if_missing:
                item_service.refresh_item_embeddings(
                    candidate.item_id,
                    refresh_image=payload.use_image,
                    refresh_description=not payload.use_image,
                )
                db.refresh(candidate)
                candidate_embedding = getattr(candidate, embedding_field)
                vector = item_service.parse_embedding(candidate_embedding)
        if vector is None:
            continue
        score = item_service.cosine_similarity(query_vector, vector)
        results.append(
            schemas.SimilarItemResult(item=candidate, score=score)
        )

    results.sort(key=lambda r: r.score, reverse=True)
    limited_results = results[: payload.max_results]

    return schemas.SimilarItemsResponse(query_item_id=query_item_id, results=limited_results)


@admin_router.post(":bulk-update-status", response_model=schemas.BulkStatusUpdateResponse)
def bulk_update_status(
    payload: schemas.BulkStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin),
):
    if not item_service.is_valid_status(payload.status):
        raise HTTPException(status_code=400, detail="Invalid status value")
    if payload.status != "expired":
        raise HTTPException(status_code=400, detail="Only expiration is supported")

    unique_ids = set(payload.item_ids)
    if not unique_ids:
        raise HTTPException(status_code=400, detail="No item ids provided")

    items = (
        db.query(models.Item)
        .filter(models.Item.item_id.in_(unique_ids))
        .all()
    )

    found_ids = {item.item_id for item in items}
    not_found = sorted(unique_ids - found_ids)

    updated_ids: list[int] = []
    already_expired: list[int] = []

    for item in items:
        if item.deleted_at:
            already_expired.append(item.item_id)
            continue
        if item.status == payload.status:
            already_expired.append(item.item_id)
            continue
        if not item_service.is_allowed_transition(item.status, payload.status):
            already_expired.append(item.item_id)
            continue
        item.status = payload.status
        item.updated_at = datetime.utcnow()
        updated_ids.append(item.item_id)
        db.add(item)

    if updated_ids:
        audit_service.log_item_event(
            db,
            actor_id=current_admin.user_id,
            action="bulk_update_status",
            metadata={"item_ids": updated_ids, "status": payload.status},
        )

    db.commit()

    return schemas.BulkStatusUpdateResponse(
        status=payload.status,
        result=schemas.BulkStatusUpdateResult(
            updated_ids=updated_ids,
            already_in_status=already_expired,
            not_found_ids=not_found,
        ),
    )


@admin_router.post("/upload", response_model=schemas.ItemRead, status_code=status.HTTP_201_CREATED)
async def upload_item(
    image: UploadFile,
    background_tasks: BackgroundTasks,
    finder_user_id: int = Form(...),
    description: str | None = Form(None),
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin),
):
    """Uploads an image, validates lighting, generates caption, and stores item in DB."""

    filename = secure_filename(image.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, "wb") as buffer:
        buffer.write(await image.read())

    good, brightness, contrast = is_lighting_good(filepath)
    if not good:
        os.remove(filepath)
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Lighting is not good enough, please re-upload.",
                "brightness": brightness,
                "contrast": contrast,
            },
        )

    custom_prompt = (
        "Output as: Color: <…>; Type: <…>; Material: <…>; Features: <…>; Optional: Brand/Markings: <…>."
    )
    gemini_caption = generate_caption_with_gemini(filepath, prompt=custom_prompt)
    combined_caption = f"{description}. {gemini_caption}" if description else gemini_caption

    new_item = models.Item(
        gemini_description=gemini_caption,
        description=combined_caption,
        image_url=filepath,
        status="uploaded",
        finder_user_id=finder_user_id,
    )

    db.add(new_item)
    db.flush()

    audit_service.log_item_event(
        db,
        actor_id=current_admin.user_id,
        action="upload",
        item_id=new_item.item_id,
        metadata={"finder_user_id": finder_user_id},
    )

    db.commit()
    db.refresh(new_item)

    _schedule_embedding_refresh(
        background_tasks,
        new_item.item_id,
        refresh_image=True,
        refresh_description=True,
    )

    return new_item
