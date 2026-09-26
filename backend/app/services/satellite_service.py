import os
from app.services.provider_metadata import source_metadata

MOSDAC_URL = "https://mosdac.gov.in/"


def satellite_status():
    configured = bool(os.getenv("MOSDAC_API_URL", "").strip())
    return {
        "provider": "ISRO / MOSDAC",
        "gateway": MOSDAC_URL,
        "configured": configured,
        "mode": "live_adapter" if configured else "gateway_catalog",
        "products": ["SST", "chlorophyll"],
        "fusion": "multi_satellite_ready",
        "last_known_good": True,
        "source": source_metadata(
            provider="ISRO / MOSDAC",
            mode="live_adapter" if configured else "gateway_catalog",
            note="Prototype gateway. Configure an approved machine-readable MOSDAC endpoint before claiming live satellite values.",
        ),
    }
