from tests._helpers import TOKEN


def _ingest_day(client, reach, captured):
    payload = {
        "account": {"ig_user_id": "ig-1", "name": "Pleniq"},
        "captured_at": captured,
        "reels": [{
            "ig_media_id": "media-1", "media_product_type": "REELS",
            "timestamp": "2026-07-01T12:00:00+00:00",
            "metrics": {"reach": reach, "views": 5000, "likes": 300, "comments": 20,
                        "saved": 80, "shares": 40, "total_interactions": 440,
                        "ig_reels_avg_watch_time": 8200, "ig_reels_video_view_total_time": 41000},
        }],
    }
    assert client.post("/api/v1/ingest/instagram", json=payload,
                       headers={"X-Ingest-Token": TOKEN}).status_code == 200


def test_history_has_one_row_per_day_ordered(client, db):
    _ingest_day(client, reach=1000, captured="2026-07-14T06:00:00+00:00")
    _ingest_day(client, reach=2000, captured="2026-07-15T06:00:00+00:00")
    rid = client.get("/api/v1/reels").json()[0]["id"]
    hist = client.get(f"/api/v1/reels/{rid}/history").json()
    assert len(hist) == 2
    assert hist[0]["snapshot_date"] == "2026-07-14"
    assert hist[1]["snapshot_date"] == "2026-07-15"
    assert hist[0]["reach"] == 1000
    assert hist[1]["reach"] == 2000
    assert abs(hist[1]["engagement_rate"] - 0.22) < 1e-6  # 440/2000


def test_history_empty_for_unknown_reel(client, db):
    assert client.get("/api/v1/reels/no-existe/history").json() == []
