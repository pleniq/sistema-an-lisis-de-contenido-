from sqlalchemy import text


def test_core_tables_and_view_exist(db):
    tables = {r[0] for r in db.execute(text(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    ))}
    assert {"accounts", "reels", "reel_metric_snapshots", "ingest_runs",
            "angulos", "formatos", "tipos_hook", "categorias", "temas"} <= tables
    views = {r[0] for r in db.execute(text(
        "SELECT table_name FROM information_schema.views WHERE table_schema='public'"
    ))}
    assert "reel_latest_metrics" in views
