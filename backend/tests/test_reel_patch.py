from tests._helpers import ingest_reels, TOKEN


def test_patch_sets_titulo_guion_and_labels(client, db):
    reels = ingest_reels(client, n=1)
    rid = reels[0]["id"]
    resp = client.patch(f"/api/v1/reels/{rid}", json={
        "titulo": "Mi hook fuerte", "guion": "Primer segundo: ...",
        "angulo": "Educativo", "formato": "Talking head", "categoria": "TOFU",
    })
    assert resp.status_code == 200
    row = resp.json()
    assert row["titulo"] == "Mi hook fuerte"
    assert row["guion"] == "Primer segundo: ..."
    assert row["angulo"] == "Educativo"
    assert row["formato"] == "Talking head"
    assert row["categoria"] == "TOFU"
    # la etiqueta quedó disponible en el catálogo
    angulos = client.get("/api/v1/labels/angulo").json()
    assert any(a["name"] == "Educativo" for a in angulos)


def test_patch_reuses_label_same_name(client, db):
    reels = ingest_reels(client, n=2)
    for r in reels:
        resp = client.patch(f"/api/v1/reels/{r['id']}", json={"formato": "Reel editado"})
        assert resp.status_code == 200
    formatos = client.get("/api/v1/labels/formato").json()
    assert sum(1 for f in formatos if f["name"] == "Reel editado") == 1  # no duplica


def test_patch_clear_label_with_null(client, db):
    reels = ingest_reels(client, n=1)
    rid = reels[0]["id"]
    client.patch(f"/api/v1/reels/{rid}", json={"angulo": "Educativo"})
    resp = client.patch(f"/api/v1/reels/{rid}", json={"angulo": None})
    assert resp.status_code == 200
    assert resp.json()["angulo"] is None


def test_patch_404_unknown_reel(client, db):
    resp = client.patch("/api/v1/reels/no-existe", json={"titulo": "x"})
    assert resp.status_code == 404


def test_ingest_does_not_overwrite_labels(client, db):
    reels = ingest_reels(client, n=1)
    rid = reels[0]["id"]
    client.patch(f"/api/v1/reels/{rid}", json={"angulo": "Educativo", "titulo": "T"})
    ingest_reels(client, n=1)  # re-sync mismo media
    row = client.get(f"/api/v1/reels/{rid}").json()
    assert row["angulo"] == "Educativo"
    assert row["titulo"] == "T"
