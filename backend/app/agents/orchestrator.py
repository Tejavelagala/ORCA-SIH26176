import asyncio

from app.agents.graph_orchestrator import run_graph
from app.agents.intent_agent import classify_intent
from app.agents.ocean_agent import get_ocean
from app.agents.weather_agent import run as weather_run
from app.agents.geo_agent import run as geo_run
from app.engine.risk_engine import evaluate
from app.engine.route_engine import recommend_route
from app.services.provider_metadata import utc_now_iso
from app.services.explanation_service import generate_explanation
from app.services.cache_service import cache_key, get_json, set_json
from app.services.persistence_service import persist_query
from app.services.knowledge_service import search_knowledge
from app.services.resilience_service import save_last_known_good


async def run_query(query: str, location: str, language: str = "en-IN"):
    intent = classify_intent(query)
    key = cache_key(query, location, language)

    cached = await get_json(key)
    if cached:
        cached["cache"] = {"hit": True, "backend": "redis" if __import__("os").getenv("REDIS_URL") else "memory"}
        return cached

    graph_result = await run_graph(query, location, language, intent)
    if graph_result:
        result = graph_result
    else:
        ocean, weather, geo = await asyncio.gather(
            get_ocean(location),
            weather_run(location),
            geo_run(location),
        )

        risk = evaluate(ocean, weather, geo)
        route = recommend_route(
            {**ocean, "query_coordinates": geo.get("coordinates")},
            risk,
            geo,
        )

        explanation = await generate_explanation(
            query, risk, ocean, weather, geo, language
        )

        trace = [
            {"stage": "Intent", "status": "completed", "detail": f"Detected {intent.get('intent', 'general')} intent."},
            {"stage": "Ocean Agent", "status": "completed", "detail": f"PFZ/advisory evidence collected in {ocean.get('data_mode', 'unknown')} mode."},
            {"stage": "Weather Agent", "status": "completed", "detail": f"Weather and marine conditions collected in {weather.get('data_mode', 'unknown')} mode."},
            {"stage": "Geo Agent", "status": "completed", "detail": f"Geospatial check completed with status {geo.get('eez_status', 'unknown')}."},
            {"stage": "Risk Engine", "status": "completed", "detail": f"Deterministic rules produced {risk.get('status', 'UNKNOWN')}."},
            {"stage": "Explanation", "status": "completed", "detail": f"Evidence explanation generated in {explanation.get('mode', 'unknown')} mode."},
        ]

        result = {
            "query": query,
            "location": location,
            "generated_at": utc_now_iso(),
            "risk": risk,
            "agents": {"ocean": ocean, "weather": weather, "geo": geo},
            "route": route,
            "explanation": explanation["text"],
            "explanation_mode": explanation["mode"],
            "language": language,
            "intent": intent,
            "orchestration": "asyncio_fallback",
            "trace": trace,
        }

    weather_data = result.get("agents", {}).get("weather", {})
    geo_data = result.get("agents", {}).get("geo", {})
    ocean_data = result.get("agents", {}).get("ocean", {})
    timeline = []
    for point in (weather_data.get("forecast_series") or []):
        point_risk = evaluate(ocean_data, point, geo_data)
        timeline.append({
            "time": point.get("time"),
            "status": point_risk.get("status"),
            "score": point_risk.get("score"),
            "risk_band": point_risk.get("risk_band"),
            "confidence": point_risk.get("confidence"),
        })
    result["risk_timeline"] = timeline
    result["evidence_ledger"] = [
        {
            "metric": "wind_speed_kmh",
            "value": weather_data.get("wind_speed_kmh"),
            "unit": "km/h",
            "source": (weather_data.get("source") or {}).get("provider"),
            "mode": (weather_data.get("source") or {}).get("mode"),
            "timestamp": weather_data.get("forecast_time"),
        },
        {
            "metric": "wave_height_m",
            "value": weather_data.get("wave_height_m"),
            "unit": "m",
            "source": (weather_data.get("source") or {}).get("provider"),
            "mode": (weather_data.get("source") or {}).get("mode"),
            "timestamp": weather_data.get("forecast_time"),
        },
        {
            "metric": "pfz",
            "value": ocean_data.get("pfz"),
            "unit": "reference",
            "source": (ocean_data.get("source") or {}).get("provider"),
            "mode": (ocean_data.get("source") or {}).get("mode"),
            "timestamp": (ocean_data.get("advisory") or {}).get("forecast_date"),
        },
        {
            "metric": "geofence",
            "value": geo_data.get("matched_layers", []),
            "unit": "GIS layers",
            "source": (geo_data.get("source") or {}).get("provider"),
            "mode": (geo_data.get("source") or {}).get("mode"),
            "timestamp": None,
        },
    ]

    result["knowledge"] = {
        "provider": "ChromaDB",
        "results": search_knowledge(query, limit=4),
        "purpose": "grounding and source context only; never a safety decision",
    }
    result["cache"] = {"hit": False, "backend": "redis" if __import__("os").getenv("REDIS_URL") else "memory"}
    result["persistence"] = persist_query(result)
    result["evidence_summary"] = {
        "risk_authority": "deterministic_risk_engine",
        "ocean_mode": result.get("agents", {}).get("ocean", {}).get("source", {}).get("mode"),
        "weather_mode": result.get("agents", {}).get("weather", {}).get("source", {}).get("mode"),
        "geo_mode": result.get("agents", {}).get("geo", {}).get("source", {}).get("mode"),
    }
    await set_json(key, result, ttl_seconds=180)
    result["offline_snapshot"] = save_last_known_good(result)
    return result
