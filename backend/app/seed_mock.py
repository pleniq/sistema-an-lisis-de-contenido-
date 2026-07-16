"""Carga 3 reels mock vía el servicio de ingesta. Uso: python -m app.seed_mock"""
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.schemas.v1.ingest import IngestBatch, IngestAccount, IngestReel, IngestMetrics


def main():
    now = datetime.now(timezone.utc)
    batch = IngestBatch(
        account=IngestAccount(ig_user_id="ig-demo", name="Cuenta Demo"),
        captured_at=now,
        reels=[
            IngestReel(ig_media_id=f"media-{i}", permalink=f"https://instagram.com/reel/{i}",
                       caption=f"Reel de ejemplo {i}", media_product_type="REELS",
                       timestamp=datetime(2026, 7, i + 1, tzinfo=timezone.utc),
                       metrics=IngestMetrics(reach=1000 * i, views=5000 * i, likes=300 * i,
                                             comments=20 * i, saved=80 * i, shares=40 * i,
                                             total_interactions=440 * i,
                                             ig_reels_avg_watch_time=8000 + 200 * i,
                                             ig_reels_video_view_total_time=40000 + 1000 * i))
            for i in range(1, 4)
        ],
    )
    from app.services.v1.ingest_service import ingest_batch
    db = SessionLocal()
    try:
        res = ingest_batch(db, batch)
        print(f"Seed OK: {res}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
