from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.v1 import sync_service

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/status")
def sync_status(db: Session = Depends(get_db)):
    return sync_service.get_status(db)


@router.post("/refresh")
def sync_refresh(trigger: str = "manual", force: bool = False, db: Session = Depends(get_db)):
    result = sync_service.refresh(db, trigger=trigger, force=force)
    if result["outcome"] == "already_running":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Ya hay una actualización en curso")
    # ok / skipped_fresh / not_configured / token_expired / error → 200 con el outcome en el body
    return result
