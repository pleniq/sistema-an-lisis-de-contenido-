from tests._helpers import ingest_reels


def test_analysis_groups_and_averages(client, db):
    reels = ingest_reels(client, n=3)
    by_media = {r["ig_media_id"]: r["id"] for r in reels}
    # media-1 y media-2 → formato "A" (reach 1000 y 2000); media-3 → "B" (reach 3000)
    client.patch(f"/api/v1/reels/{by_media['media-1']}", json={"formato": "A"})
    client.patch(f"/api/v1/reels/{by_media['media-2']}", json={"formato": "A"})
    client.patch(f"/api/v1/reels/{by_media['media-3']}", json={"formato": "B"})

    resp = client.get("/api/v1/analysis?group_by=formato")
    assert resp.status_code == 200
    groups = {row["grupo"]: row for row in resp.json()}
    assert groups["A"]["reels"] == 2
    assert groups["B"]["reels"] == 1
    assert groups["A"]["reach"] == 1500.0   # (1000+2000)/2
    assert groups["B"]["reach"] == 3000.0
    assert abs(groups["A"]["engagement_rate"] - 0.44) < 1e-6


def test_analysis_includes_unlabeled_group(client, db):
    reels = ingest_reels(client, n=2)
    client.patch(f"/api/v1/reels/{reels[0]['id']}", json={"categoria": "TOFU"})
    resp = client.get("/api/v1/analysis?group_by=categoria")
    groups = {row["grupo"]: row for row in resp.json()}
    assert "(sin etiqueta)" in groups  # el reel sin categoría cae acá


def test_analysis_invalid_group_by_400(client, db):
    assert client.get("/api/v1/analysis?group_by=inexistente").status_code == 400
