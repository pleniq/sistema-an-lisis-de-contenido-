from app.core.config import get_settings

TOKEN = get_settings().LAB_INGEST_TOKEN

PAYLOAD = {
    "account": {"ig_user_id": "ig-1", "name": "Pleniq"},
    "captured_at": "2026-07-15T06:00:00+00:00",
    "reels": [{
        "ig_media_id": "media-1", "permalink": "https://ig/1", "caption": "hola",
        "media_product_type": "REELS", "timestamp": "2026-07-10T12:00:00+00:00",
        "metrics": {"reach": 1000, "views": 5000, "likes": 300, "comments": 20,
                    "saved": 80, "shares": 40, "total_interactions": 440,
                    "ig_reels_avg_watch_time": 8200, "ig_reels_video_view_total_time": 41000},
    }],
}


def test_ingest_requires_token(client):
    resp = client.post("/api/v1/ingest/instagram", json=PAYLOAD)
    assert resp.status_code == 401


def test_ingest_with_token_ok(client):
    resp = client.post("/api/v1/ingest/instagram", json=PAYLOAD,
                       headers={"X-Ingest-Token": TOKEN})
    assert resp.status_code == 200
    assert resp.json() == {"reels_processed": 1, "snapshots_written": 1}
