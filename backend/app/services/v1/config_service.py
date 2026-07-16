from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.v1 import MetaConnection
from app.repositories.v1 import config_repository as repo
from app.services.v1 import meta_client
from app.schemas.v1.config import MetaConfigIn, MetaConfigStatus


def _now() -> datetime:
    return datetime.now(timezone.utc)


def token_status(conn: Optional[MetaConnection]) -> str:
    if conn is None or not conn.access_token:
        return "missing"
    if conn.token_expires_at and conn.token_expires_at <= _now():
        return "expired"
    if not conn.last_test_ok and conn.last_error:
        return "expired"
    return "ok"


def _to_status(conn: Optional[MetaConnection]) -> MetaConfigStatus:
    st = token_status(conn)
    days = None
    if conn and conn.token_expires_at:
        days = max(0, (conn.token_expires_at - _now()).days)
    return MetaConfigStatus(
        connected=st == "ok",
        token_status=st,
        ig_user_id=conn.ig_user_id if conn else None,
        account_name=conn.account_name if conn else None,
        token_expires_at=conn.token_expires_at if conn else None,
        days_left=days,
        long_lived=bool(conn and conn.token_expires_at),
        last_error=conn.last_error if conn else None,
    )


def get_status(db: Session) -> MetaConfigStatus:
    return _to_status(repo.get_connection(db))


def save(db: Session, data: MetaConfigIn) -> MetaConfigStatus:
    """Guarda el token. Si vienen app_id + app_secret, lo canjea a long-lived (~60 días).
    Siempre prueba el token y registra el resultado."""
    token = data.access_token.strip()
    expires_at = None
    error: Optional[str] = None
    ok = False

    if data.app_id and data.app_secret:
        try:
            token, expires_in = meta_client.exchange_long_lived(
                data.app_id.strip(), data.app_secret.strip(), token)
            if expires_in:
                expires_at = _now() + timedelta(seconds=expires_in)
        except meta_client.MetaError as exc:
            error = f"No se pudo canjear el token largo: {exc}"

    if error is None:
        try:
            meta_client.test_token(token)
            ok = True
        except meta_client.MetaAuthError as exc:
            error = f"Token inválido o expirado: {exc}"
        except meta_client.MetaError as exc:
            error = f"Error probando el token: {exc}"

    fields = dict(access_token=token, last_test_ok=ok, last_error=error, token_expires_at=expires_at)
    if data.ig_user_id:
        fields["ig_user_id"] = data.ig_user_id.strip()
    if data.account_name:
        fields["account_name"] = data.account_name.strip()
    if data.app_id:
        fields["app_id"] = data.app_id.strip()
    if data.app_secret:
        fields["app_secret"] = data.app_secret.strip()

    conn = repo.upsert_connection(db, **fields)
    return _to_status(conn)


def mark_token_ok(db: Session) -> None:
    if repo.get_connection(db) is not None:
        repo.upsert_connection(db, last_test_ok=True, last_error=None)


def mark_token_expired(db: Session, msg: str = "Token de Meta expirado") -> None:
    if repo.get_connection(db) is not None:
        repo.upsert_connection(db, last_test_ok=False, last_error=msg)
