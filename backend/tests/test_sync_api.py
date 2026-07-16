from datetime import datetime, timedelta, timezone

import pytest

from app.models.v1 import IngestRun, MetaConnection
from app.schemas.v1.ingest import IngestBatch, IngestAccount, IngestReel, IngestMetrics
from app.services.v1 import meta_client


def _connect(db):
    db.add(MetaConnection(access_token="tok", ig_user_id="ig-1", account_name="Pleniq", last_test_ok=True))
    db.commit()


def _fake_batch():
    return IngestBatch(
        account=IngestAccount(ig_user_id="ig-1", name="Pleniq"),
        captured_at=datetime.now(timezone.utc),
        reels=[IngestReel(ig_media_id="media-1", media_product_type="REELS",
                          timestamp=datetime(2026, 7, 10, tzinfo=timezone.utc),
                          metrics=IngestMetrics(reach=1000, views=5000, likes=300, comments=20,
                                                saved=80, shares=40, total_interactions=440,
                                                ig_reels_avg_watch_time=8200,
                                                ig_reels_video_view_total_time=41000))],
    )


@pytest.fixture
def meta_ok(monkeypatch):
    monkeypatch.setattr("app.services.v1.meta_client.fetch_batch",
                        lambda token, ig, name="Instagram": _fake_batch())


def test_status_when_not_configured(client, db):
    body = client.get("/api/v1/sync/status").json()
    assert body["configured"] is False
    assert body["token_status"] == "missing"
    assert body["running"] is False


def test_refresh_not_configured(client, db):
    resp = client.post("/api/v1/sync/refresh?force=true")
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "not_configured"


def test_refresh_ok_ingests_reels(client, db, meta_ok):
    _connect(db)
    resp = client.post("/api/v1/sync/refresh?force=true")
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "ok"
    assert resp.json()["reels_processed"] == 1
    assert len(client.get("/api/v1/reels").json()) == 1
    assert client.get("/api/v1/sync/status").json()["token_status"] == "ok"


def test_refresh_token_expired(client, db, monkeypatch):
    _connect(db)

    def _boom(token, ig, name="Instagram"):
        raise meta_client.MetaAuthError("Session has expired")
    monkeypatch.setattr("app.services.v1.meta_client.fetch_batch", _boom)

    resp = client.post("/api/v1/sync/refresh?force=true")
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "token_expired"
    assert client.get("/api/v1/sync/status").json()["token_status"] == "expired"


def test_refresh_skipped_when_fresh(client, db, meta_ok):
    _connect(db)
    client.post("/api/v1/sync/refresh?force=true")   # deja last_synced reciente
    resp = client.post("/api/v1/sync/refresh?force=false")
    assert resp.json()["outcome"] == "skipped_fresh"


def test_refresh_409_when_running(client, db, meta_ok):
    _connect(db)
    db.add(IngestRun(trigger="manual", status="running", started_at=datetime.now(timezone.utc)))
    db.commit()
    resp = client.post("/api/v1/sync/refresh?force=true")
    assert resp.status_code == 409


def test_stuck_run_is_reaped(client, db):
    db.add(IngestRun(trigger="manual", status="running",
                     started_at=datetime.now(timezone.utc) - timedelta(minutes=20)))
    db.commit()
    status = client.get("/api/v1/sync/status").json()
    assert status["running"] is False
    assert status["last_run"]["status"] == "error"
