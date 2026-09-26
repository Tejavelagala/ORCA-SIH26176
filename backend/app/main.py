import os

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.agents.orchestrator import run_query
from app.agents.intent_agent import classify_intent
from app.engine.risk_engine import evaluate
from app.engine.route_engine import recommend_route
from app.services.provider_metadata import source_metadata, utc_now_iso
from app.services.geo_service import COORDS
from app.services.knowledge_service import knowledge_status, search_knowledge
from app.services.resilience_service import build_escalation, build_fallback_message, channel_status, load_last_known_good
from app.services.satellite_service import satellite_status
from app.services.language_service import language_status, translate
from app.services.session_service import create_session, delete_session, get_session, session_status

app = FastAPI(
    title="ORCA Marine Intelligence API",
    description="SIH-26176 multi-agent marine decision-support prototype.",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEMO_SCENARIOS = {
    "safe": {"wind_speed_kmh": 14.8, "wave_height_m": 0.58, "cyclone_warning": False, "description": "Normal prototype sea conditions"},
    "caution": {"wind_speed_kmh": 35.0, "wave_height_m": 1.0, "cyclone_warning": False, "description": "Elevated prototype wind condition"},
    "unsafe": {"wind_speed_kmh": 18.0, "wave_height_m": 3.2, "cyclone_warning": False, "description": "High prototype wave condition"},
    "cyclone_alert": {"wind_speed_kmh": 22.0, "wave_height_m": 1.4, "cyclone_warning": True, "description": "Marine cyclone-warning scenario"},
    "blocked": {"wind_speed_kmh": 14.8, "wave_height_m": 0.58, "cyclone_warning": False, "description": "Configured restricted-zone scenario"},
    "data_unavailable": {"wind_speed_kmh": 14.8, "wave_height_m": None, "cyclone_warning": False, "description": "Critical wave data unavailable"},
}


@app.get("/")
def root():
    return {
        "name": "ORCA",
        "problem_statement": "SIH-26176",
        "product": "Marine EcOsystem Reasoning with Collaborative Agents",
        "status": "running",
        "architecture": [
            "Intent Agent", "LangGraph Orchestrator", "Ocean Agent",
            "Weather Agent", "Geo Agent", "Deterministic Risk Engine",
            "Route Context Engine", "Evidence / Explanation Layer",
        ],
    }


@app.get("/health")
def health():
    return {"status": "healthy", "service": "orca-api", "version": app.version}


@app.get("/api/system/status")
def system_status():
    kb = knowledge_status()
    return {
        "service": "ORCA",
        "version": app.version,
        "orchestration": "LangGraph with asyncio fallback",
        "llm_configured": bool(os.getenv("LLM_API_KEY")),
        "redis_configured": bool(os.getenv("REDIS_URL")),
        "postgres_configured": bool(os.getenv("DATABASE_URL")),
        "postgis_enabled_by_stack": bool(os.getenv("DATABASE_URL")),
        "imd_configured": bool(os.getenv("IMD_MARINE_URL")),
        "incois_configured": bool(os.getenv("INCOIS_PFZ_URL")),
        "gis_configured": bool(os.getenv("GEO_LAYERS_PATH")),
        "knowledge_base": kb,
        "supported_locations": sorted(COORDS.keys()),
        "languages": ["en-IN", "te-IN", "hi-IN"],
        "channels": channel_status(),
        "human_in_loop": True,
        "proactive_geofencing": True,
        "satellite": satellite_status(),
        "language_layer": language_status(),
        "sessions": session_status(),
    }


@app.get("/api/intent")
def intent(q: str):
    return classify_intent(q)


@app.get("/api/knowledge/search")
def knowledge_search(q: str, limit: int = Query(default=5, ge=1, le=10)):
    return {"query": q, "results": search_knowledge(q, limit), "status": knowledge_status()}


@app.get("/api/channels/status")
def channels_status():
    return channel_status()


@app.get("/api/offline/snapshot")
def offline_snapshot(location: str | None = None):
    snapshot = load_last_known_good(location)
    if not snapshot:
        raise HTTPException(status_code=404, detail="No last-known-good snapshot is available")
    return snapshot


@app.post("/api/fallback/message")
def fallback_message(payload: dict = Body(...)):
    channel = str(payload.get("channel", "sms")).lower()
    if channel not in {"sms", "ivr"}:
        raise HTTPException(status_code=400, detail="Channel must be sms or ivr")
    return build_fallback_message(payload.get("result") or payload, channel)


@app.post("/api/escalate")
def escalate(payload: dict = Body(...)):
    target = str(payload.get("target", "coast_guard"))
    if target not in {"coast_guard", "incois", "disaster_team"}:
        raise HTTPException(status_code=400, detail="Unsupported escalation target")
    return build_escalation(payload.get("result") or payload, target)


@app.post("/api/language/translate")
async def language_translate(payload: dict = Body(...)):
    text = str(payload.get("text", "")).strip()
    source_language = str(payload.get("source_language", "en-IN"))
    target_language = str(payload.get("target_language", "te-IN"))
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    if source_language not in {"en-IN", "te-IN", "hi-IN"} or target_language not in {"en-IN", "te-IN", "hi-IN"}:
        raise HTTPException(status_code=400, detail="Unsupported language")
    return await translate(text, source_language, target_language)


@app.get("/api/satellite/status")
def satellite_gateway_status():
    return satellite_status()


@app.get("/api/evidence/catalog")
def evidence_catalog():
    return {
        "sources": [
            {"provider": "INCOIS PFZ", "role": "Potential Fishing Zone advisory and ocean evidence", "url": "https://www.incois.gov.in/MarineFisheries/PfzWebGis"},
            {"provider": "INCOIS Ocean State Forecast", "role": "Marine wind/wave/ocean state evidence", "url": "https://www.incois.gov.in/oceanservices/osfforecast.jsp"},
            {"provider": "IMD Marine", "role": "Marine forecast/warning gateway", "url": "https://mausam.imd.gov.in/responsive/marine_forecast.php"},
            {"provider": "MOSDAC", "role": "ISRO satellite-data gateway", "url": "https://mosdac.gov.in/"},
            {"provider": "Bhuvan / GIS", "role": "Geospatial context and thematic layers", "url": "https://bhuvan.nrsc.gov.in/"},
            {"provider": "ORCA Risk Engine", "role": "Deterministic safety classification", "authoritative": True},
        ]
    }


@app.post("/api/session")
def create_orca_session(payload: dict = Body(default={})):
    language = str(payload.get("language", "en-IN"))
    location = str(payload.get("location", "Kakinada"))
    mission = str(payload.get("mission", "fisher"))
    if language not in {"en-IN", "te-IN", "hi-IN"}:
        raise HTTPException(status_code=400, detail="Unsupported language")
    if location.strip().lower() not in COORDS:
        raise HTTPException(status_code=400, detail="Unsupported prototype location")
    return create_session(language=language, location=location, mission=mission)


@app.get("/api/session/{session_id}")
def read_orca_session(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    return {**session, "status": "active"}


@app.delete("/api/session/{session_id}")
def remove_orca_session(session_id: str):
    if not delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted", "session_id": session_id}


@app.get("/api/session/status")
def orca_session_status():
    return session_status()


@app.get("/api/authority/dashboard")
async def authority_dashboard():
    import asyncio
    locations = sorted(COORDS.keys())
    query_text = "Give the current marine authority situation brief with risk, weather, waves, PFZ and geographic restrictions."
    results = await asyncio.gather(
        *(run_query(query_text, location, "en-IN") for location in locations)
    )
    centres = []
    for item in results:
        centres.append({
            "location": item.get("location"),
            "status": item.get("risk", {}).get("status"),
            "score": item.get("risk", {}).get("score"),
            "risk_band": item.get("risk", {}).get("risk_band"),
            "confidence": item.get("risk", {}).get("confidence"),
            "wind_speed_kmh": item.get("agents", {}).get("weather", {}).get("wind_speed_kmh"),
            "wave_height_m": item.get("agents", {}).get("weather", {}).get("wave_height_m"),
            "rain_probability_pct": item.get("agents", {}).get("weather", {}).get("rain_probability_pct"),
            "cyclone_warning": item.get("agents", {}).get("weather", {}).get("cyclone_warning"),
            "restricted_zone": item.get("agents", {}).get("geo", {}).get("restricted_zone"),
            "forecast_time": item.get("agents", {}).get("weather", {}).get("forecast_time"),
            "source_modes": item.get("evidence_summary", {}),
        })
    counts = {}
    for centre in centres:
        counts[centre["status"]] = counts.get(centre["status"], 0) + 1
    alerts = [
        {
            "location": centre["location"],
            "status": centre["status"],
            "score": centre["score"],
            "message": (
                "Cyclone warning active" if centre["cyclone_warning"]
                else "Restricted zone detected" if centre["restricted_zone"]
                else "Elevated marine risk" if centre["status"] in {"CAUTION", "UNSAFE"}
                else "No prototype threshold alert"
            ),
        }
        for centre in centres
    ]
    return {
        "generated_at": utc_now_iso(),
        "scope": "configured ORCA prototype locations",
        "summary": counts,
        "centres": centres,
        "alerts": alerts,
        "risk_authority": "deterministic_risk_engine",
        "disclaimer": "Authority dashboard is a prototype operational view; thresholds and provider coverage are not official regulatory guidance.",
    }


@app.get("/api/query")
async def query(q: str, location: str = "Kakinada", language: str = "en-IN", session_id: str | None = None):
    if language not in {"en-IN", "te-IN", "hi-IN"}:
        raise HTTPException(status_code=400, detail="Unsupported language")
    return await run_query(q, location, language, session_id)


@app.get("/api/demo")
async def demo(scenario: str = "safe", location: str = "Kakinada"):
    key = scenario.lower().strip()
    if key not in DEMO_SCENARIOS:
        return {"error": "Unknown demo scenario", "available": list(DEMO_SCENARIOS.keys())}

    conditions = DEMO_SCENARIOS[key]
    normalized_location = location.strip().lower()
    if normalized_location not in COORDS:
        raise HTTPException(
            status_code=400,
            detail={"message": "Unsupported prototype location", "supported_locations": sorted(COORDS.keys())},
        )

    lon, lat = COORDS[normalized_location]
    pfz = {
        "location": location,
        "name": f"{location} PFZ Demo",
        "latitude": round(lat + 0.15, 4),
        "longitude": round(lon + 0.30, 4),
        "distance_km": 18,
        "direction": "NE",
    }
    restricted = key == "blocked"
    ocean = {
        "agent": "Ocean Agent",
        "pfz": pfz,
        "data_mode": "demo",
        "geometry_mode": "demo",
        "advisory": {"available": False, "url": None, "forecast_date": None, "valid_upto": None},
        "source": source_metadata(provider="ORCA Demo PFZ Profile", mode="demo", note="Demonstration data only."),
    }
    weather = {
        "agent": "Weather Agent",
        "provider": "ORCA Demo Scenario",
        "temperature_c": 30.8,
        "rain_probability_pct": 3,
        **{k: v for k, v in conditions.items() if k != "description"},
        "data_mode": "demo",
        "source": source_metadata(provider="ORCA Demo Scenario", mode="demo", note=conditions["description"]),
    }
    geo = {
        "matched_layers": [{"name": "Demo Restricted Marine Zone", "type": "restricted", "restricted": True}] if restricted else [],
        "restricted_zone": restricted,
        "eez_status": "demo",
        "data_mode": "demo",
        "coordinates": {"latitude": lat, "longitude": lon},
        "source": source_metadata(provider="ORCA Demo GIS", mode="demo", note=conditions["description"]),
    }

    risk = evaluate(ocean, weather, geo)
    trace = [
        {"stage": "Intent", "status": "completed", "detail": "Demo scenario routed to the ORCA workflow."},
        {"stage": "Ocean Agent", "status": "completed", "detail": "Demo PFZ evidence loaded."},
        {"stage": "Weather Agent", "status": "completed", "detail": f"Demo marine conditions loaded for {key.upper()}."},
        {"stage": "Geo Agent", "status": "completed", "detail": "Demo geospatial condition evaluated."},
        {"stage": "Risk Engine", "status": "completed", "detail": f"Deterministic rules produced {risk['status']}."},
        {"stage": "Explanation", "status": "completed", "detail": "Deterministic demo explanation generated."},
    ]
    route = recommend_route({**ocean, "query_coordinates": geo["coordinates"]}, risk, geo)

    return {
        "query": f"Demo scenario: {key}",
        "location": location,
        "intent": classify_intent(f"Demo scenario: {key}"),
        "orchestration": "demo_deterministic",
        "generated_at": utc_now_iso(),
        "risk": risk,
        "agents": {"ocean": ocean, "weather": weather, "geo": geo},
        "route": route,
        "explanation": f"ORCA demo scenario '{key}' produced {risk['status']} using the deterministic Risk Engine.",
        "explanation_mode": "demo_deterministic",
        "language": "en-IN",
        "trace": trace,
        "evidence_summary": {"risk_authority": "deterministic_risk_engine", "ocean_mode": "demo", "weather_mode": "demo", "geo_mode": "demo"},
    }
