import asyncio

from app.agents.ocean_agent import get_ocean
from app.agents.weather_agent import run as weather_run
from app.agents.geo_agent import run as geo_run
from app.engine.risk_engine import evaluate
from app.engine.route_engine import recommend_route
from app.services.provider_metadata import utc_now_iso


async def run_query(query: str, location: str):
    # Agents run concurrently so the slowest live provider does not block
    # the other independent data sources from starting.
    ocean, weather, geo = await asyncio.gather(
        get_ocean(location),
        weather_run(location),
        geo_run(location),
    )

    risk = evaluate(ocean, weather, geo)
    route = recommend_route(ocean)

    return {
        "query": query,
        "location": location,
        "generated_at": utc_now_iso(),
        "risk": risk,
        "agents": {
            "ocean": ocean,
            "weather": weather,
            "geo": geo,
        },
        "route": route,
        "explanation": build_explanation(risk, ocean, weather, geo),
    }


def build_explanation(risk, ocean, weather, geo):
    pfz = ocean["pfz"]

    return (
        f"ORCA classified the request as {risk['status']}. "
        f"PFZ reference: {pfz['distance_km']} km {pfz['direction']}. "
        f"Wind: {weather.get('wind_speed_kmh')} km/h; "
        f"wave height: {weather.get('wave_height_m')} m. "
        f"Geo restricted-zone flag: {geo.get('restricted_zone')}."
    )
