from app import create_app


app = create_app()
client = app.test_client()


def test_forecast_route():
    response = client.get("/api/forecast")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_forecast_aggregated_route():
    response = client.get("/api/forecast/aggregated?country=India")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    if data:
        row = data[0]
        assert "Country" in row
        assert "Year" in row
        assert "Predicted Victims" in row


def test_forecast_timeline_requires_country():
    response = client.get("/api/forecast/timeline")
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"]["code"] == "missing_country"


def test_forecast_timeline_country():
    response = client.get("/api/forecast/timeline?country=India")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    if data:
        row = data[0]
        assert "Year" in row
        assert "Victims" in row
        assert "Type" in row
