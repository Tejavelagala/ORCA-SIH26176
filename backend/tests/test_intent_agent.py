from app.agents.intent_agent import classify_intent

def test_fishing_intent():
    result = classify_intent("Is it safe to fish near Kakinada?")
    assert result["intent"] == "fishing"
    assert result["mission"] == "fisher"

def test_shipping_intent():
    result = classify_intent("Can my ship operate near Chennai?")
    assert result["intent"] == "shipping"
    assert result["mission"] == "ship_operator"
