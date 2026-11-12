from fastapi.testclient import TestClient


def test_health_and_catalog(client: TestClient) -> None:
    assert client.get("/health").json()["status"] == "ok"
    assert len(client.get("/catalog").json()["products"]) == 2


def test_compare_returns_refusal_without_projection(client: TestClient) -> None:
    response = client.post(
        "/scenarios/compare", json={"scenarios": [{"label": "High", "product_id": "demo_330ml_6pk", "price": 20}]}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["scenarios"][0]["status"] == "refused"
    assert result["scenarios"][0]["revenue"] is None
    assert result["assumptions"]


def test_unknown_product_returns_422(client: TestClient) -> None:
    response = client.post(
        "/scenarios/compare", json={"scenarios": [{"label": "Unknown", "product_id": "missing", "price": 10}]}
    )
    assert response.status_code == 422


def test_empty_candidates_returns_422(client: TestClient) -> None:
    assert client.post("/scenarios/compare", json={"scenarios": []}).status_code == 422


def test_unconfigured_copilot_returns_503(client: TestClient) -> None:
    assert client.post("/copilot", json={"question": "Compare prices"}).status_code == 503
