"""Modelos v1. Re-exporta las entidades para `from app.models.v1 import Account, Reel, ...`.
Importar este paquete registra todas las tablas en Base.metadata (lo usa Alembic)."""
from app.models.v1.accounts import Account
from app.models.v1.labels import Angulo, Formato, TipoHook, Categoria, Tema
from app.models.v1.reels import Reel
from app.models.v1.snapshots import ReelMetricSnapshot
from app.models.v1.ingest_runs import IngestRun

__all__ = [
    "Account",
    "Angulo", "Formato", "TipoHook", "Categoria", "Tema",
    "Reel", "ReelMetricSnapshot", "IngestRun",
]
