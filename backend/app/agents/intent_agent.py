from typing import Dict

INTENT_KEYWORDS = {
    "fishing": ("fish", "fishing", "pfz", "catch", "fisher"),
    "shipping": ("ship", "vessel", "cargo", "route", "sailing", "marine operation"),
    "coast_guard": ("coast guard", "patrol", "restricted", "surveillance", "coastal"),
    "disaster": ("cyclone", "storm", "disaster", "rescue", "emergency", "flood"),
    "weather": ("weather", "wind", "rain", "wave", "sea condition"),
    "geospatial": ("eez", "imbl", "mpa", "restricted zone", "boundary", "map"),
}

MISSION_DEFAULTS = {
    "fishing": "fisher",
    "shipping": "ship_operator",
    "coast_guard": "coastguard",
    "disaster": "disaster",
}

def classify_intent(query: str) -> Dict:
    text = (query or "").lower().strip()
    scores = {
        intent: sum(1 for keyword in keywords if keyword in text)
        for intent, keywords in INTENT_KEYWORDS.items()
    }
    intent = max(scores, key=scores.get) if text else "general"
    if not scores or scores.get(intent, 0) == 0:
        intent = "general"

    mission = MISSION_DEFAULTS.get(intent)
    return {
        "intent": intent,
        "mission": mission,
        "scores": scores,
        "confidence": round(
            scores.get(intent, 0) / max(1, sum(scores.values())), 2
        ),
    }
