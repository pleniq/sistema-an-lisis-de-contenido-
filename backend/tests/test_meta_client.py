import pytest

from app.services.v1 import meta_client as mc


# --- detección de error de auth ---
def test_is_auth_error():
    assert mc._is_auth_error({"error": {"code": 190}})
    assert mc._is_auth_error({"error": {"type": "OAuthException"}})
    assert not mc._is_auth_error({"error": {"code": 4, "type": "Throttle"}})
    assert not mc._is_auth_error({})


# --- _check: swallow de errores no-auth, precedencia del auth ---
def test_check_swallows_non_auth_when_allowed():
    assert mc._check({"error": {"code": 100, "message": "bad metric"}}, allow_error=True) == {"data": []}


def test_check_raises_non_auth_when_not_allowed():
    with pytest.raises(mc.MetaError):
        mc._check({"error": {"code": 100, "message": "bad"}}, allow_error=False)


def test_check_raises_auth_even_when_allowed():
    with pytest.raises(mc.MetaAuthError):
        mc._check({"error": {"code": 190}}, allow_error=True)


# --- exchange ---
def test_exchange_result_parses():
    tok, exp = mc._exchange_result({"access_token": "long", "expires_in": 5184000})
    assert tok == "long" and exp == 5184000


def test_exchange_result_auth_error():
    with pytest.raises(mc.MetaAuthError):
        mc._exchange_result({"error": {"code": 190, "message": "bad"}})


# --- fetch_batch: paginación + filtro de reels + parseo de insights ---
def test_fetch_batch_paginates_filters_and_parses(monkeypatch):
    page1 = {
        "data": [{"id": "m1", "media_product_type": "REELS", "permalink": "p1",
                  "caption": "c1", "timestamp": "2026-07-01T00:00:00+0000"}],
        "paging": {"next": "NEXT_URL"},
    }
    page2 = {"data": [{"id": "m2", "media_product_type": "REELS"},
                      {"id": "x", "media_product_type": "IMAGE"}]}  # el IMAGE se descarta
    insights = {
        "m1": {"data": [{"name": "reach", "values": [{"value": 100}]},
                        {"name": "views", "values": [{"value": 200}]}]},
        "m2": {"data": [{"name": "reach", "values": [{"value": 50}]}]},
    }

    def fake_get(url, params, token, allow_error=False):
        if "/media" in url:
            return page1
        if "/insights" in url:
            return insights[url.split("/")[-2]]
        return {}

    monkeypatch.setattr(mc, "_get", fake_get)
    monkeypatch.setattr(mc, "_get_url", lambda url: page2)

    batch = mc.fetch_batch("tok", "ig-1", "Pleniq")
    assert batch.account.ig_user_id == "ig-1"
    assert sorted(r.ig_media_id for r in batch.reels) == ["m1", "m2"]
    by = {r.ig_media_id: r for r in batch.reels}
    assert by["m1"].metrics.reach == 100
    assert by["m1"].metrics.views == 200
    assert by["m2"].metrics.reach == 50
    assert by["m2"].metrics.likes is None  # métrica ausente → None


def test_fetch_batch_auth_error_propagates(monkeypatch):
    def boom(url, params, token, allow_error=False):
        raise mc.MetaAuthError("expired")
    monkeypatch.setattr(mc, "_get", boom)
    with pytest.raises(mc.MetaAuthError):
        mc.fetch_batch("tok", "ig-1")
