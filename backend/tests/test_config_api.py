import pytest


def test_get_config_missing(client, db):
    body = client.get("/api/v1/config/meta").json()
    assert body["connected"] is False
    assert body["token_status"] == "missing"


def test_put_config_with_app_secret_exchanges_and_connects(client, db, monkeypatch):
    monkeypatch.setattr("app.services.v1.meta_client.exchange_long_lived",
                        lambda app_id, secret, tok: ("long-token", 5184000))  # ~60 días
    monkeypatch.setattr("app.services.v1.meta_client.test_token",
                        lambda tok: {"id": "1", "name": "Pleniq"})
    resp = client.put("/api/v1/config/meta", json={
        "access_token": "short", "ig_user_id": "178", "account_name": "Pleniq",
        "app_id": "app", "app_secret": "sec",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["connected"] is True
    assert body["token_status"] == "ok"
    assert body["long_lived"] is True
    assert body["days_left"] is not None and body["days_left"] > 50


def test_put_config_expired_token(client, db, monkeypatch):
    from app.services.v1 import meta_client

    def _boom(tok):
        raise meta_client.MetaAuthError("expired")
    monkeypatch.setattr("app.services.v1.meta_client.test_token", _boom)
    resp = client.put("/api/v1/config/meta", json={"access_token": "bad", "ig_user_id": "178"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_status"] == "expired"
    assert body["connected"] is False
    assert body["last_error"] is not None
