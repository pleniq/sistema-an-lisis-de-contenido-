from datetime import datetime, timezone
from app.schemas.v1.ingest import IngestBatch, IngestAccount, IngestReel, IngestMetrics
from app.services.v1.ingest_service import ingest_batch


def test_reels_returns_latest_metrics_and_ratios(client, db):
    ingest_batch(db, IngestBatch(
        account=IngestAccount(ig_user_id="ig-1", name="Pleniq"),
        captured_at=datetime(2026, 7, 15, 6, tzinfo=timezone.utc),
        reels=[IngestReel(ig_media_id="media-1", media_product_type="REELS",
                          timestamp=datetime(2026, 7, 10, tzinfo=timezone.utc),
                          metrics=IngestMetrics(reach=1000, views=5000, likes=300,
                                                comments=20, saved=80, shares=40,
                                                total_interactions=440,
                                                ig_reels_avg_watch_time=8200,
                                                ig_reels_video_view_total_time=41000))],
    ))
    resp = client.get("/api/v1/reels")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    row = data[0]
    assert row["reach"] == 1000
    assert row["engagement_rate"] == 0.44   # 440/1000
    assert row["save_rate"] == 0.08         # 80/1000
    assert abs(row["avg_watch_time_sec"] - 8.2) < 1e-6
