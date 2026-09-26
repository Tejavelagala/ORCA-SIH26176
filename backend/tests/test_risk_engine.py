from app.engine.risk_engine import evaluate


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
