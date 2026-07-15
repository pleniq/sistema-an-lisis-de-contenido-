from typing import Optional

from sqlalchemy.orm import Session

from app.models import Reel
from app.repositories.reel_repository import (
    list_reels_with_latest, get_reel_with_latest, list_snapshots,
)
from app.repositories import label_repository as labels
from app.schemas.reel import ReelRow, ReelUpdate, SnapshotRow

MANUAL_TEXT_FIELDS = {"titulo", "guion"}


def get_reels(db: Session) -> list[ReelRow]:
    return [ReelRow(**row) for row in list_reels_with_latest(db)]


def get_reel(db: Session, reel_id: str) -> Optional[ReelRow]:
    row = get_reel_with_latest(db, reel_id)
    return ReelRow(**row) if row else None


def get_reel_history(db: Session, reel_id: str) -> list[SnapshotRow]:
    return [SnapshotRow(**row) for row in list_snapshots(db, reel_id)]


def update_reel(db: Session, reel_id: str, update: ReelUpdate) -> Optional[ReelRow]:
    reel = db.get(Reel, reel_id)
    if reel is None:
        return None

    provided = update.model_dump(exclude_unset=True)

    for field in MANUAL_TEXT_FIELDS & provided.keys():
        setattr(reel, field, provided[field])

    for dimension in labels.DIMENSIONS.keys() & provided.keys():
        _, fk_col = labels.DIMENSIONS[dimension]
        value = provided[dimension]
        if value is None or not str(value).strip():
            setattr(reel, fk_col, None)
        else:
            label = labels.get_or_create(db, reel.account_id, dimension, str(value))
            setattr(reel, fk_col, label.id)

    db.commit()
    return ReelRow(**get_reel_with_latest(db, reel_id))
