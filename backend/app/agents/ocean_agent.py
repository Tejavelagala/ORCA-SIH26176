from app.services.ocean_service import get_pfz
from app.services.satellite_service import satellite_status
from app.services.fishing_service import build_fishing_intelligence


async def get_ocean(location: str):
    data = await get_pfz(location)
    fishing = build_fishing_intelligence(
        data.get("pfz"),
        data.get("source", {}).get("mode", "unknown"),
    )

    return {
        "agent": "Ocean Agent",
        "pfz": data["pfz"],
        "advisory": data.get("advisory"),
        "geometry_mode": data.get("geometry_mode", "unknown"),
        "satellite": satellite_status(),
        "fishing_intelligence": fishing,
        "source": data["source"],
        "data_mode": data["source"]["mode"],
    }
