from datetime import datetime, timezone

from app.models.v1 import Reel, ReelMetricSnapshot
from app.schemas.v1.ingest import IngestBatch, IngestAccount, IngestReel, IngestMetrics
from app.services.v1.ingest_service import ingest_batch


def _batch(reach=1000, captured="2026-07-15T06:00:00+00:00"):
    return IngestBatch(
        account=IngestAccount(ig_user_id="ig-1", name="Pleniq"),
        captured_at=datetime.fromisoformat(captured),
        reels=[IngestReel(
            ig_media_id="media-1", permalink="https://ig/1",
            caption="hola", media_product_type="REELS",
            timestamp=datetime(2026, 7, 10, tzinfo=timezone.utc),
            metrics=IngestMetrics(reach=reach, views=5000, likes=300, comments=20,
                                  saved=80, shares=40, total_interactions=440,
                                  ig_reels_avg_watch_time=8200,
                                  ig_reels_video_view_total_time=41000),
        )],
    )


def test_ingest_creates_reel_and_snapshot(db):
    res = ingest_batch(db, _batch())
    assert res == {"reels_processed": 1, "snapshots_written": 1}
    assert db.query(Reel).count() == 1
    assert db.query(ReelMetricSnapshot).count() == 1


def test_ingest_same_day_is_idempotent(db):
    ingest_batch(db, _batch(reach=1000))
    ingest_batch(db, _batch(reach=2500))  # misma media, mismo día
    assert db.query(Reel).count() == 1
    assert db.query(ReelMetricSnapshot).count() == 1  # NO duplica
    snap = db.query(ReelMetricSnapshot).one()
    assert snap.reach == 2500  # actualizó al último valor


def test_ingest_does_not_overwrite_manual_fields(db):
    ingest_batch(db, _batch())
    reel = db.query(Reel).one()
    reel.titulo = "Mi título"
    reel.guion = "Mi guion"
    db.commit()
    ingest_batch(db, _batch(reach=9999))  # re-sync
    reel = db.query(Reel).one()
    assert reel.titulo == "Mi título"  # la ingesta NO lo pisó
    assert reel.guion == "Mi guion"
