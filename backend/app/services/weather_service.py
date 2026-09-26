import asyncio

import httpx

from app.services.provider_metadata import source_metadata

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"

DEMO_WEATHER = {
    "temperature_c": 30.8,
    "wind_speed_kmh": 14.8,
    "wave_height_m": 0.58,
    "rain_probability_pct": 3,
}


async def get_weather(lat: float, lon: float):
    weather_params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m",
        "hourly": "precipitation_probability,wind_speed_10m",
        "forecast_days": 2,
        "timezone": "Asia/Kolkata",
    }

    marine_params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "wave_height",
        "forecast_days": 2,
        "timezone": "Asia/Kolkata",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            weather_response, marine_response = await asyncio.gather(
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

        times = hourly.get("time", [])
        marine_times = marine_hourly.get("time", [])
        wind_values = hourly.get("wind_speed_10m", [])
        rain_values = hourly.get("precipitation_probability", [])
        wave_values = marine_hourly.get("wave_height", [])

        target_index = 0
        for index, timestamp in enumerate(times):
            if "T08:00" in str(timestamp):
                target_index = index
                break

        marine_index = min(target_index, len(marine_times) - 1) if marine_times else target_index
        wind = wind_values[target_index] if target_index < len(wind_values) else None
        rain = rain_values[target_index] if target_index < len(rain_values) else None
        waves = wave_values[marine_index] if marine_index < len(wave_values) else None
        forecast_time = times[target_index] if target_index < len(times) else None

        return {
            "agent": "Weather Agent",
            "provider": "Open-Meteo",
            "temperature_c": current.get("temperature_2m"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "wave_height_m": waves[0] if waves else None,
            "rain_probability_pct": rain,
            "cyclone_warning": False,
            "forecast_time": forecast_time,
            "forecast_period": "tomorrow_morning_prototype",
            "data_mode": "live",
            "source": source_metadata(
                provider="Open-Meteo Weather + Marine",
                mode="live",
                note="Prototype live weather/marine provider; authoritative IMD marine warnings should be integrated separately.",
            ),
        }
    except (httpx.HTTPError, ValueError, KeyError, IndexError):
        return {
            "agent": "Weather Agent",
            "provider": "Open-Meteo",
            **DEMO_WEATHER,
            "cyclone_warning": False,
            "forecast_time": None,
            "forecast_period": "demo_fallback",
            "data_mode": "demo",
            "source": source_metadata(
                provider="ORCA Demo Weather Profile",
                mode="demo",
                note="Live weather/marine provider unavailable; demo values are used for presentation only and must not be treated as navigation guidance.",
            ),
        }
