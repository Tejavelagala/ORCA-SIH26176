from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agents.orchestrator import run_query
from app.engine.risk_engine import evaluate
from app.engine.route_engine import recommend_route
from app.services.provider_metadata import source_metadata, utc_now_iso
from app.services.geo_service import COORDS
from app.agents.intent_agent import classify_intent
import os

app = FastAPI(title="ORCA", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEMO_SCENARIOS = {
    "safe": {
        "wind_speed_kmh": 14.8,
        "wave_height_m": 0.58,
        "cyclone_warning": False,
        "description": "Normal prototype sea conditions",
    },
    "caution": {
        "wind_speed_kmh": 35.0,
        "wave_height_m": 1.0,
        "cyclone_warning": False,
        "description": "Elevated prototype wind condition",
    },
    "unsafe": {
        "wind_speed_kmh": 18.0,
        "wave_height_m": 3.2,
        "cyclone_warning": False,
        "description": "High prototype wave condition",
    },
    "blocked": {
        "wind_speed_kmh": 14.8,
        "wave_height_m": 0.58,
        "cyclone_warning": False,
        "description": "Configured restricted-zone scenario",
    },
    "data_unavailable": {
        "wind_speed_kmh": 14.8,
        "wave_height_m": None,
        "cyclone_warning": False,
        "description": "Critical wave data unavailable",
    },
}


@app.get("/")
def root():
    return {"name": "ORCA", "problem_statement": "SIH-26176", "status": "running"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "orca-api",
        "version": app.version,
    }


@app.get("/api/system/status")
def system_status():
    return {
        "service": "ORCA",
        "version": app.version,
        "orchestration": "LangGraph with asyncio fallback",
        "llm_configured": bool(os.getenv("LLM_API_KEY")),
        "redis_configured": bool(os.getenv("REDIS_URL")),
        "postgres_configured": bool(os.getenv("DATABASE_URL")),
        "imd_configured": bool(os.getenv("IMD_MARINE_URL")),
        "incois_configured": bool(os.getenv("INCOIS_PFZ_URL")),
        "gis_configured": bool(os.getenv("GEO_LAYERS_PATH")),
        "supported_locations": sorted(COORDS.keys()),
    }


@app.get("/api/intent")
def intent(q: str):
    return classify_intent(q)


@app.get("/api/query")
async def query(
    q: str,
    location: str = "Kakinada",
    language: str = "en-IN",
):
    return await run_query(q, location, language)


@app.get("/api/demo")
async def demo(
    scenario: str = "safe",
    location: str = "Kakinada",
):
    key = scenario.lower().strip()
    if key not in DEMO_SCENARIOS:
        return {
            "error": "Unknown demo scenario",
            "available": list(DEMO_SCENARIOS.keys()),
        }

    conditions = DEMO_SCENARIOS[key]
    normalized_location = location.strip().lower()
    if normalized_location not in COORDS:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported prototype location",
                "supported_locations": sorted(COORDS.keys()),
            },
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
        "source": source_metadata(
            provider="ORCA Demo PFZ Profile",
            mode="demo",
            note="Demonstration data only.",
        ),
    }
    weather = {
        "agent": "Weather Agent",
        "provider": "ORCA Demo Scenario",
        "temperature_c": 30.8,
        "rain_probability_pct": 3,
        **{k: v for k, v in conditions.items() if k != "description"},
        "data_mode": "demo",
        "source": source_metadata(
            provider="ORCA Demo Scenario",
            mode="demo",
            note=conditions["description"],
        ),
    }
    geo = {
        "matched_layers": (
            [{
                "name": "Demo Restricted Marine Zone",
                "type": "restricted",
                "restricted": True,
            }]
            if restricted else []
        ),
        "restricted_zone": restricted,
        "eez_status": "demo",
        "data_mode": "demo",
        "coordinates": {"latitude": lat, "longitude": lon},
        "source": source_metadata(
            provider="ORCA Demo GIS",
            mode="demo",
            note=conditions["description"],
        ),
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
    route = recommend_route({**ocean, "query_coordinates": geo["coordinates"]}, risk)

    return {
        "query": f"Demo scenario: {key}",
        "location": location,
        "generated_at": utc_now_iso(),
        "risk": risk,
        "agents": {"ocean": ocean, "weather": weather, "geo": geo},
        "route": route,
        "explanation": (
            f"ORCA demo scenario '{key}' produced {risk['status']} "
            "using the deterministic Risk Engine."
        ),
        "explanation_mode": "demo_deterministic",
        "language": "en-IN",
        "trace": trace,
    }
