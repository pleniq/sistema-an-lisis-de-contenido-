from typing import Optional
from pydantic import BaseModel


class AnalysisRow(BaseModel):
    grupo: str
    reels: int
    reach: Optional[float] = None
    views: Optional[float] = None
    likes: Optional[float] = None
    comments: Optional[float] = None
    saved: Optional[float] = None
    shares: Optional[float] = None
    total_interactions: Optional[float] = None
    avg_watch_time_sec: Optional[float] = None
    engagement_rate: Optional[float] = None
    save_rate: Optional[float] = None
    share_rate: Optional[float] = None
