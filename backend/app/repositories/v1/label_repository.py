"""Etiquetas: una tabla de dimensión por dimensión, con create-on-the-fly.

DIMENSIONS mapea el nombre público de la dimensión → (modelo, columna FK en reels).
Es la única fuente de ese mapeo; el resto del código lo importa de acá.

Anti-duplicados: el match es CASE-INSENSITIVE, así "Talking head" y "talking head"
son la misma etiqueta (no se duplican por tipeo/mayúsculas).
"""
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.v1 import Angulo, Formato, TipoHook, Categoria, Tema, Reel

DIMENSIONS = {
    "angulo": (Angulo, "angulo_id"),
    "formato": (Formato, "formato_id"),
    "tipo_hook": (TipoHook, "tipo_hook_id"),
    "categoria": (Categoria, "categoria_id"),
    "tema": (Tema, "tema_id"),
}


# Valores sugeridos por dimensión (framework de contenido de Pleniq).
DEFAULT_VALUES = {
    "angulo": [
        "Deseo", "Dolor", "Resultado del servicio", "Viejo vs Nuevo", "Objeciones",
        "Obstáculos", "Errores comunes", "Mitos / creencias", "Enemigo común",
    ],
    "formato": [
        "Talking head con jump cuts", "Talking head + B-roll", "POV de proceso real",
        "Carrusel con hook", "Voz en off + B-roll", "Walk & talk",
        "Screen recording narrado", "Storytime sentado", "Skit / actuado",
        "Pizarra / explainer", "Reacción / crítica", "Duo / colaboración",
    ],
    "tipo_hook": [
        "Desafiante / provocador", "Promesa / resultado", "Historia / prueba social",
        "Problema / dolor", "Comparación / contraste", "Urgencia / FOMO",
        "Curiosidad / loop abierto",
    ],
    "categoria": ["TOFU", "MOFU", "BOFU"],
    "tema": [
        "Sistemas a medida", "Páginas web", "Automatizaciones", "CRM",
        "Precios", "Casos de cliente",
    ],
}


def is_valid_dimension(dimension: str) -> bool:
    return dimension in DIMENSIONS


def seed_defaults(db: Session, account_id: str) -> dict:
    """Crea los valores sugeridos de cada dimensión (idempotente). Devuelve cuántos hay por dimensión."""
    for dimension, values in DEFAULT_VALUES.items():
        for name in values:
            get_or_create(db, account_id, dimension, name)
    db.commit()
    return {dim: len(vals) for dim, vals in DEFAULT_VALUES.items()}


def list_labels(db: Session, dimension: str) -> list:
    model, _ = DIMENSIONS[dimension]
    return db.query(model).order_by(func.lower(model.name)).all()


def list_labels_with_counts(db: Session, dimension: str) -> list[tuple]:
    """Cada etiqueta + cuántos reels la usan (para la pantalla de gestión)."""
    model, fk = DIMENSIONS[dimension]
    fk_col = getattr(Reel, fk)
    counts = dict(db.query(fk_col, func.count(Reel.id)).group_by(fk_col).all())
    labels = db.query(model).order_by(func.lower(model.name)).all()
    return [(l, counts.get(l.id, 0)) for l in labels]


def get_or_create(db: Session, account_id: str, dimension: str, name: str):
    """Devuelve la etiqueta (match case-insensitive); la crea si no existe."""
    model, _ = DIMENSIONS[dimension]
    name = name.strip()
    label = (db.query(model)
               .filter(model.account_id == account_id, func.lower(model.name) == name.lower())
               .first())
    if label is None:
        label = model(account_id=account_id, name=name)
        db.add(label)
        db.flush()
    return label


def rename_label(db: Session, dimension: str, label_id: str, new_name: str):
    """Renombra. Si el nuevo nombre choca (case-insensitive) con OTRA etiqueta,
    FUSIONA: reasigna los reels y borra la duplicada. Devuelve (label, merged)."""
    model, fk = DIMENSIONS[dimension]
    new_name = new_name.strip()
    label = db.get(model, label_id)
    if label is None:
        return None, False

    existing = (db.query(model)
                  .filter(model.account_id == label.account_id,
                          func.lower(model.name) == new_name.lower(),
                          model.id != label_id)
                  .first())
    if existing is not None:
        db.query(Reel).filter(getattr(Reel, fk) == label_id).update({fk: existing.id})
        db.delete(label)
        db.commit()
        return existing, True

    label.name = new_name
    db.commit()
    return label, False


def delete_label(db: Session, dimension: str, label_id: str) -> bool:
    """Borra la etiqueta; los reels que la usaban quedan sin ella (FK SET NULL)."""
    model, _ = DIMENSIONS[dimension]
    label = db.get(model, label_id)
    if label is None:
        return False
    db.delete(label)
    db.commit()
    return True


def count_reels(db: Session, dimension: str, label_id: str) -> int:
    _, fk = DIMENSIONS[dimension]
    return db.query(func.count(Reel.id)).filter(getattr(Reel, fk) == label_id).scalar() or 0


def get_default_account_id(db: Session) -> Optional[str]:
    from app.models.v1 import Account
    account = db.query(Account).order_by(Account.created_at).first()
    return account.id if account else None
