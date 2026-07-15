from sqlalchemy.orm import Session
from app.repositories.reel_repository import list_reels_with_latest
from app.schemas.reel import ReelRow


def get_reels(db: Session) -> list[ReelRow]:
    return [ReelRow(**row) for row in list_reels_with_latest(db)]
