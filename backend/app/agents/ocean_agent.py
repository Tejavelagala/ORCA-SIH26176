from app.services.ocean_service import get_pfz
from app.services.satellite_service import satellite_status


async def get_ocean(location: str):
    data = await get_pfz(location)

    return {
        "agent": "Ocean Agent",
        "pfz": data["pfz"],
        "advisory": data.get("advisory"),
        "geometry_mode": data.get("geometry_mode", "unknown"),
        "satellite": satellite_status(),
        "source": data["source"],
        "data_mode": data["source"]["mode"],
    }
