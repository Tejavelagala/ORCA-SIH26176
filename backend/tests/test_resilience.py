from app.services.resilience_service import build_escalation, build_fallback_message


def test_sms_fallback_contract():
    result = {
        "location": "Kakinada",
        "risk": {"status": "CAUTION", "reasons": ["high wind"]},
        "explanation": "Prototype warning.",
    }
    message = build_fallback_message(result, "sms")
    assert message["channel"] == "sms"
    assert "CAUTION" in message["message"]


def test_human_escalation_contract():
    result = {
        "location": "Kakinada",
        "risk": {"status": "UNSAFE", "reasons": ["high waves"]},
    }
    escalation = build_escalation(result, "coast_guard")
    assert escalation["target"] == "coast_guard"
    assert escalation["status"] == "queued_for_human_review"
    assert escalation["priority"] == "high"
