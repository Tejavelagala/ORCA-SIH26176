from app.services.geo_service import get_geo


async def run(location: str):
    data = await get_geo(location)

    return {
        "agent": "Geo Agent",
        **data,
        "data_mode": data["source"]["mode"],
    }
