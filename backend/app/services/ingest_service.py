from sqlalchemy.orm import Session

from app.schemas.ingest import IngestBatch
from app.repositories.ingest_repository import upsert_account, upsert_reel, upsert_snapshot


def ingest_batch(db: Session, batch: IngestBatch) -> dict:
    account = upsert_account(db, batch.account)
    account.last_synced_at = batch.captured_at
    reels_processed = 0
    snapshots_written = 0
    for reel_data in batch.reels:
        reel = upsert_reel(db, account.id, reel_data, synced_at=batch.captured_at)
        if upsert_snapshot(db, reel, reel_data, captured_at=batch.captured_at):
            snapshots_written += 1
        reels_processed += 1
    db.commit()
    return {"reels_processed": reels_processed, "snapshots_written": snapshots_written}
