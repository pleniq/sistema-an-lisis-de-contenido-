from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.v1.base import _uuid, _now


class MetaConnection(Base):
    """Conexión con la Graph API de Meta. Fila única (settings del sistema).
    Guarda el token que usa el backend para jalar métricas. Uso local; el token
    vive acá para que Luca pueda gestionarlo desde la pantalla de Configuración."""
    __tablename__ = "meta_connection"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ig_user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    account_name: Mapped[str] = mapped_column(String(255), default="Instagram")
    app_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    app_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_test_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
