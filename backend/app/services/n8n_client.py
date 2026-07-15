"""Cliente fino hacia n8n. Aislado para poder mockearlo en tests."""
import httpx

from app.core.config import get_settings


def ping_n8n() -> bool:
    """True si el webhook de ping de n8n responde 200 dentro del timeout.
    Si no hay URL configurada, n8n se considera apagado (False) sin llamar."""
    settings = get_settings()
    url = settings.LAB_N8N_PING_WEBHOOK_URL
    if not url:
        return False
    try:
        resp = httpx.get(url, timeout=settings.LAB_N8N_PING_TIMEOUT_SECONDS)
        return resp.status_code == 200
    except httpx.HTTPError:
        return False


def trigger_ingest(run_id: str) -> None:
    """Dispara el webhook de ingesta de n8n (fire-and-forget corto).
    n8n hará el trabajo pesado y posteará el batch a /ingest/instagram."""
    settings = get_settings()
    url = settings.LAB_N8N_INGEST_WEBHOOK_URL
    if not url:
        return
    try:
        httpx.post(url, json={"run_id": run_id}, timeout=settings.LAB_N8N_PING_TIMEOUT_SECONDS)
    except httpx.HTTPError:
        # el disparo puede fallar; el run queda 'running' y lo reapea la guarda de stuck
        pass
