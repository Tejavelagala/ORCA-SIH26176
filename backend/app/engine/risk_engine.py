def evaluate(ocean: dict, weather: dict, geo: dict):
    reasons = []
    factors = []

    wind = weather.get("wind_speed_kmh")
    wave = weather.get("wave_height_m")
    cyclone = bool(weather.get("cyclone_warning"))
    restricted = bool(geo.get("restricted_zone"))

    # Safety-critical geographic restriction takes precedence.
    if restricted:
        return {
            "status": "BLOCKED",
            "reasons": ["Restricted GIS zone detected"],
            "factors": [{"factor": "geographic_restriction", "value": True, "effect": "block"}],
            "decision_mode": "deterministic_prototype",
        }

    # An explicit warning takes precedence over numerical conditions.
    if cyclone:
        return {
            "status": "UNSAFE",
            "reasons": ["Marine/cyclone warning flag detected"],
            "factors": [{"factor": "marine_warning", "value": True, "effect": "unsafe"}],
            "decision_mode": "deterministic_prototype",
        }

    # Fail closed: unavailable critical inputs must never become SAFE.
    missing = []
    if wind is None:
        missing.append("wind speed")
    if wave is None:
        missing.append("wave height")

    if missing:
        return {
            "status": "DATA_UNAVAILABLE",
            "reasons": ["Critical environmental data unavailable: " + ", ".join(missing)],
            "factors": [{"factor": "missing_critical_data", "value": missing, "effect": "unknown"}],
            "decision_mode": "deterministic_prototype",
        }

    if wave >= 3:
        status = "UNSAFE"
        reasons.append("Prototype high-wave threshold triggered")
        factors.append({"factor": "wave_height_m", "value": wave, "threshold": 3, "effect": "unsafe"})
    elif wave >= 2:
        status = "CAUTION"
        reasons.append("Prototype elevated-wave threshold triggered")
        factors.append({"factor": "wave_height_m", "value": wave, "threshold": 2, "effect": "caution"})
    elif wind >= 30:
        status = "CAUTION"
        reasons.append("Prototype high-wind threshold triggered")
        factors.append({"factor": "wind_speed_kmh", "value": wind, "threshold": 30, "effect": "caution"})
    else:
        status = "SAFE"
        reasons.append("No prototype risk threshold triggered")
        factors.append({"factor": "wind_wave", "value": {"wind_kmh": wind, "wave_m": wave}, "effect": "no_threshold"})

    # Ocean/PFZ availability is reported separately; it is not treated as a
    # safety guarantee because PFZ suitability and navigation safety are different concepts.
    ocean_mode = (ocean.get("source") or {}).get("mode")
    if ocean_mode in {"fallback", "unavailable"}:
        reasons.append("Ocean/PFZ source is using fallback or unavailable data")
        factors.append({"factor": "ocean_data_mode", "value": ocean_mode, "effect": "provenance_warning"})

    if geo.get("eez_status") == "unavailable":
        reasons.append("Authoritative geographic layers are unavailable")
        factors.append({"factor": "geo_data", "value": "unavailable", "effect": "provenance_warning"})

    return {
        "status": status,
        "reasons": reasons,
        "factors": factors,
        "decision_mode": "deterministic_prototype",
    }
