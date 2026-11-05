def test_homepage(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Network Dashboard" in response.data
    assert b"NetTrack | Network Intelligence" in response.data


def test_health_api(client):
    response = client.get("/api/health")

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["application"] == "NetTrack"
    assert data["status"] == "healthy"