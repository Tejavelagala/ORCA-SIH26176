from app.engine.risk_engine import evaluate
from app.engine.route_engine import recommend_route


def base_weather(wind=14.8, wave=0.58):
    return {
        "wind_speed_kmh": wind,
        "wave_height_m": wave,
        "cyclone_warning": False,
    }


def test_safe_prototype_case():
    result = evaluate({}, base_weather(), {"restricted_zone": False})
    assert result["status"] == "SAFE"


def test_caution_prototype_case():
    result = evaluate({}, base_weather(wind=35, wave=1.0), {"restricted_zone": False})
    assert result["status"] == "CAUTION"


def test_unsafe_wave_case():
    result = evaluate({}, base_weather(wave=3.2), {"restricted_zone": False})
    assert result["status"] == "UNSAFE"


def test_restricted_zone_blocks():
    result = evaluate({}, base_weather(), {"restricted_zone": True})
    assert result["status"] == "BLOCKED"


def test_missing_critical_data_does_not_return_safe():
    result = evaluate(
        {},
        {"wind_speed_kmh": 14.8, "wave_height_m": None, "cyclone_warning": False},
        {"restricted_zone": False},
    )
    assert result["status"] == "DATA_UNAVAILABLE"


def test_route_is_blocked_for_unsafe_risk():
    route = recommend_route(
        {
            "pfz": {
                "name": "Demo PFZ",
                "direction": "NE",
                "distance_km": 18,
                "latitude": 17.05,
                "longitude": 82.40,
            },
            "query_coordinates": {"latitude": 16.99, "longitude": 82.25},
        },
        {"status": "UNSAFE"},
    )
    assert route["safe_to_navigate"] is False
    assert route["route_mode"] == "straight_line_prototype"


def test_route_bearing_is_computed():
    route = recommend_route(
        {
            "pfz": {
                "name": "Demo PFZ",
                "direction": "NE",
                "distance_km": 18,
                "latitude": 17.05,
                "longitude": 82.40,
            },
            "query_coordinates": {"latitude": 16.99, "longitude": 82.25},
        },
        {"status": "SAFE"},
    )
    assert "computed_bearing_degrees" in route
    assert route["computed_direction"] in {"N", "NE", "E", "SE", "S", "SW", "W", "NW"}
