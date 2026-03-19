from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from store import get_store
from agents import ExceptionOrchestrator
from celonis import get_celonis_client
from notifications import NotificationManager
from models import ExceptionStatus

router = APIRouter()

class ProcessRequest(BaseModel):
    raw_input: dict

@router.get("/exceptions")
def list_exceptions(status: Optional[str] = None, limit: int = 50):
    return [e.to_dict() for e in get_store().list_exceptions(status=status, limit=limit)]

@router.get("/exceptions/pending")
def get_pending():
    return [e.to_dict() for e in get_store().list_exceptions(status="pending_decision", limit=100)]

@router.get("/exceptions/{exception_id}")
def get_exception(exception_id: str):
    store = get_store()
    exc = store.get_exception(exception_id)
    if not exc: return {"error": "Not found"}
    data = exc.to_dict()
    data["decisions"] = [d.to_dict() for d in store.get_decisions(exception_id)]
    data["actions"] = [a.to_dict() for a in store.get_actions(exception_id)]
    return data

@router.get("/exceptions/{exception_id}/trace")
def get_exception_trace(exception_id: str):
    """Get the agent conversation trace for an exception."""
    store = get_store()
    exc = store.get_exception(exception_id)
    if not exc:
        return {"error": "Not found"}
    trace = (exc.recommended_action_params or {}).get("agent_trace", {})
    if not trace:
        return {"error": "No trace found for this exception"}
    return trace

@router.post("/process")
def process_exception(req: ProcessRequest):
    store = get_store()
    exc = ExceptionOrchestrator(store).process(req.raw_input)
    if exc.status == ExceptionStatus.PENDING_DECISION:
        ctx, cls, rc = exc.context, exc.classification, exc.root_cause
        briefing = f"Exception: {ctx.exception_type}\nExposure: ${ctx.financial_exposure:,.2f}\nRoot Cause: {rc.hypothesis[:200] if rc else 'N/A'}\nRecommended: {exc.recommended_action}"
        NotificationManager().notify(exc.id, briefing, cls.priority if cls else 3, cls.category if cls else "unknown",
            f"http://localhost:3000/exception/{exc.id}")
    return exc.to_dict()

@router.post("/process-all")
def process_all():
    store = get_store()
    results = []
    for case in get_celonis_client().get_open_exceptions():
        c = {k: v for k, v in case.items()}
        c.pop("description", None)
        try:
            exc = ExceptionOrchestrator(store).process(c)
            results.append({"case_id": c.get("case_id"), "id": exc.id, "status": exc.status.value})
        except Exception as e:
            results.append({"case_id": c.get("case_id"), "error": str(e)})
    return {"processed": len(results), "results": results}

@router.get("/variants")
def get_variants():
    return get_celonis_client().get_process_variants()