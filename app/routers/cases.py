from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("/", response_model=schemas.CaseRead)
def create_case(case: schemas.CaseCreate, db: Session = Depends(get_db)):
    db_case = models.Case(**case.model_dump(exclude_unset=True))
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case


@router.get("/", response_model=list[schemas.CaseRead])
def list_cases(db: Session = Depends(get_db)):
    return db.query(models.Case).order_by(models.Case.found_id.desc()).all()
