from datetime import datetime
from sqlalchemy.orm import Session

from app.models.v1 import Account, Reel, ReelMetricSnapshot
from app.schemas.v1.ingest import IngestAccount, IngestReel


def upsert_account(db: Session, data: IngestAccount) -> Account:
    account = db.query(Account).filter(Account.ig_user_id == data.ig_user_id).one_or_none()
    if account is None:
        account = Account(ig_user_id=data.ig_user_id, name=data.name)
        db.add(account)
        db.flush()
    else:
        account.name = data.name
    return account


def upsert_reel(db: Session, account_id: str, data: IngestReel, synced_at: datetime) -> Reel:
    reel = db.query(Reel).filter(Reel.ig_media_id == data.ig_media_id).one_or_none()
    if reel is None:
        reel = Reel(account_id=account_id, ig_media_id=data.ig_media_id)
        db.add(reel)
    # SOLO campos de la API — nunca titulo/guion/labels
    reel.permalink = data.permalink
    reel.caption = data.caption
    reel.thumbnail_url = data.thumbnail_url
    reel.media_product_type = data.media_product_type
    reel.published_at = data.timestamp
    reel.last_synced_at = synced_at
    db.flush()
    return reel


def upsert_snapshot(db: Session, reel: Reel, data: IngestReel, captured_at: datetime) -> bool:
    """Devuelve True si escribió/actualizó un snapshot."""
    snap_date = captured_at.date()
    m = data.metrics
    snap = (db.query(ReelMetricSnapshot)
              .filter(ReelMetricSnapshot.reel_id == reel.id,
                      ReelMetricSnapshot.snapshot_date == snap_date)
              .one_or_none())
    if snap is None:
        snap = ReelMetricSnapshot(reel_id=reel.id, snapshot_date=snap_date)
        db.add(snap)
    snap.captured_at = captured_at
    snap.reach = m.reach
    snap.views = m.views
    snap.likes = m.likes
    snap.comments = m.comments
    snap.saved = m.saved
    snap.shares = m.shares
    snap.total_interactions = m.total_interactions
    snap.avg_watch_time_ms = m.ig_reels_avg_watch_time
    snap.total_watch_time_ms = m.ig_reels_video_view_total_time
    db.flush()
    return True
