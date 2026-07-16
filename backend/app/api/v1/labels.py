from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.v1 import label_repository as labels
from app.schemas.v1.label import LabelOut, LabelCreate, LabelRename, LabelRenameResult

router = APIRouter(prefix="/labels", tags=["labels"])


def _valid_or_404(dimension: str):
    if not labels.is_valid_dimension(dimension):
        raise HTTPException(status_code=404, detail=f"Dimensión desconocida: {dimension}")


@router.get("/{dimension}", response_model=list[LabelOut])
def list_dimension(dimension: str, db: Session = Depends(get_db)):
    _valid_or_404(dimension)
    return [LabelOut(id=l.id, name=l.name, count=c)
            for l, c in labels.list_labels_with_counts(db, dimension)]


@router.post("/{dimension}", response_model=LabelOut, status_code=status.HTTP_201_CREATED)
def create_dimension(dimension: str, body: LabelCreate, db: Session = Depends(get_db)):
    _valid_or_404(dimension)
    account_id = labels.get_default_account_id(db)
    if account_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No hay cuenta todavía; sincronizá al menos una vez")
    label = labels.get_or_create(db, account_id, dimension, body.name)
    db.commit()
    return LabelOut(id=label.id, name=label.name,
                    count=labels.count_reels(db, dimension, label.id))


@router.patch("/{dimension}/{label_id}", response_model=LabelRenameResult)
def rename_dimension(dimension: str, label_id: str, body: LabelRename, db: Session = Depends(get_db)):
    _valid_or_404(dimension)
    label, merged = labels.rename_label(db, dimension, label_id, body.name)
    if label is None:
        raise HTTPException(status_code=404, detail="Etiqueta no encontrada")
    return LabelRenameResult(id=label.id, name=label.name, merged=merged)


@router.delete("/{dimension}/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dimension(dimension: str, label_id: str, db: Session = Depends(get_db)):
    _valid_or_404(dimension)
    if not labels.delete_label(db, dimension, label_id):
        raise HTTPException(status_code=404, detail="Etiqueta no encontrada")
