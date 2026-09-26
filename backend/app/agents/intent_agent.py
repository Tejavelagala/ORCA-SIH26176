from typing import Dict

INTENT_KEYWORDS = {
    "fishing": ("fish", "fishing", "pfz", "catch", "fisher", "చేప", "చేపలు", "మత్స్య", "मछली", "मछुआरा", "मछली पकड़"),
    "shipping": ("ship", "vessel", "cargo", "route", "sailing", "marine operation", "నౌక", "ఓడ", "जहाज", "नौका", "कार्गो"),
    "coast_guard": ("coast guard", "patrol", "restricted", "surveillance", "coastal", "కోస్ట్ గార్డ్", "పహారా", "तटरक्षक", "गश्त"),
    "disaster": ("cyclone", "storm", "disaster", "rescue", "emergency", "flood", "తుఫాను", "విపత్తు", "రక్షణ", "आपदा", "चक्रवात", "बचाव"),
    "weather": ("weather", "wind", "rain", "wave", "sea condition", "వాతావరణం", "గాలి", "వర్షం", "అలలు", "मौसम", "हवा", "बारिश", "लहर"),
    "geospatial": ("eez", "imbl", "mpa", "restricted zone", "boundary", "map", "సరిహద్దు", "మ్యాప్", "नक्शा", "सीमा"),
}

MISSION_DEFAULTS = {
    "fishing": "fisher",
    "shipping": "ship_operator",
    "coast_guard": "coastguard",
    "disaster": "disaster",
}

LANGUAGE_HINTS = {
    "te-IN": ("చేప", "చేపలు", "మత్స్య", "వాతావరణం", "గాలి", "తుఫాను", "రక్షణ", "సముద్రం"),
    "hi-IN": ("मछली", "मछुआरा", "मौसम", "हवा", "तूफान", "बचाव", "समुद्र", "जहाज"),
}


def classify_intent(query: str) -> Dict:
    text = (query or "").lower().strip()
    scores = {intent: sum(1 for keyword in keywords if keyword in text) for intent, keywords in INTENT_KEYWORDS.items()}
    intent = max(scores, key=scores.get) if text else "general"
    if not scores or scores.get(intent, 0) == 0:
        intent = "general"
    mission = MISSION_DEFAULTS.get(intent)
    language_hint = next((language for language, hints in LANGUAGE_HINTS.items() if any(h in text for h in hints)), "en-IN")
    total = sum(scores.values())
    return {
        "intent": intent,
        "mission": mission,
        "scores": scores,
        "confidence": round(scores.get(intent, 0) / max(1, total), 2),
        "language_hint": language_hint,
        "supported_languages": ["en-IN", "te-IN", "hi-IN"],
    }
