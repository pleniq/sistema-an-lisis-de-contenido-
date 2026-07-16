from tests._helpers import ingest_reels


def test_list_labels_empty(client, db):
    resp = client.get("/api/v1/labels/formato")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_label(client, db):
    ingest_reels(client, n=1)  # crea la cuenta
    resp = client.post("/api/v1/labels/categoria", json={"name": "BOFU"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "BOFU"


def test_create_label_idempotent(client, db):
    ingest_reels(client, n=1)
    first = client.post("/api/v1/labels/tema", json={"name": "Precios"}).json()
    second = client.post("/api/v1/labels/tema", json={"name": "Precios"}).json()
    assert first["id"] == second["id"]  # misma etiqueta, no duplica
    temas = client.get("/api/v1/labels/tema").json()
    assert sum(1 for t in temas if t["name"] == "Precios") == 1


def test_unknown_dimension_404(client, db):
    assert client.get("/api/v1/labels/inexistente").status_code == 404


def test_create_label_without_account_400(client, db):
    resp = client.post("/api/v1/labels/angulo", json={"name": "X"})
    assert resp.status_code == 400


def test_create_is_case_insensitive(client, db):
    ingest_reels(client, n=1)
    a = client.post("/api/v1/labels/formato", json={"name": "Talking head"}).json()
    b = client.post("/api/v1/labels/formato", json={"name": "talking HEAD"}).json()
    assert a["id"] == b["id"]  # misma etiqueta pese a mayúsculas distintas
    assert len(client.get("/api/v1/labels/formato").json()) == 1


def test_list_includes_counts(client, db):
    reels = ingest_reels(client, n=2)
    for r in reels:
        client.patch(f"/api/v1/reels/{r['id']}", json={"formato": "Talking head"})
    formatos = client.get("/api/v1/labels/formato").json()
    assert formatos[0]["count"] == 2


def test_rename_label(client, db):
    ingest_reels(client, n=1)
    lid = client.post("/api/v1/labels/angulo", json={"name": "Educativo"}).json()["id"]
    resp = client.patch(f"/api/v1/labels/angulo/{lid}", json={"name": "Didáctico"})
    assert resp.status_code == 200
    assert resp.json() == {"id": lid, "name": "Didáctico", "merged": False}


def test_rename_into_existing_merges(client, db):
    reels = ingest_reels(client, n=2)
    # dos etiquetas casi iguales por tipeo, una en cada reel
    client.patch(f"/api/v1/reels/{reels[0]['id']}", json={"formato": "Talking head"})
    client.patch(f"/api/v1/reels/{reels[1]['id']}", json={"formato": "Talkinghead"})
    dupe = next(f for f in client.get("/api/v1/labels/formato").json() if f["name"] == "Talkinghead")
    # renombrar la duplicada al nombre bueno → fusiona
    resp = client.patch(f"/api/v1/labels/formato/{dupe['id']}", json={"name": "Talking head"})
    assert resp.json()["merged"] is True
    formatos = client.get("/api/v1/labels/formato").json()
    assert len(formatos) == 1
    assert formatos[0]["count"] == 2  # los 2 reels quedaron en la etiqueta buena


def test_delete_label_unsets_reels(client, db):
    reels = ingest_reels(client, n=1)
    rid = reels[0]["id"]
    lid = client.patch(f"/api/v1/reels/{rid}", json={"formato": "Talking head"}).json()
    fid = client.get("/api/v1/labels/formato").json()[0]["id"]
    assert client.delete(f"/api/v1/labels/formato/{fid}").status_code == 204
    assert client.get("/api/v1/labels/formato").json() == []
    assert client.get(f"/api/v1/reels/{rid}").json()["formato"] is None
