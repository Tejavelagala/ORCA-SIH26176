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
    assert 0 <= result["score"] < 25
    assert result["risk_band"] == "LOW"


def test_caution_prototype_case():
    result = evaluate({}, base_weather(wind=35, wave=1.0), {"restricted_zone": False})
    assert result["status"] == "CAUTION"
    assert 25 <= result["score"] < 60


def test_unsafe_wave_case():
    result = evaluate({}, base_weather(wave=3.2), {"restricted_zone": False})
    assert result["status"] == "UNSAFE"
    assert result["score"] >= 60


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
    assert route["route_mode"] in {"straight_line_reference", "geofence_aware_a_star_reference"}


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
    assert route["direction"] == route["computed_direction"]
    assert route["distance_km"] > 0


def test_demo_scenario_profiles():
    from app.main import DEMO_SCENARIOS

    assert set(DEMO_SCENARIOS) == {
        "safe",
        "caution",
        "unsafe",
        "blocked",
        "data_unavailable",
    }


def test_demo_profiles_map_to_expected_statuses():
    from app.main import DEMO_SCENARIOS

    expected = {
        "safe": "SAFE",
        "caution": "CAUTION",
        "unsafe": "UNSAFE",
        "blocked": "BLOCKED",
        "data_unavailable": "DATA_UNAVAILABLE",
    }

    for name, expected_status in expected.items():
        conditions = DEMO_SCENARIOS[name]
        weather = {
            "wind_speed_kmh": conditions["wind_speed_kmh"],
            "wave_height_m": conditions["wave_height_m"],
            "cyclone_warning": conditions["cyclone_warning"],
        }
        geo = {"restricted_zone": name == "blocked"}
        result = evaluate({}, weather, geo)
        assert result["status"] == expected_status


def test_demo_trace_contract():
    from app.main import DEMO_SCENARIOS

    assert len(DEMO_SCENARIOS) == 6
    assert set(DEMO_SCENARIOS) == {
        "safe",
        "caution",
        "unsafe",
        "cyclone_alert",
        "blocked",
        "data_unavailable",
    }
