from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.v1.config import MetaConfigIn, MetaConfigStatus
from app.services.v1 import config_service

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/meta", response_model=MetaConfigStatus)
def get_meta(db: Session = Depends(get_db)):
    """Estado de la conexión con Meta (nunca devuelve el token)."""
    return config_service.get_status(db)


@router.put("/meta", response_model=MetaConfigStatus)
def put_meta(body: MetaConfigIn, db: Session = Depends(get_db)):
    """Guarda/actualiza el token. Con app_id + app_secret lo canjea a 60 días."""
    return config_service.save(db, body)
