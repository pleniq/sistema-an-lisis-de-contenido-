from tests._helpers import ingest_reels


def test_export_builds_markdown_with_table_and_guiones(client, db):
    reels = ingest_reels(client, n=2)
    ids = [r["id"] for r in reels]
    client.patch(f"/api/v1/reels/{ids[0]}", json={
        "titulo": "Hook fuerte", "guion": "Primer segundo: pregunta directa.",
        "angulo": "Educativo", "formato": "Talking head",
    })
    resp = client.post("/api/v1/reels/export", json={"reel_ids": ids})
    assert resp.status_code == 200
    body = resp.json()
    assert body["format"] == "markdown"
    assert body["reels"] == 2
    text = body["text"]
    assert "| # | título | publicado |" in text     # header de tabla una sola vez
    assert "0.440" in text                            # ratio a 3 decimales (ER 0.44)
    assert "## Guiones" in text
    assert "Primer segundo: pregunta directa." in text


def test_export_empty_ids(client, db):
    resp = client.post("/api/v1/reels/export", json={"reel_ids": []})
    assert resp.status_code == 200
    assert resp.json()["reels"] == 0


def test_export_without_guion_omits_section(client, db):
    reels = ingest_reels(client, n=1)
    resp = client.post("/api/v1/reels/export", json={"reel_ids": [reels[0]["id"]]})
    text = resp.json()["text"]
    assert "## Guiones" not in text  # no hay guiones cargados
