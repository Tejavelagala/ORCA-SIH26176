from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def source_metadata(
    *,
    provider: str,
    mode: str,
    fetched_at: str | None = None,
    note: str | None = None,
) -> dict:
    metadata = {
        "provider": provider,
        "mode": mode,
        "fetched_at": fetched_at or utc_now_iso(),
    }

    if note:
        metadata["note"] = note

    return metadata
