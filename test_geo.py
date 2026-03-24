from app import create_app


app = create_app()
client = app.test_client()


def test_geo_hotspots_route():
    response = client.get("/api/geo-hotspots?year=2027")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    if data:
        row = data[0]
        assert "country" in row
        assert "latitude" in row
        assert "longitude" in row
        assert "risk_score" in row


def test_geo_hotspots_invalid_year():
    response = client.get("/api/geo-hotspots?year=-1")
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"]["code"] == "invalid_year"


def test_geo_future_areas_route():
    response = client.get("/api/geo-future-areas?year=2027&country=India")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    if data:
        row = data[0]
        assert "country" in row
        assert "latitude" in row
        assert "longitude" in row
        assert "risk_score" in row


def test_geo_future_areas_invalid_year():
    response = client.get("/api/geo-future-areas?year=-1")
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"]["code"] == "invalid_year"
