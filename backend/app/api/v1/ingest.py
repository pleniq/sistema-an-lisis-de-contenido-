import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.schemas.v1.ingest import IngestBatch
from app.services.v1.ingest_service import ingest_batch

router = APIRouter(prefix="/ingest", tags=["ingest"])


def _check_token(x_ingest_token: str | None = Header(default=None)):
    expected = get_settings().LAB_INGEST_TOKEN
    # comparación constant-time para evitar timing side-channel
    if not secrets.compare_digest(x_ingest_token or "", expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de ingesta inválido")


@router.post("/instagram", status_code=status.HTTP_200_OK, dependencies=[Depends(_check_token)])
def ingest_instagram(batch: IngestBatch, db: Session = Depends(get_db)):
    return ingest_batch(db, batch)
