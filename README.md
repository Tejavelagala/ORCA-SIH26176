# ORCA — SIH 2026 PS-26176

Marine EcOsystem Reasoning with Collaborative Agents.

## MVP
A solo-developer prototype demonstrating:
- conversational marine query handling
- Ocean, Weather and Geo agents
- deterministic risk evaluation
- evidence-oriented responses
- Leaflet map visualization

## Run
cd backend
python -m venv venv
# Windows: venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

Open http://127.0.0.1:8000/docs

Then open frontend/index.html in a browser.

> Demo PFZ values are explicitly marked as demo data. Do not present them as live INCOIS observations.
