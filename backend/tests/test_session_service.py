from app.services.session_service import contextualize, create_session, get_session, update_session


def test_session_contextualizes_short_follow_up():
    session = create_session(location="Kakinada")
    update_session(
        session["session_id"],
        query="Is it safe to fish tomorrow?",
        result={"risk": {"status": "CAUTION", "score": 44}, "agents": {"weather": {}}},
        location="Kakinada",
        language="en-IN",
    )
    resolved, current = contextualize(session["session_id"], "What about 12 PM?", "Kakinada")
    assert "Follow-up to previous ORCA marine query" in resolved
    assert current["history"][-1]["query"] == "Is it safe to fish tomorrow?"


def test_session_keeps_last_twelve_turns():
    session = create_session()
    for i in range(15):
        update_session(
            session["session_id"],
            query=f"query {i}",
            result={"risk": {"status": "SAFE", "score": 10}, "agents": {"weather": {}}},
            location="Kakinada",
            language="en-IN",
        )
    current = get_session(session["session_id"])
    assert len(current["history"]) == 12
    assert current["history"][0]["query"] == "query 3"
