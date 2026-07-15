"""Helpers compartidos por los tests de API (ingesta rápida de reels de ejemplo)."""
from app.core.config import get_settings

TOKEN = get_settings().LAB_INGEST_TOKEN


def _metrics(i=1):
    return {"reach": 1000 * i, "views": 5000 * i, "likes": 300 * i, "comments": 20 * i,
            "saved": 80 * i, "shares": 40 * i, "total_interactions": 440 * i,
            "ig_reels_avg_watch_time": 8000 + 200 * i,
            "ig_reels_video_view_total_time": 40000 + 1000 * i}


def ingest_reels(client, n=1):
    """Ingesta n reels de ejemplo. Devuelve la lista de reels (de GET /reels)."""
    payload = {
        "account": {"ig_user_id": "ig-1", "name": "Pleniq"},
        "captured_at": "2026-07-15T06:00:00+00:00",
        "reels": [{
            "ig_media_id": f"media-{i}", "permalink": f"https://ig/{i}",
            "caption": f"Reel {i}", "media_product_type": "REELS",
            "timestamp": f"2026-07-0{i}T12:00:00+00:00",
            "metrics": _metrics(i),
        } for i in range(1, n + 1)],
    }
    resp = client.post("/api/v1/ingest/instagram", json=payload,
                       headers={"X-Ingest-Token": TOKEN})
    assert resp.status_code == 200, resp.text
    return client.get("/api/v1/reels").json()
