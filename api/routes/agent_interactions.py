from fastapi import APIRouter
from store import get_store

router = APIRouter()


@router.get("/agent-interactions/{exception_id}")
def get_agent_interactions_for_exception(exception_id: str):
    """
    Return the full agent interaction trace (prompt chain) for a specific exception.
    Shows each agent step: full prompt, full response, timing, and handoff.
    """
    store = get_store()
    interactions = store.get_agent_interactions(exception_id=exception_id)
    if not interactions:
        # Fall back to the legacy trace stored in exception record
        exc = store.get_exception(exception_id)
        if not exc:
            return {"error": "Not found"}
        trace = (exc.recommended_action_params or {}).get("agent_trace", {})
        if trace:
            return {"exception_id": exception_id, "source": "legacy_trace", "trace": trace}
        return {"error": "No interaction trace found for this exception"}
    return {"exception_id": exception_id, "source": "interaction_tracer", "interactions": interactions}


@router.get("/agent-interactions")
def list_agent_interactions(limit: int = 100):
    """
    Return a summary list of all traced agent interactions.
    """
    store = get_store()
    all_interactions = store.get_agent_interactions()
    summaries = []
    for interaction in all_interactions[:limit]:
        summaries.append({
            "id": interaction.get("id"),
            "exception_id": interaction.get("exception_id"),
            "recorded_at": interaction.get("recorded_at"),
            "total_steps": interaction.get("total_steps", 0),
            "total_duration_ms": interaction.get("total_duration_ms", 0),
        })
    return {"total": len(summaries), "interactions": summaries}
