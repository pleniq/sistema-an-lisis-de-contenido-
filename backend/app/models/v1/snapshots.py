from datetime import datetime, date
from typing import Optional

from sqlalchemy import String, Integer, BigInteger, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.v1.base import _uuid, _now


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
