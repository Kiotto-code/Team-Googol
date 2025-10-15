import os
import json
from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException
from sqlalchemy.orm import Session
from werkzeug.utils import secure_filename

from ..db import get_db
from .. import models, schemas
from ..dependencies.auth import require_roles
from ..utils.clip_utils import get_image_embedding, get_text_embedding, UPLOAD_FOLDER
from ..utils.upload_utils import is_lighting_good
from ..utils.caption_utils import generate_caption_with_gemini

admin_router = APIRouter(
    prefix="/api/v1/admin/items",
    tags=["admin-items"],
    dependencies=[Depends(require_roles("admin", "staff"))],
)
public_router = APIRouter(prefix="/api/v1/items", tags=["items"])

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@admin_router.post("/", response_model=schemas.ItemRead)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    db_item = models.Item(**item.model_dump(exclude_unset=True))
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def _list_items(db: Session) -> list[models.Item]:
    return db.query(models.Item).order_by(models.Item.item_id.desc()).all()


@admin_router.get("/", response_model=list[schemas.ItemRead])
def list_items(db: Session = Depends(get_db)):
    return _list_items(db)


@public_router.get("/", response_model=list[schemas.ItemRead])
def list_items_public(db: Session = Depends(get_db)):
    return _list_items(db)


@admin_router.post("/upload", response_model=schemas.ItemRead)
async def upload_item(
    image: UploadFile,
    finder_user_id: int = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db),
):
    """Uploads an image, validates lighting, generates caption + embeddings, and stores item in DB."""

    # --- Save file ---
    filename = secure_filename(image.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, "wb") as buffer:
        buffer.write(await image.read())

    # --- Lighting check ---
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

    # --- Generate caption using Gemini ---
    custom_prompt = (
        "Output as: Color: <…>; Type: <…>; Material: <…>; Features: <…>; Optional: Brand/Markings: <…>."
    )
    gemini_caption = generate_caption_with_gemini(filepath, prompt=custom_prompt)

    # Combine user and AI caption
    combined_caption = f"{description}. {gemini_caption}" if description else gemini_caption

    # --- Compute embeddings ---
    img_emb = get_image_embedding(filepath).detach().cpu().numpy().flatten().tolist()
    desc_emb = get_text_embedding(combined_caption).detach().cpu().numpy().flatten().tolist()

    # --- Save item to database ---
    new_item = models.Item(
        gemini_description=gemini_caption,
        description=combined_caption,
        image_url=filepath,
        image_embedding=json.dumps(img_emb),
        description_embedding=json.dumps(desc_emb),
        status="uploaded",
        finder_user_id=finder_user_id,
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item
