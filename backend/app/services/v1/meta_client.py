"""Cliente directo de la Graph API de Meta.

El backend jala las métricas de Instagram por acá (antes lo hacía n8n). Aísla
la Graph API para poder mockearla en tests y detectar el token expirado.
"""
from datetime import datetime, timezone

import httpx

from app.schemas.v1.ingest import IngestBatch, IngestAccount, IngestReel, IngestMetrics

GRAPH = "https://graph.facebook.com/v21.0"
REEL_METRICS = (
    "reach,views,likes,comments,saved,shares,total_interactions,"
    "ig_reels_avg_watch_time,ig_reels_video_view_total_time"
)
MEDIA_FIELDS = "id,media_type,media_product_type,permalink,caption,thumbnail_url,timestamp"


class MetaAuthError(Exception):
    """Token inválido o expirado (Graph API code 190 / OAuthException)."""


class MetaError(Exception):
    """Otro error de la Graph API."""


def _is_auth_error(payload: dict) -> bool:
    err = payload.get("error", {})
    return err.get("code") in (190, 102, 463, 467) or err.get("type") == "OAuthException"


def _raise(payload: dict):
    msg = payload.get("error", {}).get("message", "Error de Meta")
    if _is_auth_error(payload):
        raise MetaAuthError(msg)
    raise MetaError(msg)


def _get(url: str, params: dict, token: str, allow_error: bool = False) -> dict:
    resp = httpx.get(url, params={**params, "access_token": token}, timeout=30)
    data = resp.json()
    if "error" in data:
        if _is_auth_error(data):
            raise MetaAuthError(data["error"].get("message", "Token inválido o expirado"))
        if allow_error:
            return {"data": []}
        _raise(data)
    return data


def test_token(token: str) -> dict:
    """Devuelve {id, name} si el token es válido; MetaAuthError si expiró."""
    return _get(f"{GRAPH}/me", {"fields": "id,name"}, token)


def exchange_long_lived(app_id: str, app_secret: str, short_token: str) -> tuple[str, int]:
    """Cambia un token (corto o largo) por uno long-lived (~60 días).
    Devuelve (token, expires_in_segundos)."""
    resp = httpx.get(f"{GRAPH}/oauth/access_token", params={
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_token,
    }, timeout=30)
    data = resp.json()
    if "error" in data:
        _raise(data)
    return data["access_token"], int(data.get("expires_in", 0))


def fetch_batch(token: str, ig_user_id: str, account_name: str = "Instagram") -> IngestBatch:
    """Trae todos los Reels + sus insights y arma el batch para la ingesta."""
    media = _get(f"{GRAPH}/{ig_user_id}/media", {"fields": MEDIA_FIELDS, "limit": 100}, token)
    reels = [m for m in media.get("data", []) if m.get("media_product_type") == "REELS"]

    out: list[IngestReel] = []
    for m in reels:
        ins = _get(f"{GRAPH}/{m['id']}/insights", {"metric": REEL_METRICS}, token, allow_error=True)
        mm: dict = {}
        for d in ins.get("data", []):
            vals = d.get("values", [])
            mm[d["name"]] = vals[0]["value"] if vals else None
        out.append(IngestReel(
            ig_media_id=m["id"], permalink=m.get("permalink"), caption=m.get("caption"),
            thumbnail_url=m.get("thumbnail_url"), media_product_type="REELS", timestamp=m.get("timestamp"),
            metrics=IngestMetrics(
                reach=mm.get("reach"), views=mm.get("views"), likes=mm.get("likes"),
                comments=mm.get("comments"), saved=mm.get("saved"), shares=mm.get("shares"),
                total_interactions=mm.get("total_interactions"),
                ig_reels_avg_watch_time=mm.get("ig_reels_avg_watch_time"),
                ig_reels_video_view_total_time=mm.get("ig_reels_video_view_total_time"),
            ),
        ))

    return IngestBatch(
        account=IngestAccount(ig_user_id=ig_user_id, name=account_name),
        captured_at=datetime.now(timezone.utc),
        reels=out,
    )
