import httpx

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"

async def get_weather(lat: float, lon: float):
    weather_params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m",
        "hourly": "precipitation_probability,wind_speed_10m",
        "forecast_days": 1,
        "timezone": "Asia/Kolkata",
    }

    marine_params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "wave_height",
        "forecast_days": 1,
        "timezone": "Asia/Kolkata",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        weather_response, marine_response = await __import__("asyncio").gather(
            client.get(WEATHER_URL, params=weather_params),
            client.get(MARINE_URL, params=marine_params),
        )
        weather_response.raise_for_status()
        marine_response.raise_for_status()

    weather = weather_response.json()
    marine = marine_response.json()

    current = weather.get("current", {})
    hourly = weather.get("hourly", {})
    marine_hourly = marine.get("hourly", {})

    wind = hourly.get("wind_speed_10m", [None])
    rain = hourly.get("precipitation_probability", [None])
    waves = marine_hourly.get("wave_height", [None])

    return {
        "agent": "Weather Agent",
        "provider": "Open-Meteo",
        "temperature_c": current.get("temperature_2m"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "wave_height_m": waves[0] if waves else None,
        "rain_probability_pct": rain[0] if rain else None,
        "cyclone_warning": False,
        "data_mode": "live",
    }
