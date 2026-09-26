from app.services.fishing_service import build_fishing_intelligence


def test_fishing_intelligence_returns_ranked_candidate():
    result = build_fishing_intelligence({
        "name": "Kakinada PFZ Demo",
        "latitude": 16.99,
        "longitude": 82.55,
        "distance_km": 18,
        "direction": "NE",
        "sst_c": 28.2,
        "chlorophyll_mg_m3": 0.68,
    })
    assert result["available"] is True
    assert result["candidates"][0]["rank"] == 1
    assert 0 <= result["fishing_score"] <= 100
    assert "indicative_species" in result["candidates"][0]
