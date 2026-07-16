"""Orquesta el sync on-demand con 3 guardas: frescura, lock y liveness de n8n.

Outcomes de refresh() → el router los mapea a HTTP:
    "skipped_fresh"   → 200  (sincronizado hace poco; "entrar sin actualizar")
    "already_running" → 409  (ya hay una corrida en curso)
    "n8n_down"        → 503  (n8n no responde el ping)
    "started"         → 202  (se creó la corrida y se disparó n8n)
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.v1 import n8n_client
from app.repositories.v1 import ingest_run_repository as runs


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize_run(run) -> Optional[dict]:
    if run is None:
        return None
    return {
        "id": run.id,
        "trigger": run.trigger,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "reels_processed": run.reels_processed,
        "snapshots_written": run.snapshots_written,
        "error_detail": run.error_detail,
    }


def get_status(db: Session) -> dict:
    settings = get_settings()
    runs.reap_stuck_runs(db, settings.LAB_SYNC_STUCK_MINUTES)
    active = runs.get_active_run(db)
    last_run = runs.get_last_run(db)
    last_synced_at = runs.get_last_synced_at(db)
    return {
        "n8n_alive": n8n_client.ping_n8n(),
        "running": active is not None,
        "last_synced_at": last_synced_at.isoformat() if last_synced_at else None,
        "last_run": _serialize_run(last_run),
    }


def _is_fresh(last_synced_at: Optional[datetime], stale_minutes: int) -> bool:
    if last_synced_at is None:
        return False
    age_seconds = (_now() - last_synced_at).total_seconds()
    return age_seconds < stale_minutes * 60


def refresh(db: Session, trigger: str = "manual", force: bool = False) -> dict:
    """Aplica las guardas y, si corresponde, crea la corrida y dispara n8n."""
    settings = get_settings()

    # Guarda 1 — frescura (el botón manual manda force=True y la saltea)
    if not force:
        last_synced_at = runs.get_last_synced_at(db)
        if _is_fresh(last_synced_at, settings.LAB_SYNC_STALE_MINUTES):
            return {"outcome": "skipped_fresh",
                    "last_synced_at": last_synced_at.isoformat() if last_synced_at else None}

    # Guarda 2 — lock (reapear colgadas primero, luego ver si hay una viva)
    runs.reap_stuck_runs(db, settings.LAB_SYNC_STUCK_MINUTES)
    if runs.get_active_run(db) is not None:
        return {"outcome": "already_running"}

    # Guarda 3 — liveness de n8n
    if not n8n_client.ping_n8n():
        return {"outcome": "n8n_down"}

    # Dispara
    run = runs.create_run(db, account_id=None, trigger=trigger)
    n8n_client.trigger_ingest(run.id)
    return {"outcome": "started", "run_id": run.id}
