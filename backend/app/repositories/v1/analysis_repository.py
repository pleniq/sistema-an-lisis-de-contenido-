from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories.v1.label_repository import DIMENSIONS


def analysis_by_dimension(db: Session, dimension: str) -> list[dict]:
    """Promedio de cada métrica + ratios por grupo de la dimensión, con count.
    `dimension` ya viene validado contra DIMENSIONS (whitelist), así que interpolar
    el nombre de tabla/columna es seguro."""
    model, fk_col = DIMENSIONS[dimension]
    table = model.__tablename__

    sql = f"""
        SELECT COALESCE(l.name, '(sin etiqueta)') AS grupo,
               COUNT(*)                    AS reels,
               AVG(m.reach)                AS reach,
               AVG(m.views)                AS views,
               AVG(m.likes)                AS likes,
               AVG(m.comments)             AS comments,
               AVG(m.saved)                AS saved,
               AVG(m.shares)               AS shares,
               AVG(m.total_interactions)   AS total_interactions,
               AVG(m.avg_watch_time_sec)   AS avg_watch_time_sec,
               AVG(m.engagement_rate)      AS engagement_rate,
               AVG(m.save_rate)            AS save_rate,
               AVG(m.share_rate)           AS share_rate
        FROM reels r
        JOIN reel_latest_metrics m ON m.reel_id = r.id
        LEFT JOIN {table} l ON l.id = r.{fk_col}
        GROUP BY COALESCE(l.name, '(sin etiqueta)')
        ORDER BY AVG(m.engagement_rate) DESC NULLS LAST
    """
    rows = db.execute(text(sql)).mappings().all()
    return [dict(row) for row in rows]
