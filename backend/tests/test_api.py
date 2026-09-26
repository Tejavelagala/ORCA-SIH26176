from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_demo_endpoint_returns_expected_statuses():
    expected = {
        "safe": "SAFE",
        "caution": "CAUTION",
        "unsafe": "UNSAFE",
        "blocked": "BLOCKED",
        "data_unavailable": "DATA_UNAVAILABLE",
    }

    for scenario, status in expected.items():
        response = client.get(
            "/api/demo",
            params={"scenario": scenario, "location": "Kakinada"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["risk"]["status"] == status
        assert payload["trace"][-2]["stage"] == "Risk Engine"
        assert payload["route"]["safe_to_navigate"] is (status in {"SAFE", "CAUTION"})


def test_demo_unknown_scenario_is_explicit():
    response = client.get(
        "/api/demo",
        params={"scenario": "not-a-real-scenario"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] == "Unknown demo scenario"
    assert set(payload["available"]) == {
        "safe",
        "caution",
        "unsafe",
        "blocked",
        "data_unavailable",
    }


def test_query_endpoint_contract(monkeypatch):
    async def fake_run_query(query, location, language="en-IN"):
        return {
            "query": query,
            "location": location,
            "language": language,
            "risk": {"status": "SAFE"},
            "trace": [
                {"stage": "Intent", "status": "completed", "detail": "test"},
                {"stage": "Ocean Agent", "status": "completed", "detail": "test"},
                {"stage": "Weather Agent", "status": "completed", "detail": "test"},
                {"stage": "Geo Agent", "status": "completed", "detail": "test"},
                {"stage": "Risk Engine", "status": "completed", "detail": "test"},
                {"stage": "Explanation", "status": "completed", "detail": "test"},
            ],
        }

    monkeypatch.setattr("app.main.run_query", fake_run_query)

    response = client.get(
        "/api/query",
        params={
            "q": "Is it safe to fish?",
            "location": "Kakinada",
            "language": "en-IN",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["location"] == "Kakinada"
    assert payload["risk"]["status"] == "SAFE"
    assert len(payload["trace"]) == 6
    assert payload["trace"][0]["stage"] == "Intent"
    assert payload["trace"][-1]["stage"] == "Explanation"
