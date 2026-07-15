from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class IngestMetrics(BaseModel):
    reach: Optional[int] = None
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    saved: Optional[int] = None
    shares: Optional[int] = None
    total_interactions: Optional[int] = None
    ig_reels_avg_watch_time: Optional[int] = None       # ms
    ig_reels_video_view_total_time: Optional[int] = None  # ms


class IngestReel(BaseModel):
    ig_media_id: str
    permalink: Optional[str] = None
    caption: Optional[str] = None
    thumbnail_url: Optional[str] = None
    media_product_type: Optional[str] = None
    timestamp: Optional[datetime] = None  # published_at
    metrics: IngestMetrics


class IngestAccount(BaseModel):
    ig_user_id: str
    name: str


class IngestBatch(BaseModel):
    account: IngestAccount
    reels: list[IngestReel]
    captured_at: datetime
