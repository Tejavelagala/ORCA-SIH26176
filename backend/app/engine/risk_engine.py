def evaluate(ocean: dict, weather: dict, geo: dict):
    reasons = []
    status = "SAFE"

    wind = weather.get("wind_speed_kmh")
    wave = weather.get("wave_height_m")

    # Prototype thresholds only; validate against authoritative maritime guidance
    # before using for real-world safety decisions.
    if geo.get("restricted_zone"):
        return {
            "status": "BLOCKED",
            "reasons": ["Restricted zone detected"],
            "decision_mode": "deterministic_prototype",
        }

    if weather.get("cyclone_warning"):
        return {
            "status": "UNSAFE",
            "reasons": ["Cyclone warning flag detected"],
            "decision_mode": "deterministic_prototype",
        }

    # Fail closed when critical environmental values are unavailable.
    # Missing data must never be treated as SAFE.
    if wind is None or wave is None:
        missing = []
        if wind is None:
            missing.append("wind speed")
        if wave is None:
            missing.append("wave height")

        return {
            "status": "DATA_UNAVAILABLE",
            "reasons": [
                "Critical environmental data unavailable: "
                + ", ".join(missing)
            ],
            "decision_mode": "deterministic_prototype",
        }

    if wave >= 3:
        status = "UNSAFE"
        reasons.append("Prototype wave threshold exceeded")
    elif wave >= 2 or wind >= 30:
        status = "CAUTION"
        reasons.append("Prototype caution threshold triggered")
    else:
        reasons.append("No prototype risk threshold triggered")

    return {
        "status": status,
        "reasons": reasons,
        "decision_mode": "deterministic_prototype",
    }
