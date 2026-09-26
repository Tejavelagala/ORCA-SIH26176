from datetime import datetime, timedelta


def _clamp(value, low=0, high=100):
    return max(low, min(high, value))


def build_fishing_intelligence(pfz: dict | None, source_mode: str = "demo") -> dict:
    if not pfz:
        return {
            "available": False,
            "mode": "unavailable",
            "candidates": [],
            "note": "No PFZ geometry is available for this location.",
        }

    # Prototype heuristic. When authoritative SST/chlorophyll layers are
    # connected, these fields can be replaced without changing the API.
    sst = float(pfz.get("sst_c", 28.4))
    chlorophyll = float(pfz.get("chlorophyll_mg_m3", 0.42))
    distance = float(pfz.get("distance_km", 20))

    sst_score = _clamp(100 - abs(sst - 28.0) * 18)
    chl_score = _clamp(chlorophyll / 1.2 * 100)
    distance_score = _clamp(100 - distance * 2.0)
    fishing_score = round(0.45 * sst_score + 0.40 * chl_score + 0.15 * distance_score)

    if fishing_score >= 75:
        band = "HIGH"
    elif fishing_score >= 50:
        band = "MODERATE"
    else:
        band = "LOW"

    tomorrow = datetime.now() + timedelta(days=1)
    return {
        "available": True,
        "mode": "demo_heuristic" if source_mode != "live" else "live_inputs_heuristic",
        "fishing_score": fishing_score,
        "band": band,
        "candidates": [{
            "rank": 1,
            "name": pfz.get("name", "PFZ candidate"),
            "latitude": pfz.get("latitude"),
            "longitude": pfz.get("longitude"),
            "distance_km": round(distance, 1),
            "direction": pfz.get("direction"),
            "sst_c": sst,
            "chlorophyll_mg_m3": chlorophyll,
            "indicative_species": ["Indian mackerel", "oil sardine"],
            "best_window": f"{tomorrow.date().isoformat()} 05:30–09:30 IST",
            "score": fishing_score,
        }],
        "factors": [
            {"factor": "sst_suitability", "score": round(sst_score), "value": sst},
            {"factor": "chlorophyll_suitability", "score": round(chl_score), "value": chlorophyll},
            {"factor": "distance", "score": round(distance_score), "value_km": round(distance, 1)},
        ],
        "disclaimer": "Prototype fishing heuristic; species and timing are indicative and not an authoritative fisheries forecast.",
    }
