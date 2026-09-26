# ORCA — SIH 2026 PS-26176

**Marine EcOsystem Reasoning with Collaborative Agents**

ORCA is a conversational multi-agent marine decision-support prototype aligned with the SIH presentation architecture: an Intent/Language layer routes the request, specialized Ocean/Weather/Geo agents collect evidence in parallel, LangGraph coordinates the workflow, a deterministic Risk Engine makes the safety classification, and an evidence/explanation layer produces the final brief.

## PPT-aligned technology stack

| Presentation technology / idea | Product implementation |
|---|---|
| Python | FastAPI backend |
| LangGraph / collaborative agents | LangGraph + asyncio fallback |
| Ocean Agent | INCOIS PFZ advisory adapter + explicit demo fallback |
| Weather Agent | Open-Meteo weather + marine forecast |
| Geo Agent | Shapely + configurable GeoJSON |
| ISRO / MOSDAC | Evidence gateway/catalog |
| INCOIS | PFZ + Ocean State Forecast gateways |
| IMD | Configurable marine warning adapter |
| ChromaDB | Persistent marine/source knowledge index |
| Indic language layer | English + Telugu + Hindi intent and response support |
| LLM | Optional grounded explanation only |
| PostgreSQL / PostGIS | Query/evidence persistence with spatial point storage |
| Redis | Response cache |
| React | Primary web application |
| Leaflet / OpenStreetMap | Marine evidence map |
| Voice / IVR-ready design | Browser speech input/output; API remains text-first |
| Docker | Backend + React + Redis + PostGIS Compose stack |

## Architecture

    User Query
        |
    Intent + Language
        |
    LangGraph Orchestrator
      /    |     Ocean  Weather  Geo
 Agent   Agent   Agent
          |    /
    Deterministic Risk Engine
        |
    Route Context + Evidence Summary
        |
    ChromaDB Knowledge Layer
        |
    Grounded Explanation
        |
    React + Leaflet + Voice UI

**Safety boundary:** the deterministic Risk Engine is authoritative. The LLM and ChromaDB layer cannot make, change, soften, or override a risk decision.

## Product capabilities

- Natural-language marine queries.
- Fisher, Ship Operator, Coast Guard and Disaster Team mission modes.
- Parallel specialized agents.
- Five explicit risk states: SAFE, CAUTION, UNSAFE, BLOCKED and DATA_UNAVAILABLE.
- Explainable 0–100 risk score, risk band and confidence estimate.
- Multi-morning risk timeline from the marine forecast series.
- Auditable evidence ledger for key environmental and geospatial metrics.
- PFZ fishing-intelligence heuristic using SST, chlorophyll and distance with indicative species/window metadata.
- Geofence-aware A* reference route planning.
- Tomorrow-morning weather targeting.
- INCOIS PFZ advisory metadata and provenance.
- Configurable IMD warning adapter.
- Configurable GIS point-in-polygon checks.
- PostGIS-backed evidence/query persistence.
- Redis response caching.
- ChromaDB marine/source knowledge index with deterministic fallback.
- English, Telugu and Hindi intent/response support.
- Optional grounded OpenAI-compatible explanation model.
- Route distance, bearing and direction context.
- Leaflet evidence map.
- Marine Alert Watch.
- Deterministic presentation scenarios for all five risk states.
- Source/evidence catalog API.
- System capability/status API.
- Dockerized product stack.
- MOSDAC satellite evidence gateway and multi-satellite-ready fusion metadata.
- Bhashini-ready language adapter plus browser voice fallback.
- Last-known-good offline snapshot for patchy connectivity.
- SMS/IVR fallback adapter endpoints.
- Human-in-loop escalation queue for Coast Guard, INCOIS and disaster teams.
- Proactive Alert Watch / geofencing workflow.

## API

    GET /health
    GET /api/system/status
    GET /api/intent?q=...
    GET /api/knowledge/search?q=...
    GET /api/evidence/catalog
    GET /api/channels/status
    GET /api/offline/snapshot?location=Kakinada
    GET /api/satellite/status
    POST /api/language/translate
    POST /api/fallback/message
    POST /api/escalate
    GET /api/query?q=...&location=Kakinada&language=en-IN

    GET /api/demo?scenario=safe&location=Kakinada
    GET /api/demo?scenario=caution&location=Kakinada
    GET /api/demo?scenario=unsafe&location=Kakinada
    GET /api/demo?scenario=cyclone_alert&location=Kakinada
    GET /api/demo?scenario=safe&location=Visakhapatnam
    GET /api/demo?scenario=blocked&location=Kakinada
    GET /api/demo?scenario=data_unavailable&location=Kakinada

## Local run

Backend:

    cd backend
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    $env:PYTHONPATH = "."
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

React:

    cd frontend-react
    npm install
    npm run dev

Compose:

    docker compose up --build

Services:

- React/Nginx: http://127.0.0.1:3000
- FastAPI: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- Redis: localhost:6379
- PostGIS: localhost:5432

## Evidence boundaries

- Open-Meteo is the current prototype live weather/marine provider.
- INCOIS currently supplies advisory metadata; PFZ geometry remains explicitly demo geometry unless an approved machine-readable authoritative geometry source is configured.
- IMD marine warnings require an approved configured endpoint.
- MOSDAC is exposed as a satellite evidence gateway with multi-satellite-ready metadata; live machine-readable values require an approved configured endpoint.
- Bhashini is exposed as a configurable national-language adapter; browser speech remains the local fallback.
- SMS/IVR endpoints are adapter-ready and do not contact external providers until webhooks are configured.
- Human-in-loop escalation creates an auditable prototype queue record; it does not silently contact agencies.
- ChromaDB is a knowledge/evidence aid, not the safety authority.
- Demo thresholds are prototype rules, not official maritime regulations.
- Straight-line route calculations are reference context, not operational navigation.

## Fast SIH demo

1. Start backend and React.
2. Open the ORCA dashboard.
3. Run the Kakinada fishing query.
4. Show Ocean, Weather and Geo evidence.
5. Show the deterministic Risk Engine result.
6. Trigger SAFE, CAUTION, UNSAFE, BLOCKED and DATA_UNAVAILABLE.
7. Show route context, provenance, knowledge layer and source gateways.
8. Switch English/Telugu/Hindi and demonstrate voice input/output.

The product intentionally prioritizes a working, explainable prototype over unsupported claims of operational maritime authority.
