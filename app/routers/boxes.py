from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models, schemas
from ..dependencies.auth import require_roles

router = APIRouter(
    prefix="/api/v1/admin/boxes",
    tags=["admin-boxes"],
    dependencies=[Depends(require_roles("admin", "staff"))],
)


@router.post("/", response_model=schemas.BoxRead)
def create_box(box: schemas.BoxCreate, db: Session = Depends(get_db)):
    db_box = models.Box(**box.model_dump(exclude_unset=True))
    db.add(db_box)
    db.commit()
    db.refresh(db_box)
    return db_box


@router.get("/", response_model=list[schemas.BoxRead])
def list_boxes(db: Session = Depends(get_db)):
    return db.query(models.Box).order_by(models.Box.box_id.desc()).all()
