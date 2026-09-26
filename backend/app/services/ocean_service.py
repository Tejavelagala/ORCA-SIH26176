import json
from pathlib import Path

from app.services.provider_metadata import source_metadata

DATA = Path(__file__).resolve().parents[1] / "data" / "demo_pfz.json"


async def get_pfz(location: str) -> dict:
    items = json.loads(DATA.read_text(encoding="utf-8"))

    pfz = next(
        (item for item in items if item["location"].lower() == location.lower()),
        items[0],
    )

    return {
        "pfz": pfz,
        "source": source_metadata(
            provider="INCOIS PFZ advisory concept",
            mode="demo",
            note="Replace demo file with an INCOIS PFZ adapter for production.",
        ),
    }
