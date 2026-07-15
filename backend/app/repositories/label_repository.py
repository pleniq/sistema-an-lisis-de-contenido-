"""Etiquetas: una tabla de dimensión por dimensión, con create-on-the-fly.

DIMENSIONS mapea el nombre público de la dimensión → (modelo, columna FK en reels).
Es la única fuente de ese mapeo; el resto del código lo importa de acá.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Angulo, Formato, TipoHook, Categoria, Tema

DIMENSIONS = {
    "angulo": (Angulo, "angulo_id"),
    "formato": (Formato, "formato_id"),
    "tipo_hook": (TipoHook, "tipo_hook_id"),
    "categoria": (Categoria, "categoria_id"),
    "tema": (Tema, "tema_id"),
}


def is_valid_dimension(dimension: str) -> bool:
    return dimension in DIMENSIONS


def list_labels(db: Session, dimension: str) -> list:
    model, _ = DIMENSIONS[dimension]
    return db.query(model).order_by(model.name).all()


def get_or_create(db: Session, account_id: str, dimension: str, name: str):
    """Devuelve la etiqueta (account_id, name); la crea si no existe. Idempotente."""
    model, _ = DIMENSIONS[dimension]
    name = name.strip()
    label = (db.query(model)
               .filter(model.account_id == account_id, model.name == name)
               .one_or_none())
    if label is None:
        label = model(account_id=account_id, name=name)
        db.add(label)
        db.flush()
    return label


def get_default_account_id(db: Session) -> Optional[str]:
    from app.models import Account
    account = db.query(Account).order_by(Account.created_at).first()
    return account.id if account else None
