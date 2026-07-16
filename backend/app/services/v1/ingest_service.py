from sqlalchemy.orm import Session

from app.schemas.v1.ingest import IngestBatch
from app.repositories.v1.ingest_repository import upsert_account, upsert_reel, upsert_snapshot
from app.repositories.v1.ingest_run_repository import close_open_runs


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
    # Cierra la corrida abierta (si el batch llegó vía el sync async de n8n).
    close_open_runs(db, reels_processed=reels_processed, snapshots_written=snapshots_written)
    return {"reels_processed": reels_processed, "snapshots_written": snapshots_written}
