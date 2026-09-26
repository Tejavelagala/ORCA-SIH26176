from app.services.weather_service import get_weather

LOCATIONS = {
    "kakinada": (16.9891, 82.2475),
    "visakhapatnam": (17.6868, 83.2185),
    "chennai": (13.0827, 80.2707),
}


async def run(location: str):
    lat, lon = LOCATIONS.get(location.lower(), LOCATIONS["kakinada"])
    return await get_weather(lat, lon)
