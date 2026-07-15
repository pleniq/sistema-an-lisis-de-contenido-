from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import IngestRun, Account


def _now() -> datetime:
    return datetime.now(timezone.utc)


def reap_stuck_runs(db: Session, stuck_minutes: int) -> int:
    """Marca como 'error' las corridas 'running' más viejas que el umbral
    (la máquina se apagó a mitad). Devuelve cuántas reapeó."""
    cutoff = _now() - timedelta(minutes=stuck_minutes)
    stuck = (db.query(IngestRun)
               .filter(IngestRun.status == "running", IngestRun.started_at < cutoff)
               .all())
    for run in stuck:
        run.status = "error"
        run.finished_at = _now()
        run.error_detail = f"reapeada por stuck (> {stuck_minutes} min sin cerrar)"
    if stuck:
        db.commit()
    return len(stuck)


def get_active_run(db: Session) -> Optional[IngestRun]:
    """Corrida 'running' vigente (asume que ya se reapearon las colgadas)."""
    return (db.query(IngestRun)
              .filter(IngestRun.status == "running")
              .order_by(IngestRun.started_at.desc())
              .first())


def create_run(db: Session, account_id: Optional[str], trigger: str) -> IngestRun:
    run = IngestRun(account_id=account_id, trigger=trigger, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def close_run(db: Session, run_id: str, status: str, reels_processed: int = 0,
              snapshots_written: int = 0, error_detail: Optional[str] = None) -> None:
    run = db.get(IngestRun, run_id)
    if run is None:
        return
    run.status = status
    run.finished_at = _now()
    run.reels_processed = reels_processed
    run.snapshots_written = snapshots_written
    run.error_detail = error_detail
    db.commit()


def close_open_runs(db: Session, reels_processed: int, snapshots_written: int) -> None:
    """Cierra como 'ok' cualquier corrida 'running' (la ingesta llegó, el ciclo terminó).
    Best-effort: si no hay corrida abierta (ej. seed manual), no hace nada."""
    open_runs = db.query(IngestRun).filter(IngestRun.status == "running").all()
    if not open_runs:
        return
    for run in open_runs:
        run.status = "ok"
        run.finished_at = _now()
        run.reels_processed = reels_processed
        run.snapshots_written = snapshots_written
    db.commit()


def get_last_run(db: Session) -> Optional[IngestRun]:
    return db.query(IngestRun).order_by(IngestRun.started_at.desc()).first()


def get_last_synced_at(db: Session) -> Optional[datetime]:
    """Sync más reciente entre todas las cuentas (v1 tiene una sola)."""
    return db.execute(select(func.max(Account.last_synced_at))).scalar_one_or_none()
