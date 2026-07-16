from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.v1 import sync_service

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/status")
def sync_status(db: Session = Depends(get_db)):
    return sync_service.get_status(db)


@router.post("/refresh")
def sync_refresh(response: Response, trigger: str = "manual", force: bool = False,
                 db: Session = Depends(get_db)):
    result = sync_service.refresh(db, trigger=trigger, force=force)
    outcome = result["outcome"]
    if outcome == "already_running":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Ya hay una actualización en curso")
    if outcome == "n8n_down":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="n8n apagado")
    if outcome == "skipped_fresh":
        response.status_code = status.HTTP_200_OK
        return result
    # started
    response.status_code = status.HTTP_202_ACCEPTED
    return result
