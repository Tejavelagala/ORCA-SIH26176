from app.agents.intent_agent import classify_intent
from app.services.knowledge_service import search_knowledge, knowledge_status


def test_telugu_intent_hint():
    result = classify_intent("చేపలు పట్టడానికి సముద్రం ఎలా ఉంది?")
    assert result["intent"] == "fishing"
    assert result["language_hint"] == "te-IN"


def test_hindi_intent_hint():
    result = classify_intent("मछली पकड़ने के लिए मौसम कैसा है?")
    assert result["intent"] == "fishing"
    assert result["language_hint"] == "hi-IN"


def test_knowledge_catalog_search():
    result = search_knowledge("INCOIS PFZ fishing advisory", limit=3)
    assert result
    assert any("INCOIS" in item["source"] for item in result)


def test_knowledge_status_contract():
    status = knowledge_status()
    assert status["provider"] == "ChromaDB"
    assert status["documents"] >= 1
