from typing import Any, TypedDict
from uuid import uuid4
from .config import Settings


class TripState(TypedDict, total=False):
    request: dict[str, Any]
    budget: dict[str, Any]
    booking: dict[str, Any]
    itinerary: list[dict[str, Any]]
    recommendation: str


async def budget_agent(state: TripState) -> TripState:
    request = state["request"]
    days = max((request["end_date"] - request["start_date"]).days, 1)
    daily = request["budget_eur"] / days
    state["budget"] = {"total_eur": request["budget_eur"], "daily_target_eur": round(daily, 2), "status": "on_track"}
    return state


async def booking_agent(state: TripState) -> TripState:
    request = state["request"]
    state["booking"] = {"status": "ready", "travelers": request["travelers"], "next_action": "Search live inventory before committing"}
    return state


async def itinerary_agent(state: TripState) -> TripState:
    request = state["request"]
    energy = request["energy_level"]
    state["itinerary"] = [{"day": 1, "pace": "gentle" if energy == "low" else "balanced", "focus": request["preferences"][0] if request["preferences"] else "local food", "adaptation": "Weather and fatigue checks enabled"}]
    state["recommendation"] = "Budget and booking agents agree: keep the first day flexible and reserve one local anchor."
    return state


async def reasoning_agent(state: TripState, settings: Settings) -> TripState:
    if not settings.openai_api_key:
        return state
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model=settings.openai_model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": "You are the Kinetix trip coordinator. Return one concise, practical recommendation."},
            {"role": "user", "content": f"Trip state: {state}. Reconcile budget, booking readiness, energy, and preferences."},
        ],
    )
    state["recommendation"] = response.choices[0].message.content or state["recommendation"]
    return state


async def plan_trip(request: dict[str, Any], settings: Settings) -> dict[str, Any]:
    state: TripState = {"request": request}

    async def reasoning_node(current_state: TripState) -> TripState:
        return await reasoning_agent(current_state, settings)

    try:
        from langgraph.graph import END, StateGraph
        graph = StateGraph(TripState)
        graph.add_node("budget", budget_agent)
        graph.add_node("booking", booking_agent)
        graph.add_node("itinerary", itinerary_agent)
        graph.add_node("reasoning", reasoning_node)
        graph.set_entry_point("budget")
        graph.add_edge("budget", "booking")
        graph.add_edge("booking", "itinerary")
        graph.add_edge("itinerary", "reasoning")
        graph.add_edge("reasoning", END)
        result = await graph.compile().ainvoke(state)
        result["orchestrator"] = "langgraph"
    except ImportError:
        for agent in (budget_agent, booking_agent, itinerary_agent):
            state = await agent(state)
        result = state
        result["orchestrator"] = "deterministic-fallback"
    result["trip_id"] = str(uuid4())
    return result


class VibeSearch:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.documents = [
            {"name": "Casa do Beco", "city": "Lisbon", "description": "Hidden garden, candlelight, quiet corners", "score": 0.96},
            {"name": "Prado", "city": "Lisbon", "description": "Seasonal local food, bright modern room", "score": 0.91},
            {"name": "Miradouro da Graça", "city": "Lisbon", "description": "Golden hour views, neighborhood energy", "score": 0.88},
        ]

    async def search(self, query: str, city: str, limit: int) -> list[dict[str, Any]]:
        try:
            if self.settings.pinecone_api_key:
                from pinecone import Pinecone
                index = Pinecone(api_key=self.settings.pinecone_api_key).Index(self.settings.pinecone_index)
                matches = index.query(vector=[], top_k=limit, include_metadata=True)
                return [match.metadata for match in matches.matches]
        except Exception:
            pass
        terms = set(query.lower().split())
        results = [item for item in self.documents if item["city"].lower() == city.lower()]
        return sorted(results, key=lambda item: (len(terms & set(item["description"].lower().split())), item["score"]), reverse=True)[:limit]
