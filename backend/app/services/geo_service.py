import json
import os
from pathlib import Path
from typing import Dict

from shapely.geometry import Point, shape

from app.services.provider_metadata import source_metadata

COORDS = {
    "kakinada": (82.2475, 16.9891),
    "visakhapatnam": (83.2185, 17.6868),
    "chennai": (80.2707, 13.0827),
}


def _load_layers(path: Path) -> list:
    if not path.exists():
        return []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, list) else []
    except (OSError, ValueError):
        return []


def _check_layers(lon: float, lat: float, layers: list) -> Dict:
    point = Point(lon, lat)
    hits = []

    for layer in layers:
        try:
            geometry = shape(layer["geometry"])
            if geometry.contains(point) or geometry.touches(point):
                hits.append({
                    "name": layer.get("name", "Unnamed layer"),
                    "type": layer.get("type", "unknown"),
                    "restricted": bool(layer.get("restricted", False)),
                })
        except (KeyError, TypeError, ValueError):
            continue

    return {
        "matched_layers": hits,
        "restricted_zone": any(item["restricted"] for item in hits),
    }


async def get_geo(location: str) -> dict:
    lon, lat = COORDS.get(location.lower(), COORDS["kakinada"])

    # Demo/authoritative GIS is opt-in. This prevents the bundled demo polygon
    # from accidentally blocking the default Kakinada demo scenario.
    configured = os.getenv("GEO_LAYERS_PATH", "").strip()

    if not configured:
        return {
            "matched_layers": [],
            "inside_demo_safe_area": None,
            "restricted_zone": False,
            "eez_status": "unavailable",
            "coordinates": {"latitude": lat, "longitude": lon},
            "source": source_metadata(
                provider="Geo Agent",
                mode="unavailable",
                note=(
                    "No authoritative GIS layer is configured. The bundled "
                    "demo geometry is not used for safety decisions."
                ),
            ),
        }

    layer_path = Path(configured)
    layers = _load_layers(layer_path)

    if layers:
        result = _check_layers(lon, lat, layers)
        return {
            **result,
            "inside_demo_safe_area": None,
            "eez_status": "configured-gis-check",
            "coordinates": {"latitude": lat, "longitude": lon},
            "source": source_metadata(
                provider="Configured GeoJSON GIS layers",
                mode="configured",
                note="Point-in-polygon evaluation against locally configured GIS layers.",
            ),
        }

    return {
        "matched_layers": [],
        "inside_demo_safe_area": None,
        "restricted_zone": False,
        "eez_status": "unavailable",
        "coordinates": {"latitude": lat, "longitude": lon},
        "source": source_metadata(
            provider="Geo Agent",
            mode="unavailable",
            note="Configured GIS layer could not be loaded; no restricted-zone inference made.",
        ),
    }
