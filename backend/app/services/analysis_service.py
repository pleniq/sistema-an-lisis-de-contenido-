from sqlalchemy.orm import Session

from app.repositories.analysis_repository import analysis_by_dimension
from app.schemas.analysis import AnalysisRow


def get_analysis(db: Session, group_by: str) -> list[AnalysisRow]:
    return [AnalysisRow(**row) for row in analysis_by_dimension(db, group_by)]
