import json
import os
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = Path(os.getenv("ORCA_SNAPSHOT_PATH", str(BASE_DIR / "data" / "offline_snapshot.json")))


def _now():
    return datetime.now(timezone.utc).isoformat()


def save_last_known_good(result: dict) -> dict:
    """Persist a compact last-known-good brief for patchy connectivity/offline demo."""
    payload = {
        "saved_at": _now(),
        "location": result.get("location"),
        "query": result.get("query"),
        "risk": result.get("risk"),
        "agents": result.get("agents"),
        "route": result.get("route"),
        "explanation": result.get("explanation"),
        "language": result.get("language"),
        "evidence_summary": result.get("evidence_summary"),
    }
    try:
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(json.dumps(payload, default=str), encoding="utf-8")
        return {"available": True, "path": str(SNAPSHOT_PATH), "saved_at": payload["saved_at"]}
    except OSError as exc:
        return {"available": False, "error": type(exc).__name__}


def load_last_known_good(location: str | None = None) -> dict | None:
    try:
        payload = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if location and payload.get("location", "").lower() != location.lower():
        return None
    return payload


def channel_status() -> dict:
    return {
        "voice": "browser_speech",
        "sms": "adapter_ready" if os.getenv("SMS_WEBHOOK_URL") else "demo_adapter",
        "ivr": "adapter_ready" if os.getenv("IVR_WEBHOOK_URL") else "demo_adapter",
        "offline_cache": "enabled",
    }


def build_fallback_message(result: dict, channel: str = "sms") -> dict:
    risk = (result.get("risk") or {}).get("status", "UNKNOWN")
    location = result.get("location", "selected area")
    explanation = result.get("explanation", "")
    compact = f"ORCA {risk}: {location}. {explanation}".strip()
    if channel.lower() == "ivr":
        compact = f"ORCA marine status for {location} is {risk}. {explanation}"
    return {
        "channel": channel.lower(),
        "mode": "adapter_ready" if os.getenv(f"{channel.upper()}_WEBHOOK_URL") else "demo",
        "message": compact[:480],
        "webhook_configured": bool(os.getenv(f"{channel.upper()}_WEBHOOK_URL")),
    }


def build_escalation(result: dict, target: str = "coast_guard") -> dict:
    risk = (result.get("risk") or {}).get("status", "UNKNOWN")
    return {
        "created_at": _now(),
        "target": target,
        "priority": "high" if risk in {"UNSAFE", "BLOCKED"} else "normal",
        "risk_status": risk,
        "location": result.get("location"),
        "reason": (result.get("risk") or {}).get("reasons", [])[:3],
        "mode": "human_in_loop_prototype",
        "status": "queued_for_human_review",
        "note": "Prototype escalation record; no external agency notification is sent unless a webhook is configured.",
    }
