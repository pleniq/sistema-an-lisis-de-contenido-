"""Sync on-demand: el backend jala las métricas directo de la Graph API de Meta.

refresh() es sincrónico (trae + guarda en la misma llamada; son pocos reels).
Outcomes → el router los mapea a HTTP:
    "ok"              → 200  (sincronizó; trae reels_processed / snapshots_written)
    "skipped_fresh"   → 200  (sincronizado hace poco; "entrar sin actualizar")
    "not_configured"  → 200  (falta cargar el token en Configuración)
    "token_expired"   → 200  (el token de Meta expiró; hay que pegar uno nuevo)
    "error"           → 200  (otro error de Meta; detail explica)
    "already_running" → 409  (ya hay una corrida en curso)
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.repositories.v1 import ingest_run_repository as runs
from app.repositories.v1 import config_repository
from app.services.v1 import meta_client, config_service
from app.services.v1.ingest_service import ingest_batch

logger = logging.getLogger(__name__)


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
    cfg = config_service.get_status(db)
    return {
        "running": active is not None,
        "last_synced_at": last_synced_at.isoformat() if last_synced_at else None,
        "last_run": _serialize_run(last_run),
        "configured": cfg.token_status != "missing",
        "token_status": cfg.token_status,           # ok | expired | missing
        "token_expires_at": cfg.token_expires_at.isoformat() if cfg.token_expires_at else None,
        "days_left": cfg.days_left,
        "account_name": cfg.account_name,
    }


def _is_fresh(last_synced_at: Optional[datetime], stale_minutes: int) -> bool:
    if last_synced_at is None:
        return False
    return (_now() - last_synced_at).total_seconds() < stale_minutes * 60


def refresh(db: Session, trigger: str = "manual", force: bool = False) -> dict:
    settings = get_settings()
    conn = config_repository.get_connection(db)
    if conn is None or not conn.access_token or not conn.ig_user_id:
        return {"outcome": "not_configured"}

    # Guarda 1 — frescura (el botón manual manda force=True y la saltea)
    if not force:
        last = runs.get_last_synced_at(db)
        if _is_fresh(last, settings.LAB_SYNC_STALE_MINUTES):
            return {"outcome": "skipped_fresh",
                    "last_synced_at": last.isoformat() if last else None}

    # Guarda 2 — lock
    runs.reap_stuck_runs(db, settings.LAB_SYNC_STUCK_MINUTES)
    if runs.get_active_run(db) is not None:
        return {"outcome": "already_running"}

    run = runs.create_run(db, account_id=None, trigger=trigger)
    try:
        batch = meta_client.fetch_batch(conn.access_token, conn.ig_user_id,
                                        conn.account_name or "Instagram")
        res = ingest_batch(db, batch)  # cierra la corrida abierta como 'ok'
        config_service.mark_token_ok(db)
        return {"outcome": "ok", **res}
    except meta_client.MetaAuthError as exc:
        runs.close_run(db, run.id, "error", error_detail=f"token expirado: {exc}")
        config_service.mark_token_expired(db, f"Token expirado: {exc}")
        return {"outcome": "token_expired"}
    except meta_client.MetaError as exc:
        runs.close_run(db, run.id, "error", error_detail=f"error de Meta: {exc}")
        return {"outcome": "error", "detail": "Error de la API de Meta"}
    except Exception as exc:  # inesperado: se registra en el run, no se filtra al front
        logger.exception("Error inesperado en sync/refresh")
        runs.close_run(db, run.id, "error", error_detail=str(exc))
        return {"outcome": "error", "detail": "Error inesperado al sincronizar"}
