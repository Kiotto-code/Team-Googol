from __future__ import annotations

import os
import json
from datetime import datetime, timezone
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
)
from fastapi import status
from sqlalchemy.orm import Session
from werkzeug.utils import secure_filename

from .. import models, schemas
from ..db import get_db
from ..dependencies.auth import require_roles
from ..services import audit as audit_service
from ..services import items as item_service
from ..utils.caption_utils import generate_caption_with_gemini
from ..utils.clip_utils import get_text_embedding, UPLOAD_FOLDER, get_image_embedding
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
    # Decide if embeddings should be recalculated based on updated fields
    refresh_image = any(field in {"image_url"} for field in fields)
    refresh_description = any(
        field in {"description", "gemini_description"} for field in fields
    )
    return refresh_image, refresh_description


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
    public_url = f"http://127.0.0.1:8000/uploads/{filename}"

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
        image_url=public_url,
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

    # Create a case and update default box (box_id=1) on admin upload
    box = db.query(models.Box).filter(models.Box.box_id == 1).first()
    if box is None:
        raise HTTPException(status_code=404, detail="Default box (id=1) not found")
    box.status = True
    box.door_status = True
    box.last_accessed = datetime.utcnow()

    new_case = models.Case(
        item_id=new_item.item_id,
        box_id=box.box_id,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(new_case)
    db.commit()

    _schedule_embedding_refresh(
        background_tasks,
        new_item.item_id,
        refresh_image=True,
        refresh_description=True,
    )

    return new_item


@public_router.post("/upload", response_model=schemas.ItemRead, status_code=status.HTTP_201_CREATED)
async def upload_item_public(
    image: UploadFile,
    background_tasks: BackgroundTasks,
    finder_user_id: int = Form(...),
    box_id : int = Form(...),
    description: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """
    Public upload endpoint:
    - Accepts image, finder_user_id, and optional description.
    - Checks lighting quality.
    - Generates AI caption using Gemini.
    - Saves item in DB and schedules embedding creation.
    """

    filename = secure_filename(image.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    # Save uploaded image
    with open(filepath, "wb") as buffer:
        buffer.write(await image.read())
        
    public_url = f"http://127.0.0.1:8000/uploads/{filename}"

    # Validate lighting
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

    # Generate caption using Gemini
    custom_prompt = (
        "Output as: Color: <…>; Type: <…>; Material: <…>; Features: <…>; Optional: Brand/Markings: <…>."
    )
    gemini_caption = generate_caption_with_gemini(filepath, prompt=custom_prompt)
    combined_caption = f"{description}. {gemini_caption}" if description else gemini_caption
    
    img_emb = get_image_embedding(filepath).detach().cpu().numpy().flatten().tolist()
    desc_emb = get_text_embedding(combined_caption).detach().cpu().numpy().flatten().tolist()

    # Save new item to DB
    new_item = models.Item(
        gemini_description=gemini_caption,
        description=combined_caption,
        image_embedding=json.dumps(img_emb),  # store as JSON string
        description_embedding=json.dumps(desc_emb),
        image_url=public_url,
        status="active", 
        finder_user_id=finder_user_id,
    )

    db.add(new_item)
    db.flush()  # so item_id becomes available

    db.commit()
    db.refresh(new_item)

    box = db.query(models.Box).filter(models.Box.box_id == box_id).first()
    if not box:
        raise HTTPException(status_code=404, detail=f"Box {box_id} not found")

    if not box.status:
        raise HTTPException(status_code=409, detail=f"Box {box_id} is disabled")

    # Open box and create a case for the uploaded item
    box.last_accessed = datetime.utcnow()
    box.door_status = True

    new_case = models.Case(
        item_id=new_item.item_id,
        box_id=box.box_id,
        status="pending",   #stored
        created_at=datetime.utcnow(),
    )
    db.add(new_case)
    db.commit()

    return new_item


@public_router.post("/query", status_code=status.HTTP_200_OK)
async def query_items_public(
    description: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Public query endpoint:
    - Accepts a text description.
    - Searches for the top 3 most similar active items (status='active').
    - Uses both image and description embeddings.
    - Only returns items with similarity > 0.4.
    """
    # Generate query embedding
    query_emb = get_text_embedding(description).detach().cpu().numpy().flatten()

    # Get all active items from DB
    items = db.query(models.Item).filter(models.Item.status == "active").all()
    if not items:
        raise HTTPException(status_code=404, detail="No active items found")

    results = []
    for item in items:
        try:
            img_score = 0.0
            desc_score = 0.0

            # Compare with image embedding
            if item.image_embedding:
                img_emb = np.array(json.loads(item.image_embedding), dtype=np.float32)
                img_score = float(np.dot(query_emb, img_emb))

            # Compare with description embedding
            if item.description_embedding:
                desc_emb = np.array(json.loads(item.description_embedding), dtype=np.float32)
                desc_score = float(np.dot(query_emb, desc_emb))

            # Weighted average (favor description more)
            final_score = (0.6 * desc_score + 0.4 * img_score) if desc_score != 0 else img_score

            # Keep only those above threshold
            if final_score > 0.45:
                results.append({
                    "item_id": item.item_id,
                    "description": item.description,
                    "gemini_description": item.gemini_description,
                    "image_url": item.image_url,
                    "score": round(final_score, 4),
                })
        except Exception:
            continue

    # Sort by descending similarity and take top 3
    results.sort(key=lambda x: x["score"], reverse=True)
    top_results = results[:3]

    if not top_results:
        raise HTTPException(status_code=404, detail="No similar items found (similarity > 0.4)")

    return {"results": top_results}


@public_router.post("/claim", response_model=schemas.CaseRead, status_code=status.HTTP_200_OK)
def claim_item(payload: schemas.CaseCreatePayload, db: Session = Depends(get_db)):
    """
    Claim an item by updating the existing case.
    Sets status to 'claimed'.
    """

    # Check if item exists
    item = db.query(models.Item).filter(models.Item.item_id == payload.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Check if receiver exists
    receiver = db.query(models.User).filter(models.User.user_id == payload.reciver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    # ✅ find existing case
    case = db.query(models.Case).filter(models.Case.item_id == payload.item_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found for this item")

    # ✅ update item status
    item.status = "claimed"
    db.add(item)

    # ✅ update case
    case.status = "claimed"
    case.reciver_id = payload.reciver_id

    db.commit()
    db.refresh(case)

    return case


@public_router.post("/cancel", response_model=schemas.CaseRead, status_code=status.HTTP_200_OK)
def cancel_case(payload: schemas.CaseCancelPayload, db: Session = Depends(get_db)):
    """
    Cancel a claimed case:
    - Sets case.status = 'available'
    - Sets item.status = 'active'
    - Updates case_close_at to now
    """
    # --- Find case ---
    case = db.query(models.Case).filter(models.Case.found_id == payload.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # --- Find item ---
    item = db.query(models.Item).filter(models.Item.item_id == payload.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # --- Update records ---
    case.status = "available"
    case.reciver_id = None
    item.status = "active"

    db.add_all([case, item])
    db.commit()
    db.refresh(case)

    return case


import threading

@public_router.post("/collect", response_model=schemas.CaseRead, status_code=status.HTTP_200_OK)
def collect_item(payload: schemas.CaseCollectPayload, db: Session = Depends(get_db)):
    """
    Marks a box door status as active (True) for collection. 
    Starts a 5-minute timer. 
    If the case status is not marked as "collected" after 5 minutes,
    automatically resets the box, case, and item.
    """

    # --- Find records ---
    box = db.query(models.Box).filter(models.Box.box_id == payload.box_id).first()
    case = db.query(models.Case).filter(models.Case.found_id == payload.case_id).first()
    item = db.query(models.Item).filter(models.Item.item_id == payload.item_id).first()

    if not box:
        raise HTTPException(status_code=404, detail="Box not found")
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # --- Activate box ---
    box.status = True
    db.commit()

    # --- Define background function ---
    def timeout_reset():
        with db.bind.connect() as conn:
            # Refresh states from database
            case_status = conn.execute(
                models.Case.__table__.select().where(models.Case.found_id == payload.case_id)
            ).fetchone()

            if case_status and case_status.status != "collected":
                # Reset everything if not collected
                conn.execute(
                    models.Box.__table__.update()
                    .where(models.Box.box_id == payload.box_id)
                    .values(status=False)
                )
                conn.execute(
                    models.Case.__table__.update()
                    .where(models.Case.found_id == payload.case_id)
                    .values(status="available")
                )
                conn.execute(
                    models.Item.__table__.update()
                    .where(models.Item.item_id == payload.item_id)
                    .values(status="active")
                )
                conn.commit()

    # --- Start timer thread (5 minutes = 300 seconds) ---
    timer = threading.Timer(300, timeout_reset)
    timer.start()

    return case


@public_router.post("/collected-successfully", status_code=status.HTTP_200_OK)
def collected_successfully(payload: schemas.CaseCollectedPayload, db: Session = Depends(get_db)):
    """
    Marks an item as successfully collected:
      - Closes box door
      - Updates case and item statuses
      - Increments receiver's items_lost count
    """

    # 1️⃣ Retrieve records
    case = db.query(models.Case).filter(models.Case.found_id == payload.case_id).first()
    box = db.query(models.Box).filter(models.Box.box_id == payload.box_id).first()
    item = db.query(models.Item).filter(models.Item.item_id == payload.item_id).first()

    if not case or not box or not item:
        raise HTTPException(status_code=404, detail="Case, Box, or Item not found")

    # 2️⃣ Retrieve receiver (the user who claimed the item)
    receiver = db.query(models.User).filter(models.User.user_id == case.reciver_id).first()

    # 3️⃣ Update records
    box.door_status = False
    case.status = "collected"
    case.case_close_at = datetime.now(timezone.utc)
    item.status = "collected"

    # 4️⃣ Update receiver stats
    if receiver:
        receiver.items_lost = (receiver.items_lost or 0) + 1

    # 5️⃣ Commit changes
    db.commit()
    db.refresh(case)

    return {
        "message": "Item collected successfully.",
        "case_id": case.found_id,
        "box_id": box.box_id,
        "item_id": item.item_id,
        "receiver_id": receiver.user_id if receiver else None,
        "receiver_items_lost": receiver.items_lost if receiver else None,
    }
