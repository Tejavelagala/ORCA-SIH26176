def evaluate(ocean: dict, weather: dict, geo: dict):
    reasons = []
    status = "SAFE"

    wind = weather.get("wind_speed_kmh")
    wave = weather.get("wave_height_m")

    # Prototype thresholds only; validate against authoritative maritime guidance
    # before using for real-world safety decisions.
    if geo.get("restricted_zone"):
        return {"status": "BLOCKED", "reasons": ["Restricted zone detected"]}

    if weather.get("cyclone_warning"):
        return {"status": "UNSAFE", "reasons": ["Cyclone warning flag detected"]}

    if wave is not None and wave >= 3:
        status = "UNSAFE"
        reasons.append("Prototype wave threshold exceeded")
    elif (wave is not None and wave >= 2) or (wind is not None and wind >= 30):
        status = "CAUTION"
        reasons.append("Prototype caution threshold triggered")
    else:
        reasons.append("No prototype risk threshold triggered")

    return {"status": status, "reasons": reasons}
