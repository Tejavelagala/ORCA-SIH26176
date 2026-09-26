from math import atan2, cos, radians, sin, sqrt


def _bearing_degrees(start_lat, start_lon, end_lat, end_lon):
    lat1 = radians(start_lat)
    lat2 = radians(end_lat)
    delta_lon = radians(end_lon - start_lon)

    x = sin(delta_lon) * cos(lat2)
    y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(delta_lon)

    return (atan2(x, y) * 180 / 3.141592653589793 + 360) % 360


def _compass(bearing):
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return directions[round(bearing / 45) % 8]


def recommend_route(ocean: dict, risk: dict | None = None):
    pfz = ocean.get("pfz") or {}
    start = ocean.get("query_coordinates")

    route = {
        "destination": pfz.get("name", "PFZ reference"),
        "direction": pfz.get("direction"),
        "distance_km": pfz.get("distance_km"),
        "route_mode": "straight_line_prototype",
        "safe_to_navigate": False if risk and risk.get("status") in {"UNSAFE", "BLOCKED", "DATA_UNAVAILABLE"} else True,
        "note": "Prototype straight-line reference; not a navigational route.",
    }

    if start and pfz.get("latitude") is not None and pfz.get("longitude") is not None:
        bearing = _bearing_degrees(
            start["latitude"],
            start["longitude"],
            pfz["latitude"],
            pfz["longitude"],
        )
        route["computed_bearing_degrees"] = round(bearing, 1)
        route["computed_direction"] = _compass(bearing)

    return route
