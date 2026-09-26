import asyncio
from datetime import datetime, timedelta

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


def _tomorrow_morning_index(times):
    if not times:
        return None

    tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
    for index, timestamp in enumerate(times):
        if str(timestamp).startswith(tomorrow + "T08:"):
            return index

    # Fallback to the first tomorrow-morning point available.
    for index, timestamp in enumerate(times):
        if str(timestamp).startswith(tomorrow + "T"):
            hour = int(str(timestamp)[11:13])
            if 6 <= hour <= 11:
                return index

    return 0


async def get_weather(lat: float, lon: float):
    weather_params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m",
        "hourly": "temperature_2m,precipitation_probability,wind_speed_10m",
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

        hourly = weather.get("hourly", {})
        marine_hourly = marine.get("hourly", {})

        times = hourly.get("time", [])
        marine_times = marine_hourly.get("time", [])
        temperature_values = hourly.get("temperature_2m", [])
        wind_values = hourly.get("wind_speed_10m", [])
        rain_values = hourly.get("precipitation_probability", [])
        wave_values = marine_hourly.get("wave_height", [])

        target_index = _tomorrow_morning_index(times)
        if target_index is None:
            raise ValueError("No forecast timestamps returned")

        forecast_time = times[target_index]
        target_temperature = (
            temperature_values[target_index]
            if target_index < len(temperature_values) else None
        )
        target_wind = (
            wind_values[target_index]
            if target_index < len(wind_values) else None
        )
        target_rain = (
            rain_values[target_index]
            if target_index < len(rain_values) else None
        )

        marine_index = None
        for index, timestamp in enumerate(marine_times):
            if str(timestamp) == str(forecast_time):
                marine_index = index
                break
        if marine_index is None and marine_times:
            marine_index = min(target_index, len(marine_times) - 1)

        target_wave = (
            wave_values[marine_index]
            if marine_index is not None and marine_index < len(wave_values)
            else None
        )

        return {
            "agent": "Weather Agent",
            "provider": "Open-Meteo",
            "temperature_c": target_temperature,
            "wind_speed_kmh": target_wind,
            "wave_height_m": target_wave,
            "rain_probability_pct": target_rain,
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
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
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
