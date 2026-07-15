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
    published_at: Optional[datetime] = None
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
