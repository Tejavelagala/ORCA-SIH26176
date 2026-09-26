from app.services.ocean_service import get_pfz


async def get_ocean(location: str):
    data = await get_pfz(location)

    return {
        "agent": "Ocean Agent",
        "pfz": data["pfz"],
        "source": data["source"],
        "data_mode": data["source"]["mode"],
    }
