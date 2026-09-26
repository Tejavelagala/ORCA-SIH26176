# ORCA — Final SIH Demo Checklist

## 1. Start backend

Windows PowerShell:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
$env:PYTHONPATH="."
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 2. Start frontend

In another terminal:

```powershell
cd frontend
python -m http.server 5500
```

Open:

`http://127.0.0.1:5500`

## 3. Verify backend

Open:

`http://127.0.0.1:8000/health`

Expected:

```json
{"status":"healthy"}
```

Then from the repository root:

```powershell
cd backend
$env:PYTHONPATH="."
python -m compileall app
pytest -q
```

## 4. Manual presentation sequence

1. Open ORCA.
2. Ask: **Is it safe to fish near Kakinada tomorrow morning?**
3. Point to the **Ocean, Weather and Geo** agents.
4. Show the **6-Stage ORCA Reasoning Trace**.
5. Show **Evidence → Rules → Decision → Route**.
6. Select **Fisher Mission Mode**.
7. Run **UNSAFE**.
8. Run **BLOCKED**.
9. Run **DATA GAP**.
10. Start **Presentation Mode** and let the five states cycle.
11. Show the map, route reference and provenance.
12. Optionally enable **Marine Alert Watch**.
13. Open the source gateways if asked.

## 5. Mission Modes

Verify that all four buttons work:

- 🎣 Fisher
- 🚢 Ship Operator
- 🛟 Coast Guard
- 🚨 Disaster Team

Each mode should populate a contextual query and run the normal ORCA workflow.

## 6. Alert Watch

Verify:

- Enable Alert Watch changes the status to active.
- An immediate risk check appears in the alert feed.
- The selected location is shown.
- Stop Alert Watch stops periodic checks.

Describe this as **prototype polling**, not production push notifications.

## 7. Five deterministic scenarios

Expected statuses:

- SAFE
- CAUTION
- UNSAFE
- BLOCKED
- DATA_UNAVAILABLE

These are deterministic presentation scenarios and must not be described as official maritime thresholds.

## 8. Judge explanation

> ORCA separates evidence collection from the safety decision. Ocean, Weather and Geo agents collect evidence in parallel. A deterministic Risk Engine applies explicit rules. The LLM, when configured, explains the already-computed result and does not change the safety status.

## 9. Data-source explanation

Say:

> “The current prototype uses Open-Meteo for live weather and marine conditions, an INCOIS advisory adapter for official PFZ metadata, and configurable GIS layers. PFZ geometry and some authoritative warning/boundary integrations remain prototype or configurable components.”

## 10. Do not claim

- Demo PFZ coordinates are live INCOIS PFZ geometry.
- The straight-line prototype route is a navigational route.
- Prototype thresholds are official maritime regulations.
- An unavailable provider is live.
- Alert Watch is a production push-alert service.
- Mission Modes are separate backend pipelines.
- Prototype output is authoritative navigation or safety guidance.

## 11. If something fails

- Confirm FastAPI is running on port 8000.
- Confirm the frontend is running on port 5500.
- Refresh the browser after backend changes.
- Check the browser console for frontend errors.
- Check `http://127.0.0.1:8000/health`.
- If external providers are unavailable, verify that ORCA displays the appropriate fallback/provenance state rather than claiming live data.

## Verification policy

ORCA uses **local verification only** for the SIH demo. GitHub Actions is intentionally not part of the demo verification workflow.
