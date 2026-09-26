import os
from typing import Optional

import httpx


SYSTEM_PROMPT = """
You are ORCA, a marine intelligence explanation assistant.

You do NOT make safety decisions.
You must never change, reinterpret, override, or soften the supplied risk status.
Use only the supplied evidence.
Do not invent weather, ocean, geographic, route, or warning data.
Be concise and clear for fishermen, ship operators, and response teams.
Respond in the requested language when possible.
If data is unavailable, say that it is unavailable.
Return only a short natural-language explanation.
""".strip()


def deterministic_explanation(risk: dict, ocean: dict, weather: dict, geo: dict, language: str = "en-IN") -> str:
    status = risk.get("status", "UNKNOWN")
    wind = weather.get("wind_speed_kmh")
    wave = weather.get("wave_height_m")
    pfz = ocean.get("pfz") or {}

    parts = [
        f"ORCA classified the request as {status}.",
        f"Wind is {wind} km/h and wave height is {wave} m.",
    ]

    if pfz.get("name"):
        parts.append(
            f"PFZ reference: {pfz['name']} at "
            f"{pfz.get('distance_km', 'N/A')} km {pfz.get('direction', '')}."
        )

    if geo.get("eez_status") == "unavailable":
        parts.append("Authoritative geographic layers are currently unavailable.")

    reasons = risk.get("reasons") or []
    if reasons:
        parts.append("Reason: " + "; ".join(reasons[:2]) + ".")

    text = " ".join(parts)
    if language == "te-IN":
        return f"ORCA ఈ అభ్యర్థనను {status}గా వర్గీకరించింది. గాలి వేగం {wind} km/h మరియు అలల ఎత్తు {wave} m." + (f" కారణం: {reasons[0]}." if reasons else "")
    if language == "hi-IN":
        return f"ORCA ने इस अनुरोध को {status} के रूप में वर्गीकृत किया है। हवा की गति {wind} km/h और लहरों की ऊंचाई {wave} m है।" + (f" कारण: {reasons[0]}।" if reasons else "")
    return text


async def generate_explanation(
    query: str,
    risk: dict,
    ocean: dict,
    weather: dict,
    geo: dict,
    language: str = "en-IN",
) -> dict:
    fallback = deterministic_explanation(risk, ocean, weather, geo, language)

    language_names = {
        "en-IN": "English",
        "te-IN": "Telugu",
        "hi-IN": "Hindi",
    }
    target_language = language_names.get(language, "English")

    api_key = os.getenv("LLM_API_KEY", "").strip()
    endpoint = os.getenv(
        "LLM_API_URL",
        "https://api.openai.com/v1/chat/completions",
    ).strip()
    model = os.getenv("LLM_MODEL", "").strip()

    if not api_key or not model:
        return {"text": fallback, "mode": "deterministic_fallback"}

    evidence = {
        "query": query,
        "response_language": target_language,
        "risk": risk,
        "ocean": ocean,
        "weather": weather,
        "geo": geo,
    }

    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Explain this already-computed ORCA decision in {target_language}. "
                    "Do not make a new decision.\n\n"
                    + str(evidence)
                ),
            },
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        text = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not text:
            return {"text": fallback, "mode": "deterministic_fallback"}

        return {
            "text": text,
            "mode": "llm_grounded",
            "model": model,
        }

    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        return {"text": fallback, "mode": "deterministic_fallback"}
