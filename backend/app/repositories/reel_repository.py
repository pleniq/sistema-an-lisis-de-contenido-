from sqlalchemy import text
from sqlalchemy.orm import Session


def list_reels_with_latest(db: Session) -> list[dict]:
    rows = db.execute(text("""
        SELECT r.id, r.ig_media_id, r.permalink, r.caption, r.thumbnail_url,
               r.titulo, r.published_at,
               m.snapshot_date, m.reach, m.views, m.likes, m.comments, m.saved,
               m.shares, m.total_interactions, m.avg_watch_time_sec,
               m.engagement_rate, m.save_rate, m.share_rate
        FROM reels r
        LEFT JOIN reel_latest_metrics m ON m.reel_id = r.id
        ORDER BY r.published_at DESC NULLS LAST
    """)).mappings().all()
    return [dict(row) for row in rows]
