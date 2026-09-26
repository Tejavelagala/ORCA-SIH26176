from app.engine.risk_engine import evaluate

def test_invalid_weather_values_become_data_unavailable():
    result = evaluate(
        {},
        {"wind_speed_kmh": "unknown", "wave_height_m": "unknown"},
        {"location_supported": True, "restricted_zone": False, "eez_status": "unavailable"},
    )
    assert result["status"] == "DATA_UNAVAILABLE"

def test_unsupported_location_becomes_data_unavailable():
    result = evaluate(
        {},
        {"wind_speed_kmh": 10, "wave_height_m": 0.5},
        {"location_supported": False, "restricted_zone": False, "eez_status": "unsupported-location"},
    )
    assert result["status"] == "DATA_UNAVAILABLE"
