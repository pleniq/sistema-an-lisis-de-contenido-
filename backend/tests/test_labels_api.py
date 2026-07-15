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
