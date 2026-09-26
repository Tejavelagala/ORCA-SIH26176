import json
import os
import re
from pathlib import Path
from typing import Optional

import httpx

from app.services.provider_metadata import source_metadata

DATA = Path(__file__).resolve().parents[1] / "data" / "demo_pfz.json"

DEFAULT_INCOIS_PFZ_URL = (
    "https://www.incois.gov.in/MarineFisheries/"
    "TextDataHome?mfid=1&request_locale=en"
)


def _demo_pfz(location: str) -> dict:
    items = json.loads(DATA.read_text(encoding="utf-8"))
    return next(
        (item for item in items if item["location"].lower() == location.lower()),
        items[0],
    )


def _parse_advisory_dates(html: str) -> dict:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()

    dates = re.findall(r"\b\d{1,2}\s+[A-Z]{3}\s+\d{4}\b", text, flags=re.I)

    result = {
        "forecast_date": dates[0] if len(dates) > 0 else None,
        "valid_upto": dates[1] if len(dates) > 1 else None,
    }

    return result


async def _fetch_incois_advisory(url: str) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(
            timeout=12,
            follow_redirects=True,
            headers={"User-Agent": "ORCA-SIH26176/1.0"},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

        dates = _parse_advisory_dates(response.text)

        return {
            "available": True,
            "url": url,
            **dates,
            "source": source_metadata(
                provider="INCOIS Potential Fishing Zone Advisory",
                mode="live",
                note=(
                    "Live advisory metadata fetched from the official INCOIS "
                    "Marine Fisheries Text Data page. PFZ geometry remains "
                    "separate until an approved machine-readable geometry feed "
                    "is configured."
                ),
            ),
        }
    except (httpx.HTTPError, ValueError):
        return None


async def get_pfz(location: str) -> dict:
    pfz = _demo_pfz(location)

    url = os.getenv("INCOIS_PFZ_URL", DEFAULT_INCOIS_PFZ_URL).strip()
    advisory = await _fetch_incois_advisory(url) if url else None

    if advisory:
        source = advisory["source"]
        return {
            "pfz": pfz,
            "advisory": advisory,
            "source": source,
            "geometry_mode": "demo",
        }

    return {
        "pfz": pfz,
        "advisory": {
            "available": False,
            "url": url or None,
            "forecast_date": None,
            "valid_upto": None,
        },
        "source": source_metadata(
            provider="INCOIS Potential Fishing Zone Advisory",
            mode="fallback",
            note=(
                "Official INCOIS advisory could not be fetched. "
                "Using local demo PFZ geometry."
            ),
        ),
        "geometry_mode": "demo",
    }
