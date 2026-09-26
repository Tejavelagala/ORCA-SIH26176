from typing import TypedDict
import asyncio

from app.agents.ocean_agent import get_ocean
from app.agents.weather_agent import run as weather_run
from app.agents.geo_agent import run as geo_run
from app.engine.risk_engine import evaluate
from app.engine.route_engine import recommend_route
from app.services.explanation_service import generate_explanation
from app.services.provider_metadata import utc_now_iso

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:
    StateGraph = START = END = None


class OrcaState(TypedDict, total=False):
    query: str
    location: str
    language: str
    intent: dict
    ocean: dict
    weather: dict
    geo: dict
    risk: dict
    route: dict
    explanation: dict


async def _ocean(state: OrcaState):
    return {"ocean": await get_ocean(state["location"])}

async def _weather(state: OrcaState):
    return {"weather": await weather_run(state["location"])}

async def _geo(state: OrcaState):
    return {"geo": await geo_run(state["location"])}

def _risk(state: OrcaState):
    risk = evaluate(state["ocean"], state["weather"], state["geo"])
    route = recommend_route(
        {**state["ocean"], "query_coordinates": state["geo"].get("coordinates")},
        risk,
    )
    return {"risk": risk, "route": route}

async def _explanation(state: OrcaState):
    explanation = await generate_explanation(
        state["query"],
        state["risk"],
        state["ocean"],
        state["weather"],
        state["geo"],
        state.get("language", "en-IN"),
    )
    return {"explanation": explanation}

def build_graph():
    if StateGraph is None:
        return None

    graph = StateGraph(OrcaState)
    graph.add_node("ocean_agent", _ocean)
    graph.add_node("weather_agent", _weather)
    graph.add_node("geo_agent", _geo)
    graph.add_node("risk_engine", _risk)
    graph.add_node("explanation", _explanation)

    graph.add_edge(START, "ocean_agent")
    graph.add_edge(START, "weather_agent")
    graph.add_edge(START, "geo_agent")
    graph.add_edge("ocean_agent", "risk_engine")
    graph.add_edge("weather_agent", "risk_engine")
    graph.add_edge("geo_agent", "risk_engine")
    graph.add_edge("risk_engine", "explanation")
    graph.add_edge("explanation", END)
    return graph.compile()

_GRAPH = build_graph()

async def run_graph(query: str, location: str, language: str, intent: dict):
    if _GRAPH is None:
        return None

    result = await _GRAPH.ainvoke({
        "query": query,
        "location": location,
        "language": language,
        "intent": intent,
    })

    trace = [
        {"stage": "Intent", "status": "completed", "detail": f"Detected {intent.get('intent', 'general')} intent."},
        {"stage": "Ocean Agent", "status": "completed", "detail": f"PFZ/advisory evidence collected in {result['ocean'].get('data_mode', 'unknown')} mode."},
        {"stage": "Weather Agent", "status": "completed", "detail": f"Weather and marine conditions collected in {result['weather'].get('data_mode', 'unknown')} mode."},
        {"stage": "Geo Agent", "status": "completed", "detail": f"Geospatial check completed with status {result['geo'].get('eez_status', 'unknown')}."},
        {"stage": "Risk Engine", "status": "completed", "detail": f"Deterministic rules produced {result['risk'].get('status', 'UNKNOWN')}."},
        {"stage": "Explanation", "status": "completed", "detail": f"Evidence explanation generated in {result['explanation'].get('mode', 'unknown')} mode."},
    ]

    return {
        "query": query,
        "location": location,
        "generated_at": utc_now_iso(),
        "risk": result["risk"],
        "agents": {
            "ocean": result["ocean"],
            "weather": result["weather"],
            "geo": result["geo"],
        },
        "route": result["route"],
        "explanation": result["explanation"]["text"],
        "explanation_mode": result["explanation"]["mode"],
        "language": language,
        "intent": intent,
        "orchestration": "langgraph",
        "trace": trace,
    }
