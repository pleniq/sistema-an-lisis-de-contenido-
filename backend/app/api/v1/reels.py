from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.v1.reel import ReelRow, ReelUpdate, SnapshotRow
from app.schemas.v1.export import ExportRequest, ExportResponse
from app.services.v1.reel_service import get_reels, get_reel, get_reel_history, update_reel
from app.services.v1.export_service import export_reels

router = APIRouter(prefix="/reels", tags=["reels"])


@router.get("", response_model=list[ReelRow])
def list_reels(db: Session = Depends(get_db)):
    return get_reels(db)


@router.post("/export", response_model=ExportResponse)
def export(body: ExportRequest, db: Session = Depends(get_db)):
    return export_reels(db, body.reel_ids)


@router.get("/{reel_id}", response_model=ReelRow)
def read_reel(reel_id: str, db: Session = Depends(get_db)):
    row = get_reel(db, reel_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Reel no encontrado")
    return row


@router.get("/{reel_id}/history", response_model=list[SnapshotRow])
def read_reel_history(reel_id: str, db: Session = Depends(get_db)):
    return get_reel_history(db, reel_id)


@router.patch("/{reel_id}", response_model=ReelRow)
def patch_reel(reel_id: str, update: ReelUpdate, db: Session = Depends(get_db)):
    row = update_reel(db, reel_id, update)
    if row is None:
        raise HTTPException(status_code=404, detail="Reel no encontrado")
    return row
