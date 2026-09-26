import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "demo_pfz.json"

async def get_ocean(location: str):
    items = json.loads(DATA.read_text(encoding="utf-8"))
    pfz = next((x for x in items if x["location"].lower() == location.lower()), items[0])
    return {
        "agent": "Ocean Agent",
        "pfz": pfz,
        "source": "INCOIS PFZ advisory concept / DEMO DATA",
        "data_mode": "demo"
    }
