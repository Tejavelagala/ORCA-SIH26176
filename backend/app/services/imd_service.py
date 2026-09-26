import os

import httpx

from app.services.provider_metadata import source_metadata


IMD_MARINE_URL = os.getenv("IMD_MARINE_URL", "").strip()


async def get_marine_warning(location: str) -> dict:
    """
    Optional IMD adapter.

    The endpoint is configuration-driven so ORCA does not hard-code an
    undocumented or unstable IMD endpoint.
    """
    if not IMD_MARINE_URL:
        return {
            "cyclone_warning": False,
            "warning_available": False,
            "warning_text": None,
            "source": source_metadata(
                provider="IMD Marine Forecast",
                mode="unconfigured",
                note="Set IMD_MARINE_URL when an approved IMD endpoint/feed is available.",
            ),
        }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                IMD_MARINE_URL,
                params={"location": location},
            )
            response.raise_for_status()
            payload = response.json()

        warning = bool(
            payload.get("cyclone_warning")
            or payload.get("warning")
            or payload.get("alert")
        )

        text = (
            payload.get("warning_text")
            or payload.get("message")
            or payload.get("description")
        )

        return {
            "cyclone_warning": warning,
            "warning_available": True,
            "warning_text": text,
            "source": source_metadata(
                provider="IMD Marine Forecast",
                mode="live",
                note="Configured IMD endpoint.",
            ),
        }

    except (httpx.HTTPError, ValueError) as exc:
        return {
            "cyclone_warning": False,
            "warning_available": False,
            "warning_text": None,
            "source": source_metadata(
                provider="IMD Marine Forecast",
                mode="error",
                note=f"IMD adapter request failed: {type(exc).__name__}",
            ),
        }
