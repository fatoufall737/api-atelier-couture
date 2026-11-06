def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_swagger_accessible(client):
    assert client.get("/docs").status_code == 200