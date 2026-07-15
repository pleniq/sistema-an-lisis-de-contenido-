import uuid
from datetime import datetime, date, timezone
from typing import Optional

from sqlalchemy import (
    String, Text, Integer, BigInteger, Date, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    ig_user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    token_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


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


class Reel(Base):
    __tablename__ = "reels"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    ig_media_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    permalink: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_product_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # campos manuales (la ingesta NUNCA los pisa)
    titulo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    guion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    angulo_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("angulos.id", ondelete="SET NULL"), nullable=True)
    formato_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("formatos.id", ondelete="SET NULL"), nullable=True)
    tipo_hook_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("tipos_hook.id", ondelete="SET NULL"), nullable=True)
    categoria_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("categorias.id", ondelete="SET NULL"), nullable=True)
    tema_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("temas.id", ondelete="SET NULL"), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    snapshots: Mapped[list["ReelMetricSnapshot"]] = relationship(
        "ReelMetricSnapshot", back_populates="reel", cascade="all, delete-orphan"
    )


class ReelMetricSnapshot(Base):
    __tablename__ = "reel_metric_snapshots"
    __table_args__ = (UniqueConstraint("reel_id", "snapshot_date", name="uq_snapshot_reel_date"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    reel_id: Mapped[str] = mapped_column(String(36), ForeignKey("reels.id", ondelete="CASCADE"), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    reach: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    views: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    likes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comments: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    saved: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shares: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_interactions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_watch_time_ms: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    total_watch_time_ms: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    reel: Mapped["Reel"] = relationship("Reel", back_populates="snapshots")


class IngestRun(Base):
    __tablename__ = "ingest_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    account_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    trigger: Mapped[str] = mapped_column(String(16), default="manual")  # 'auto' | 'manual'
    status: Mapped[str] = mapped_column(String(16), default="running")  # running|ok|partial|error
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reels_processed: Mapped[int] = mapped_column(Integer, default=0)
    snapshots_written: Mapped[int] = mapped_column(Integer, default=0)
    error_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
