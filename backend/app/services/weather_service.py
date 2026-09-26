import httpx

async def get_weather(lat: float, lon: float):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m",
        "hourly": "precipitation_probability,wind_speed_10m,wave_height",
        "forecast_days": 1,
        "timezone": "Asia/Kolkata"
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    current = data.get("current", {})
    hourly = data.get("hourly", {})
    waves = hourly.get("wave_height", [None])
    rain = hourly.get("precipitation_probability", [None])

    return {
        "agent": "Weather Agent",
        "provider": "Open-Meteo",
        "temperature_c": current.get("temperature_2m"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "wave_height_m": waves[0] if waves else None,
        "rain_probability_pct": rain[0] if rain else None,
        "cyclone_warning": False,
        "data_mode": "live"
    }
