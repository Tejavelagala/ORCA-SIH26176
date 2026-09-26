import time
import uuid
from typing import Optional

_SESSIONS = {}
TTL_SECONDS = 60 * 60 * 8


def create_session(language: str = "en-IN", location: str = "Kakinada", mission: str = "fisher") -> dict:
    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "created_at": time.time(),
        "updated_at": time.time(),
        "language": language,
        "location": location,
        "mission": mission,
        "vessel_type": None,
        "history": [],
        "context": {},
    }
    _SESSIONS[session_id] = session
    return public_session(session)


def get_session(session_id: str) -> Optional[dict]:
    session = _SESSIONS.get(session_id)
    if not session:
        return None
    if time.time() - session["updated_at"] > TTL_SECONDS:
        _SESSIONS.pop(session_id, None)
        return None
    session["updated_at"] = time.time()
    return session


def public_session(session: dict) -> dict:
    return {k: v for k, v in session.items() if k not in {"created_at", "updated_at"}}


def update_session(session_id: str, *, query: str, result: dict, location: str, language: str) -> dict:
    session = get_session(session_id)
    if not session:
        session = create_session(language=language, location=location)
        session_id = session["session_id"]
        session = _SESSIONS[session_id]

    session["location"] = location
    session["language"] = language
    session["updated_at"] = time.time()
    session["context"] = {
        "last_query": query,
        "last_risk": result.get("risk", {}).get("status"),
        "last_score": result.get("risk", {}).get("score"),
        "last_location": location,
        "last_forecast_time": result.get("agents", {}).get("weather", {}).get("forecast_time"),
        "last_pfz": result.get("agents", {}).get("ocean", {}).get("pfz"),
    }
    session["history"].append({
        "turn": len(session["history"]) + 1,
        "query": query,
        "risk": result.get("risk", {}).get("status"),
        "score": result.get("risk", {}).get("score"),
        "generated_at": result.get("generated_at"),
    })
    session["history"] = session["history"][-12:]
    return public_session(session)


def contextualize(session_id: str | None, query: str, location: str) -> tuple[str, dict | None]:
    if not session_id:
        return query, None
    session = get_session(session_id)
    if not session:
        return query, None

    previous = session.get("context", {})
    if not previous.get("last_query"):
        return query, public_session(session)

    follow_up_markers = (
        "what about", "how about", "then", "and ", "there", "that time",
        "same", "later", "earlier", "tomorrow", "today", "12 pm", "pm", "am",
    )
    is_follow_up = len(query.split()) <= 8 or query.lower().strip().startswith(follow_up_markers)
    if not is_follow_up:
        return query, public_session(session)

    resolved = (
        f"Follow-up to previous ORCA marine query: '{previous['last_query']}'. "
        f"Previous location: {previous.get('last_location', location)}. "
        f"Previous risk: {previous.get('last_risk', 'unknown')}. "
        f"New user request: '{query}'."
    )
    return resolved, public_session(session)


def delete_session(session_id: str) -> bool:
    return _SESSIONS.pop(session_id, None) is not None


def session_status() -> dict:
    now = time.time()
    active = sum(1 for s in _SESSIONS.values() if now - s["updated_at"] <= TTL_SECONDS)
    return {"active_sessions": active, "ttl_hours": TTL_SECONDS / 3600, "max_history_turns": 12}
