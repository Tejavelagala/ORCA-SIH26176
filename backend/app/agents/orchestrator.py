import asyncio

from app.agents.ocean_agent import get_ocean
from app.agents.weather_agent import run as weather_run
from app.agents.geo_agent import run as geo_run
from app.engine.risk_engine import evaluate
from app.engine.route_engine import recommend_route
from app.services.provider_metadata import utc_now_iso
from app.services.explanation_service import generate_explanation


async def run_query(query: str, location: str, language: str = "en-IN"):
    ocean, weather, geo = await asyncio.gather(
        get_ocean(location),
        weather_run(location),
        geo_run(location),
    )

    risk = evaluate(ocean, weather, geo)
    route = recommend_route(
        {**ocean, "query_coordinates": geo.get("coordinates")},
        risk,
    )

    explanation = await generate_explanation(
        query, risk, ocean, weather, geo, language
    )

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
        "explanation": explanation["text"],
        "explanation_mode": explanation["mode"],
        "language": language,
    }


def build_explanation(risk, ocean, weather, geo):
    # The LLM is intentionally not used for the safety decision.
    # This layer only turns already-computed structured evidence into
    # a concise human-readable explanation.
    status = risk.get("status", "UNKNOWN")
    wind = weather.get("wind_speed_kmh")
    wave = weather.get("wave_height_m")
    pfz = ocean.get("pfz") or {}
    geo_status = geo.get("eez_status", "unknown")

    parts = [
        f"ORCA classified the request as {status}.",
        f"Wind is {wind} km/h and wave height is {wave} m.",
    ]

    if pfz.get("name"):
        parts.append(
            f"PFZ reference: {pfz['name']} at "
            f"{pfz.get('distance_km', 'N/A')} km {pfz.get('direction', '')}."
        )

    if geo_status == "unavailable":
        parts.append("Authoritative geographic layers are currently unavailable.")

    reasons = risk.get("reasons") or []
    if reasons:
        parts.append("Reason: " + "; ".join(reasons[:2]) + ".")

    return {
        "mode": "deterministic_template",
        "text": " ".join(parts),
    }
