"""Tablas de dimensión de etiquetas. Una fila = un valor (ej. ángulo "Educativo")."""
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.v1.base import _uuid, _now


class _LabelBase:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Angulo(_LabelBase, Base):
    __tablename__ = "angulos"
    __table_args__ = (UniqueConstraint("account_id", "name", name="uq_angulos_account_name"),)


class Formato(_LabelBase, Base):
    __tablename__ = "formatos"
    __table_args__ = (UniqueConstraint("account_id", "name", name="uq_formatos_account_name"),)


class TipoHook(_LabelBase, Base):
    __tablename__ = "tipos_hook"
    __table_args__ = (UniqueConstraint("account_id", "name", name="uq_tipos_hook_account_name"),)


class Categoria(_LabelBase, Base):
    __tablename__ = "categorias"
    __table_args__ = (UniqueConstraint("account_id", "name", name="uq_categorias_account_name"),)


class Tema(_LabelBase, Base):
    __tablename__ = "temas"
    __table_args__ = (UniqueConstraint("account_id", "name", name="uq_temas_account_name"),)
