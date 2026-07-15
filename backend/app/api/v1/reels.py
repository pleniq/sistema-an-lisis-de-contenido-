from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.reel import ReelRow, ReelUpdate
from app.services.reel_service import get_reels, get_reel, update_reel

router = APIRouter(prefix="/reels", tags=["reels"])


@router.get("", response_model=list[ReelRow])
def list_reels(db: Session = Depends(get_db)):
    return get_reels(db)


@router.get("/{reel_id}", response_model=ReelRow)
def read_reel(reel_id: str, db: Session = Depends(get_db)):
    row = get_reel(db, reel_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Reel no encontrado")
    return row


@router.patch("/{reel_id}", response_model=ReelRow)
def patch_reel(reel_id: str, update: ReelUpdate, db: Session = Depends(get_db)):
    row = update_reel(db, reel_id, update)
    if row is None:
        raise HTTPException(status_code=404, detail="Reel no encontrado")
    return row
