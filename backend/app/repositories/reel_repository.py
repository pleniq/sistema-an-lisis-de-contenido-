from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

# SELECT compartido: reel + etiquetas (nombres) + últimas métricas y ratios.
_SELECT = """
    SELECT r.id, r.ig_media_id, r.permalink, r.caption, r.thumbnail_url,
           r.titulo, r.guion, r.published_at,
           ang.name  AS angulo,
           fmt.name  AS formato,
           hk.name   AS tipo_hook,
           cat.name  AS categoria,
           tem.name  AS tema,
           m.snapshot_date, m.reach, m.views, m.likes, m.comments, m.saved,
           m.shares, m.total_interactions, m.avg_watch_time_sec,
           m.engagement_rate, m.save_rate, m.share_rate
    FROM reels r
    LEFT JOIN reel_latest_metrics m ON m.reel_id = r.id
    LEFT JOIN angulos    ang ON ang.id = r.angulo_id
    LEFT JOIN formatos   fmt ON fmt.id = r.formato_id
    LEFT JOIN tipos_hook hk  ON hk.id  = r.tipo_hook_id
    LEFT JOIN categorias cat ON cat.id = r.categoria_id
    LEFT JOIN temas      tem ON tem.id = r.tema_id
"""


def list_reels_with_latest(db: Session) -> list[dict]:
    rows = db.execute(text(
        _SELECT + " ORDER BY r.published_at DESC NULLS LAST"
    )).mappings().all()
    return [dict(row) for row in rows]


def get_reel_with_latest(db: Session, reel_id: str) -> Optional[dict]:
    row = db.execute(text(
        _SELECT + " WHERE r.id = :rid"
    ), {"rid": reel_id}).mappings().first()
    return dict(row) if row else None


def list_snapshots(db: Session, reel_id: str) -> list[dict]:
    """Historial de snapshots de un reel (curva en el tiempo) + ratios por fila."""
    rows = db.execute(text("""
        SELECT snapshot_date, reach, views, likes, comments, saved, shares,
               total_interactions,
               (avg_watch_time_ms / 1000.0) AS avg_watch_time_sec,
               (total_interactions::float / NULLIF(reach, 0)) AS engagement_rate,
               (saved::float / NULLIF(reach, 0)) AS save_rate,
               (shares::float / NULLIF(reach, 0)) AS share_rate
        FROM reel_metric_snapshots
        WHERE reel_id = :rid
        ORDER BY snapshot_date ASC
    """), {"rid": reel_id}).mappings().all()
    return [dict(r) for r in rows]
