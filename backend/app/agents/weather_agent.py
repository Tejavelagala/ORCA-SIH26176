import asyncio

from app.services.imd_service import get_marine_warning
from app.services.weather_service import get_weather

LOCATIONS = {
    "kakinada": (16.9891, 82.2475),
    "visakhapatnam": (17.6868, 83.2185),
    "chennai": (13.0827, 80.2707),
}


async def run(location: str):
    lat, lon = LOCATIONS.get(location.lower(), LOCATIONS["kakinada"])

    weather, warning = await asyncio.gather(
        get_weather(lat, lon),
        get_marine_warning(location),
    )

    weather["cyclone_warning"] = warning["cyclone_warning"]
    weather["marine_warning"] = {
        "available": warning["warning_available"],
        "text": warning["warning_text"],
        "source": warning["source"],
    }

    return weather
