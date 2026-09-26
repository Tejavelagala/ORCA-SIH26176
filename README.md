# ORCA — SIH 2026 PS-26176

**Marine EcOsystem Reasoning with Collaborative Agents**

ORCA is a conversational multi-agent marine intelligence prototype. It follows the architecture described in the SIH presentation: specialized Ocean, Weather and Geo agents collect evidence, an orchestrator coordinates them, a deterministic Risk Engine makes the safety classification, and an explanation layer turns the result into a human-readable response.

## Current PPT-aligned stack

| Layer | Current implementation |
|---|---|
| Backend | Python + FastAPI |
| Agent orchestration | LangGraph with asyncio fallback |
| Ocean intelligence | INCOIS PFZ advisory adapter + demo PFZ geometry |
| Weather / marine | Open-Meteo live weather + marine forecast |
| Marine warning | Configurable IMD adapter |
| Geo | Shapely + configurable GeoJSON |
| Decision | Deterministic Risk Engine |
| LLM | Optional OpenAI-compatible explanation layer |
| Cache | Redis adapter with in-memory fallback |
| Database | PostgreSQL adapter, ready for PostGIS expansion |
| Web UI | React + Vite primary client |
| Map | Leaflet |
| Deployment | Docker + Docker Compose |
| Languages | English, Telugu, Hindi |
| Voice | Browser speech input/output in legacy client |
| Demo fallback | Deterministic local scenarios |

The repository also retains the original static frontend under `frontend/` as a fallback/demo client. The PPT-aligned React client is under `frontend-react/`.

## Product flow

```
USER
  ↓
INTENT AGENT
  ↓
LANGGRAPH ORCHESTRATOR
  ├── OCEAN AGENT ── INCOIS PFZ / ocean evidence
  ├── WEATHER AGENT ── weather + waves
  └── GEO AGENT ── EEZ / restricted GIS evidence
          ↓
DETERMINISTIC RISK ENGINE
  ↓
SAFE / CAUTION / UNSAFE / BLOCKED / DATA_UNAVAILABLE
  ↓
ROUTE CONTEXT + EXPLANATION
  ↓
REACT WEB UI + MAP + PROVENANCE + ALERT WATCH
```

The LLM never makes or overrides the safety decision.

## Implemented product capabilities

- Conversational marine query workflow.
- Intent classification for fishing, shipping, coast-guard, disaster, weather and geospatial queries.
- Parallel Ocean, Weather and Geo execution through LangGraph.
- Asyncio fallback if LangGraph is unavailable.
- Deterministic risk classification.
- Explicit missing-data handling.
- Tomorrow-morning forecast targeting.
- INCOIS advisory metadata integration.
- Configurable GIS point-in-polygon checks.
- PFZ/map/route visualization.
- Mission modes for Fisher, Ship Operator, Coast Guard and Disaster Team.
- Marine Alert Watch.
- Multilingual deterministic explanations.
- Optional LLM explanation layer.
- Redis response caching when REDIS_URL is configured.
- In-memory cache fallback when Redis is not available.
- PostgreSQL query persistence when DATABASE_URL is configured.
- System status endpoint exposing configured capabilities.
- React/Vite web client.
- Dockerfiles for backend and React frontend.
- Docker Compose with PostgreSQL, Redis, FastAPI and React/Nginx.
- Legacy static frontend retained for fallback.

## API

```
GET /health
GET /api/system/status
GET /api/intent?q=...
GET /api/query?q=...&location=Kakinada&language=en-IN

GET /api/demo?scenario=safe
GET /api/demo?scenario=caution
GET /api/demo?scenario=unsafe
GET /api/demo?scenario=blocked
GET /api/demo?scenario=data_unavailable
```

## Local run — backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
$env:PYTHONPATH = "."
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Local run — React client

```powershell
cd frontend-react
npm install
npm run dev
```

The Vite client defaults to `http://127.0.0.1:8000`. Override with:

```powershell
$env:VITE_API_URL="http://127.0.0.1:8000"
```

## Docker / complete local product

From repository root:

```powershell
docker compose up --build
```

Services:

- React/Nginx UI: `http://127.0.0.1:3000`
- FastAPI: `http://127.0.0.1:8000`
- FastAPI docs: `http://127.0.0.1:8000/docs`
- Redis: `localhost:6379`
- PostgreSQL: `localhost:5432`

Set `LLM_API_KEY` and `LLM_MODEL` in the shell/environment if an LLM explanation provider is desired. Without it, deterministic explanations remain available.

## Risk engine

The prototype uses five explicit states:

- **SAFE** — no configured prototype threshold triggered.
- **CAUTION** — elevated wind/wave prototype threshold.
- **UNSAFE** — high-wave or marine-warning prototype condition.
- **BLOCKED** — configured restricted GIS zone.
- **DATA_UNAVAILABLE** — critical evidence such as wind/wave or supported location is unavailable.

These are prototype rules, not official maritime regulations.

## Data provenance

ORCA exposes provider, mode and timestamp information for evidence.

Important current distinctions:

- Open-Meteo is the current live weather/marine provider.
- INCOIS integration currently retrieves advisory metadata.
- PFZ geometry is still explicitly demo geometry unless an approved machine-readable authoritative geometry source is configured.
- IMD marine warnings require a configured endpoint.
- GIS safety checks require configured GIS data.
- Redis/PostgreSQL are optional in direct local development and enabled by Docker Compose.
- The optional LLM is an explanation component only.

## PPT use cases

### Fisher
PFZ reference, sea state, weather and geographic restrictions.

### Ship Operator
Marine operating conditions, ocean evidence and route context.

### Coast Guard
Hazards, restricted zones, weather and ocean evidence.

### Disaster Team
Marine hazards, weather, ocean conditions and data limitations.

## Prototype safety boundary

ORCA is a decision-support prototype. Demo data, prototype thresholds and straight-line route calculations must not be represented as authoritative marine navigation or safety guidance.

## Development priority

Keep improving the actual working prototype. Prefer concrete functionality, provider integration, evidence quality, deterministic safety logic and usable UI over judge scripts or production infrastructure that is not needed for the prototype.
