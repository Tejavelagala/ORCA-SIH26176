from heapq import heappop, heappush
from math import atan2, cos, radians, sin, sqrt


def _bearing_degrees(start_lat, start_lon, end_lat, end_lon):
    lat1 = radians(start_lat)
    lat2 = radians(end_lat)
    delta_lon = radians(end_lon - start_lon)
    x = sin(delta_lon) * cos(lat2)
    y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(delta_lon)
    return (atan2(x, y) * 180 / 3.141592653589793 + 360) % 360


def _distance_km(start_lat, start_lon, end_lat, end_lon):
    earth_radius_km = 6371.0
    lat1 = radians(start_lat)
    lat2 = radians(end_lat)
    delta_lat = radians(end_lat - start_lat)
    delta_lon = radians(end_lon - start_lon)
    a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    return earth_radius_km * 2 * atan2(sqrt(a), sqrt(max(0.0, 1 - a)))


def _compass(bearing):
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return directions[round(bearing / 45) % 8]


def _blocked(point, layers):
    lon, lat = point
    try:
        from shapely.geometry import Point, shape
        p = Point(lon, lat)
        return any(layer.get("restricted") and shape(layer["geometry"]).contains(p) for layer in layers if layer.get("geometry"))
    except Exception:
        return False


def _astar_reference(start, goal, layers, steps=12):
    if not layers:
        return [start, goal]

    min_lon, max_lon = sorted((start[0], goal[0]))
    min_lat, max_lat = sorted((start[1], goal[1]))
    pad_lon = max(0.04, (max_lon - min_lon) * 0.45)
    pad_lat = max(0.04, (max_lat - min_lat) * 0.45)
    min_lon -= pad_lon
    max_lon += pad_lon
    min_lat -= pad_lat
    max_lat += pad_lat

    cols = rows = max(8, min(24, steps + 4))
    nodes = {}
    for x in range(cols + 1):
        for y in range(rows + 1):
            lon = min_lon + (max_lon - min_lon) * x / cols
            lat = min_lat + (max_lat - min_lat) * y / rows
            nodes[(x, y)] = (lon, lat)

    def nearest(point):
        return min(nodes, key=lambda n: (nodes[n][0] - point[0]) ** 2 + (nodes[n][1] - point[1]) ** 2)

    start_node = nearest(start)
    goal_node = nearest(goal)
    if _blocked(start, layers) or _blocked(goal, layers):
        return None

    def h(node):
        p = nodes[node]
        return (p[0] - goal[0]) ** 2 + (p[1] - goal[1]) ** 2

    open_set = [(h(start_node), 0.0, start_node)]
    came_from = {}
    cost = {start_node: 0.0}

    while open_set:
        _, current_cost, current = heappop(open_set)
        if current == goal_node:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return [start, *[nodes[n] for n in path[1:-1]], goal]

        x, y = current
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            nxt = (x + dx, y + dy)
            if nxt not in nodes:
                continue
            point = nodes[nxt]
            if _blocked(point, layers):
                continue
            step = (point[0] - nodes[current][0]) ** 2 + (point[1] - nodes[current][1]) ** 2
            new_cost = current_cost + step
            if new_cost < cost.get(nxt, float("inf")):
                cost[nxt] = new_cost
                came_from[nxt] = current
                heappush(open_set, (new_cost + h(nxt), new_cost, nxt))

    return None


def recommend_route(ocean: dict, risk: dict | None = None, geo: dict | None = None):
    pfz = ocean.get("pfz") or {}
    start = ocean.get("query_coordinates")
    destination = None
    if pfz.get("latitude") is not None and pfz.get("longitude") is not None:
        destination = {"latitude": pfz["latitude"], "longitude": pfz["longitude"]}

    route = {
        "destination": pfz.get("name", "PFZ reference"),
        "direction": pfz.get("direction"),
        "distance_km": pfz.get("distance_km"),
        "route_mode": "straight_line_reference",
        "safe_to_navigate": False if risk and risk.get("status") in {"UNSAFE", "BLOCKED", "DATA_UNAVAILABLE"} else True,
        "optimization": "geofence_aware_a_star_reference",
        "waypoints": [],
        "note": "Prototype route-planning reference; not operational navigation.",
    }

    if start and destination:
        start_pair = (start["longitude"], start["latitude"])
        goal_pair = (destination["longitude"], destination["latitude"])
        bearing = _bearing_degrees(start["latitude"], start["longitude"], destination["latitude"], destination["longitude"])
        distance = _distance_km(start["latitude"], start["longitude"], destination["latitude"], destination["longitude"])

        layers = (geo or {}).get("matched_layers", [])
        path = _astar_reference(start_pair, goal_pair, layers) if layers else [start_pair, goal_pair]

        route["distance_km"] = round(distance, 1)
        route["direction"] = _compass(bearing)
        route["computed_bearing_degrees"] = round(bearing, 1)
        route["computed_direction"] = _compass(bearing)
        route["waypoints"] = [{"latitude": round(lat, 5), "longitude": round(lon, 5)} for lon, lat in (path or [])]
        route["route_mode"] = "geofence_aware_a_star_reference" if layers and path else "straight_line_reference"
        if layers and path is None:
            route["safe_to_navigate"] = False
            route["note"] = "No geofence-safe prototype path was found; not operational navigation."

    return route
