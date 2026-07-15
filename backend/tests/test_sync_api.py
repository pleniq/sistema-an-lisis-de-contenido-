from datetime import datetime, timedelta, timezone

import pytest

from app.models import Account, IngestRun
from app.core.config import get_settings

TOKEN = get_settings().LAB_INGEST_TOKEN


@pytest.fixture
def n8n_up(monkeypatch):
    """n8n vivo: ping True y trigger no-op (sin red)."""
    monkeypatch.setattr("app.services.n8n_client.ping_n8n", lambda: True)
    monkeypatch.setattr("app.services.n8n_client.trigger_ingest", lambda run_id: None)


@pytest.fixture
def n8n_down(monkeypatch):
    monkeypatch.setattr("app.services.n8n_client.ping_n8n", lambda: False)


def test_status_shape_when_n8n_down(client, db, n8n_down):
    resp = client.get("/api/v1/sync/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["n8n_alive"] is False
    assert body["running"] is False
    assert body["last_synced_at"] is None
    assert body["last_run"] is None


def test_refresh_503_when_n8n_down(client, db, n8n_down):
    resp = client.post("/api/v1/sync/refresh?force=true")
    assert resp.status_code == 503


def test_refresh_starts_when_n8n_alive(client, db, n8n_up):
    resp = client.post("/api/v1/sync/refresh?force=true&trigger=manual")
    assert resp.status_code == 202
    assert resp.json()["outcome"] == "started"
    # ahora hay una corrida corriendo
    status = client.get("/api/v1/sync/status").json()
    assert status["running"] is True


def test_refresh_409_when_already_running(client, db, n8n_up):
    first = client.post("/api/v1/sync/refresh?force=true")
    assert first.status_code == 202
    second = client.post("/api/v1/sync/refresh?force=true")
    assert second.status_code == 409


def test_refresh_skipped_when_fresh(client, db, n8n_up):
    # cuenta sincronizada recién → frescura corta el disparo (force=false)
    db.add(Account(ig_user_id="ig-fresh", name="Fresh",
                   last_synced_at=datetime.now(timezone.utc)))
    db.commit()
    resp = client.post("/api/v1/sync/refresh?force=false")
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "skipped_fresh"


def test_stuck_run_is_reaped(client, db, n8n_down):
    db.add(IngestRun(trigger="manual", status="running",
                     started_at=datetime.now(timezone.utc) - timedelta(minutes=20)))
    db.commit()
    status = client.get("/api/v1/sync/status").json()
    assert status["running"] is False           # reapeada
    assert status["last_run"]["status"] == "error"


def test_ingest_closes_open_run(client, db, n8n_up):
    # simula una corrida disparada
    started = client.post("/api/v1/sync/refresh?force=true")
    assert started.status_code == 202
    # llega el batch de n8n → cierra la corrida
    payload = {
        "account": {"ig_user_id": "ig-1", "name": "Pleniq"},
        "captured_at": "2026-07-15T06:00:00+00:00",
        "reels": [{
            "ig_media_id": "media-1", "media_product_type": "REELS",
            "timestamp": "2026-07-10T12:00:00+00:00",
            "metrics": {"reach": 1000, "views": 5000, "likes": 300, "comments": 20,
                        "saved": 80, "shares": 40, "total_interactions": 440,
                        "ig_reels_avg_watch_time": 8200, "ig_reels_video_view_total_time": 41000},
        }],
    }
    resp = client.post("/api/v1/ingest/instagram", json=payload,
                       headers={"X-Ingest-Token": TOKEN})
    assert resp.status_code == 200
    status = client.get("/api/v1/sync/status").json()
    assert status["running"] is False
    assert status["last_run"]["status"] == "ok"
    assert status["last_run"]["reels_processed"] == 1
