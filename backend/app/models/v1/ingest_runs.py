from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.v1.base import _uuid, _now


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
