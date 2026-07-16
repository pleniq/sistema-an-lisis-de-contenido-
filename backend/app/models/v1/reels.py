from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.v1.base import _uuid, _now


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
