import asyncio

from app.services.imd_service import get_marine_warning
from app.services.weather_service import get_weather
from app.services.geo_service import COORDS


async def run(location: str):
    normalized = (location or "").strip().lower()
    if normalized not in COORDS:
        return {
            "agent": "Weather Agent",
            "provider": "none",
            "temperature_c": None,
            "wind_speed_kmh": None,
            "wave_height_m": None,
            "rain_probability_pct": None,
            "cyclone_warning": False,
            "marine_warning": {
                "available": False,
                "text": None,
                "source": {
                    "provider": "Weather Agent",
                    "mode": "unavailable",
                    "note": "Unsupported prototype location.",
                },
            },
            "forecast_time": None,
            "forecast_period": "unavailable",
            "data_mode": "unavailable",
            "source": {
                "provider": "Weather Agent",
                "mode": "unavailable",
                "note": f"Location '{location}' is not configured.",
            },
        }

    lat, lon = COORDS[normalized]

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
