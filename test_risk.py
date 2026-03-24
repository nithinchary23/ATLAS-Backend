from app import create_app


app = create_app()
client = app.test_client()


def test_risk_top10_route():
    response = client.get("/api/risk/top10")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    if data:
        row = data[0]
        assert "Country" in row
        assert "Predicted Victims" in row


def test_risk_history_route():
    response = client.get("/api/risk/history")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    if data:
        row = data[0]
        assert "Country" in row
        assert "Victims" in row
        assert "Latitude" in row
        assert "Longitude" in row


def test_risk_summary_requires_country():
    response = client.get("/api/risk/summary")
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"]["code"] == "missing_country"


def test_risk_summary_country():
    response = client.get("/api/risk/summary?country=India")
    assert response.status_code == 200
    data = response.get_json()
    assert data["Country"] == "India"
    assert "Historical Victims" in data
    assert "Future Predicted Victims" in data
    assert "Percent Change" in data
