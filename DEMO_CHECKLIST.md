# ORCA — Final SIH Demo Checklist

## 1. Start backend

Windows PowerShell:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
$env:PYTHONPATH="."
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 2. Run local smoke test

From the repository root, in a second terminal:

```powershell
python backend/scripts/smoke_test.py
```

Expected states:

- SAFE
- CAUTION
- UNSAFE
- BLOCKED
- DATA_UNAVAILABLE

## 3. Start frontend

In another terminal:

```powershell
cd frontend
python -m http.server 5500
```

Open:

`http://127.0.0.1:5500`

## 4. Manual presentation sequence

1. Ask: **Is it safe to fish?**
2. Point to Ocean, Weather and Geo agents.
3. Show Agent Activity.
4. Show Evidence → Rules → Decision → Route.
5. Run **UNSAFE**.
6. Run **BLOCKED**.
7. Run **DATA GAP**.
8. Start **Presentation Mode**.
9. Show the map and route reference.
10. Show Data Provenance.

## 5. Judge explanation

> ORCA separates evidence collection from the safety decision. Ocean, Weather and Geo agents collect evidence in parallel. A deterministic Risk Engine applies explicit rules. The LLM, when configured, explains the already-computed result and does not change the safety status.

## 6. Do not claim

- Demo PFZ coordinates are live INCOIS PFZ geometry.
- The straight-line prototype route is a navigational route.
- Prototype thresholds are official maritime regulations.
- An unavailable provider is live.
- Prototype output is authoritative navigation or safety guidance.

## 7. If something fails

- Confirm FastAPI is running on port 8000.
- Confirm the frontend is running on port 5500.
- Refresh the browser after backend changes.
- Run the local smoke test again.
- Check the browser console for frontend errors.

## Verification policy

ORCA uses **local verification only** for the SIH demo. No GitHub Actions workflow is required.
