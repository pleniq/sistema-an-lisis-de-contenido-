from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.label_repository import DIMENSIONS
from app.schemas.analysis import AnalysisRow
from app.services.analysis_service import get_analysis

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("", response_model=list[AnalysisRow])
def analysis(group_by: str, db: Session = Depends(get_db)):
    if group_by not in DIMENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"group_by inválido. Opciones: {', '.join(DIMENSIONS.keys())}",
        )
    return get_analysis(db, group_by)
