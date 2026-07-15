from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


class ReelRow(BaseModel):
    id: str
    ig_media_id: str
    permalink: Optional[str] = None
    caption: Optional[str] = None
    thumbnail_url: Optional[str] = None
    titulo: Optional[str] = None
    guion: Optional[str] = None
    published_at: Optional[datetime] = None
    # etiquetas (nombres, no ids) — para la tabla y el panel de etiquetado
    angulo: Optional[str] = None
    formato: Optional[str] = None
    tipo_hook: Optional[str] = None
    categoria: Optional[str] = None
    tema: Optional[str] = None
    # métricas del último snapshot + ratios (vista reel_latest_metrics)
    snapshot_date: Optional[date] = None
    reach: Optional[int] = None
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    saved: Optional[int] = None
    shares: Optional[int] = None
    total_interactions: Optional[int] = None
    avg_watch_time_sec: Optional[float] = None
    engagement_rate: Optional[float] = None
    save_rate: Optional[float] = None
    share_rate: Optional[float] = None


class ReelUpdate(BaseModel):
    """Edición de campos manuales. Solo se tocan los campos presentes en el request
    (exclude_unset). Un campo de dimensión en null/"" limpia la etiqueta."""
    titulo: Optional[str] = None
    guion: Optional[str] = None
    angulo: Optional[str] = None
    formato: Optional[str] = None
    tipo_hook: Optional[str] = None
    categoria: Optional[str] = None
    tema: Optional[str] = None
