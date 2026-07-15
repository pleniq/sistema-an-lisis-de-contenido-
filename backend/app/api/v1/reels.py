from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.reel import ReelRow
from app.services.reel_service import get_reels

router = APIRouter(prefix="/reels", tags=["reels"])


@router.get("", response_model=list[ReelRow])
def list_reels(db: Session = Depends(get_db)):
    return get_reels(db)
