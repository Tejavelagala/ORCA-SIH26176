from shapely.geometry import Point, Polygon

from app.services.provider_metadata import source_metadata

# Prototype geometry only. Replace with authoritative GIS layers.
SAFE_AREA = Polygon([
    (81.8, 16.5),
    (83.0, 16.5),
    (83.0, 17.5),
    (81.8, 17.5),
])

COORDS = {
    "kakinada": (82.2475, 16.9891),
    "visakhapatnam": (83.2185, 17.6868),
    "chennai": (80.2707, 13.0827),
}


async def get_geo(location: str) -> dict:
    lon, lat = COORDS.get(location.lower(), COORDS["kakinada"])
    inside = SAFE_AREA.contains(Point(lon, lat))

    return {
        "inside_demo_safe_area": inside,
        "restricted_zone": False,
        "eez_status": "prototype-check",
        "coordinates": {"latitude": lat, "longitude": lon},
        "source": source_metadata(
            provider="ORCA demo GIS layer",
            mode="demo",
            note="Replace demo geometry with authoritative EEZ/IMBL/MPA GIS layers.",
        ),
    }
