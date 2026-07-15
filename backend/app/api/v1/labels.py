from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import label_repository as labels
from app.schemas.label import LabelOut, LabelCreate

router = APIRouter(prefix="/labels", tags=["labels"])


def _valid_or_404(dimension: str):
    if not labels.is_valid_dimension(dimension):
        raise HTTPException(status_code=404, detail=f"Dimensión desconocida: {dimension}")


@router.get("/{dimension}", response_model=list[LabelOut])
def list_dimension(dimension: str, db: Session = Depends(get_db)):
    _valid_or_404(dimension)
    return [LabelOut(id=l.id, name=l.name) for l in labels.list_labels(db, dimension)]


@router.post("/{dimension}", response_model=LabelOut, status_code=status.HTTP_201_CREATED)
def create_dimension(dimension: str, body: LabelCreate, db: Session = Depends(get_db)):
    _valid_or_404(dimension)
    account_id = labels.get_default_account_id(db)
    if account_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No hay cuenta todavía; sincronizá al menos una vez")
    label = labels.get_or_create(db, account_id, dimension, body.name)
    db.commit()
    return LabelOut(id=label.id, name=label.name)
