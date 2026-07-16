"""Arma el export markdown token-eficiente para pegar en Claude Code.

Dos partes (ver diseño §7):
  1. Tabla de stats — headers una sola vez; enteros crudos, ratios a 3 decimales.
  2. Guiones — un subbloque por reel, separado de la tabla numérica.
"""
from sqlalchemy.orm import Session

from app.repositories.v1.reel_repository import get_reel_with_latest

_TABLE_HEADER = (
    "| # | título | publicado | ángulo | formato | hook | categoría | tema | "
    "reach | views | likes | coment | saves | shares | ER | save% | share% | watch_s |"
)
_TABLE_SEP = "|" + "---|" * 18


def _txt(v) -> str:
    return str(v) if v not in (None, "") else "—"


def _intv(v) -> str:
    return str(v) if v is not None else "—"


def _ratio(v) -> str:
    return f"{v:.3f}" if v is not None else "—"


def _watch(v) -> str:
    return f"{v:.1f}" if v is not None else "—"


def _day(v) -> str:
    return v.isoformat()[:10] if v is not None else "—"


def export_reels(db: Session, reel_ids: list[str]) -> dict:
    rows = [r for r in (get_reel_with_latest(db, rid) for rid in reel_ids) if r is not None]

    lines: list[str] = [f"# Reels seleccionados ({len(rows)})", "", _TABLE_HEADER, _TABLE_SEP]
    for i, r in enumerate(rows, start=1):
        lines.append(
            f"| {i} | {_txt(r['titulo'])} | {_day(r['published_at'])} | "
            f"{_txt(r['angulo'])} | {_txt(r['formato'])} | {_txt(r['tipo_hook'])} | "
            f"{_txt(r['categoria'])} | {_txt(r['tema'])} | "
            f"{_intv(r['reach'])} | {_intv(r['views'])} | {_intv(r['likes'])} | "
            f"{_intv(r['comments'])} | {_intv(r['saved'])} | {_intv(r['shares'])} | "
            f"{_ratio(r['engagement_rate'])} | {_ratio(r['save_rate'])} | "
            f"{_ratio(r['share_rate'])} | {_watch(r['avg_watch_time_sec'])} |"
        )

    guiones = [r for r in rows if r.get("guion")]
    if guiones:
        lines += ["", "## Guiones"]
        for i, r in enumerate(rows, start=1):
            if not r.get("guion"):
                continue
            titulo = r["titulo"] or r["ig_media_id"]
            lines += ["", f"### {i} — {titulo}"]
            if r.get("permalink"):
                lines.append(r["permalink"])
            lines += ["", r["guion"]]

    text = "\n".join(lines)
    return {"format": "markdown", "reels": len(rows), "text": text}
