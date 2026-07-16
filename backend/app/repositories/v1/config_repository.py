from typing import Optional

from sqlalchemy.orm import Session

from app.models.v1 import MetaConnection


def get_connection(db: Session) -> Optional[MetaConnection]:
    return db.query(MetaConnection).first()


def upsert_connection(db: Session, **fields) -> MetaConnection:
    """Fila única. Setea exactamente los campos pasados (el caller decide qué tocar)."""
    conn = db.query(MetaConnection).first()
    if conn is None:
        conn = MetaConnection()
        db.add(conn)
    for key, value in fields.items():
        setattr(conn, key, value)
    db.commit()
    db.refresh(conn)
    return conn
