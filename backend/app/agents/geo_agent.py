from shapely.geometry import Point, Polygon

# Prototype geometry only. Replace with authoritative GIS layers for production.
SAFE_AREA = Polygon([
    (81.8, 16.5), (83.0, 16.5), (83.0, 17.5), (81.8, 17.5)
])

async def run(location: str):
    coords = {"kakinada": (82.2475, 16.9891), "visakhapatnam": (83.2185, 17.6868)}
    lon, lat = coords.get(location.lower(), coords["kakinada"])
    inside = SAFE_AREA.contains(Point(lon, lat))
    return {
        "agent": "Geo Agent",
        "inside_demo_safe_area": inside,
        "restricted_zone": False,
        "eez_status": "prototype-check",
        "data_mode": "demo"
    }
