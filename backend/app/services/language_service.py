import os

import httpx

BHASHINI_API_URL = os.getenv("BHASHINI_API_URL", "").strip()
BHASHINI_API_KEY = os.getenv("BHASHINI_API_KEY", "").strip()


def language_status():
    return {
        "provider": "Bhashini",
        "configured": bool(BHASHINI_API_URL and BHASHINI_API_KEY),
        "supported_languages": ["en-IN", "te-IN", "hi-IN"],
        "voice": "browser_speech",
        "mode": "live_adapter" if BHASHINI_API_URL and BHASHINI_API_KEY else "local_fallback",
    }


async def translate(text: str, source_language: str, target_language: str) -> dict:
    if source_language == target_language:
        return {"text": text, "mode": "identity", "provider": "local"}

    if not BHASHINI_API_URL or not BHASHINI_API_KEY:
        return {
            "text": text,
            "mode": "local_fallback",
            "provider": "Bhashini adapter",
            "note": "Bhashini credentials/endpoint are not configured; original text is returned.",
        }

    payload = {
        "text": text,
        "source_language": source_language,
        "target_language": target_language,
    }
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(
                BHASHINI_API_URL,
                headers={"Authorization": f"Bearer {BHASHINI_API_KEY}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        translated = data.get("translated_text") or data.get("text") or text
        return {"text": translated, "mode": "live_adapter", "provider": "Bhashini"}
    except (httpx.HTTPError, ValueError, TypeError):
        return {
            "text": text,
            "mode": "fallback_after_error",
            "provider": "Bhashini adapter",
        }
