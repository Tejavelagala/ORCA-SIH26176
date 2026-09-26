from datetime import datetime, timezone
from typing import Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def source_metadata(
    *,
    provider: str,
    mode: str,
    fetched_at: Optional[str] = None,
    note: Optional[str] = None,
) -> dict:
    metadata = {
        "provider": provider,
        "mode": mode,
        "fetched_at": fetched_at or utc_now_iso(),
    }

    if note:
        metadata["note"] = note

    return metadata
