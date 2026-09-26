def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _confidence(ocean: dict, weather: dict, geo: dict) -> float:
    modes = [
        (ocean.get("source") or {}).get("mode"),
        (weather.get("source") or {}).get("mode"),
        (geo.get("source") or {}).get("mode"),
    ]
    weights = {"live": 0.92, "configured-gis-check": 0.90, "fallback": 0.62, "demo": 0.65, "unavailable": 0.25, None: 0.45}
    return round(min(weights.get(mode, 0.50) for mode in modes), 2)


def _risk_score(wind: float, wave: float, rain: float | None = None) -> int:
    wind_component = min(45.0, 40.0 * (max(0.0, wind) / 35.0) ** 2)
    wave_component = min(45.0, 50.0 * (max(0.0, wave) / 3.0) ** 2)
    rain_component = 0.0 if rain is None else min(10.0, max(0.0, rain) / 100.0 * 10.0)
    return int(round(min(100.0, wind_component + wave_component + rain_component)))


def _band(score: int | None) -> str:
    if score is None:
        return "UNKNOWN"
    if score < 25:
        return "LOW"
    if score < 60:
        return "MODERATE"
    return "HIGH"


def evaluate(ocean: dict, weather: dict, geo: dict):
    reasons = []
    factors = []

    wind = _number(weather.get("wind_speed_kmh"))
    wave = _number(weather.get("wave_height_m"))
    rain = _number(weather.get("rain_probability_pct"))
    cyclone = bool(weather.get("cyclone_warning"))
    restricted = bool(geo.get("restricted_zone"))

    if not geo.get("location_supported", True):
        return {
            "status": "DATA_UNAVAILABLE",
            "score": None,
            "risk_band": "UNKNOWN",
            "confidence": 0.25,
            "reasons": ["Selected location is not supported by the prototype coordinate/GIS registry"],
            "factors": [{"factor": "location_support", "value": False, "effect": "unknown"}],
            "decision_mode": "deterministic_prototype",
        }

    if restricted:
        return {
            "status": "BLOCKED",
            "score": 100,
            "risk_band": "HIGH",
            "confidence": _confidence(ocean, weather, geo),
            "reasons": ["Restricted GIS zone detected"],
            "factors": [{"factor": "geographic_restriction", "value": True, "effect": "block", "contribution": 100}],
            "decision_mode": "deterministic_prototype",
        }

    if cyclone:
        return {
            "status": "UNSAFE",
            "score": 100,
            "risk_band": "HIGH",
            "confidence": _confidence(ocean, weather, geo),
            "reasons": ["Marine/cyclone warning flag detected"],
            "factors": [{"factor": "marine_warning", "value": True, "effect": "unsafe", "contribution": 100}],
            "decision_mode": "deterministic_prototype",
        }

    missing = []
    if wind is None:
        missing.append("wind speed")
    if wave is None:
        missing.append("wave height")

    if missing:
        return {
            "status": "DATA_UNAVAILABLE",
            "score": None,
            "risk_band": "UNKNOWN",
            "confidence": 0.25,
            "reasons": ["Critical environmental data unavailable: " + ", ".join(missing)],
            "factors": [{"factor": "missing_critical_data", "value": missing, "effect": "unknown"}],
            "decision_mode": "deterministic_prototype",
        }

    score = _risk_score(wind, wave, rain)
    factors.append({
        "factor": "wind_speed_kmh",
        "value": wind,
        "threshold": 30,
        "contribution": round(min(40.0, 40.0 * (max(0.0, wind) / 35.0) ** 2), 1),
        "effect": "risk_input",
    })
    factors.append({
        "factor": "wave_height_m",
        "value": wave,
        "threshold": 2,
        "contribution": round(min(50.0, 50.0 * (max(0.0, wave) / 3.0) ** 2), 1),
        "effect": "risk_input",
    })

    if wave >= 3:
        status = "UNSAFE"
        reasons.append("Prototype high-wave threshold triggered")
        factors.append({"factor": "wave_threshold", "value": wave, "threshold": 3, "effect": "unsafe"})
    elif wave >= 2:
        status = "CAUTION"
        reasons.append("Prototype elevated-wave threshold triggered")
        factors.append({"factor": "wave_threshold", "value": wave, "threshold": 2, "effect": "caution"})
    elif wind >= 30:
        status = "CAUTION"
        reasons.append("Prototype high-wind threshold triggered")
        factors.append({"factor": "wind_threshold", "value": wind, "threshold": 30, "effect": "caution"})
    else:
        status = "SAFE"
        reasons.append("No prototype risk threshold triggered")

    ocean_mode = (ocean.get("source") or {}).get("mode")
    if ocean_mode in {"fallback", "unavailable"}:
        reasons.append("Ocean/PFZ source is using fallback or unavailable data")
        factors.append({"factor": "ocean_data_mode", "value": ocean_mode, "effect": "provenance_warning"})

    if geo.get("eez_status") in {"unavailable", "unsupported-location"}:
        reasons.append("Authoritative geographic layers are unavailable")
        factors.append({"factor": "geo_data", "value": geo.get("eez_status"), "effect": "provenance_warning"})

    return {
        "status": status,
        "score": score,
        "risk_band": _band(score),
        "confidence": _confidence(ocean, weather, geo),
        "reasons": reasons,
        "factors": factors,
        "decision_mode": "deterministic_prototype",
    }
