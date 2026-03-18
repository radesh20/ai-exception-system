from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel
from store import get_store
from models import Decision, DecisionType, ExceptionStatus, Action, ActionStatus
from agents import LearningEngine
from notifications import NotificationManager
from execution import get_executor
import config.settings as settings

router = APIRouter()

class DecisionRequest(BaseModel):
    exception_id: str
    decision_type: str
    analyst_name: str
    notes: str = ""
    final_action: str = ""

@router.post("/decisions")
def submit_decision(req: DecisionRequest):
    store = get_store()
    exc = store.get_exception(req.exception_id)
    if not exc: return {"error": "Exception not found"}

    decision = Decision(id="", exception_id=req.exception_id, decision_type=DecisionType(req.decision_type),
        analyst_name=req.analyst_name, notes=req.notes, original_recommendation=exc.recommended_action or "",
        final_action=req.final_action or exc.recommended_action or "")
    store.save_decision(decision)

    if req.decision_type == "approved": exc.status = ExceptionStatus.APPROVED
    elif req.decision_type == "rejected": exc.status = ExceptionStatus.REJECTED
    elif req.decision_type == "modified":
        exc.status = ExceptionStatus.APPROVED
        exc.recommended_action = req.final_action
    elif req.decision_type == "escalated": exc.status = ExceptionStatus.PENDING_DECISION
    store.update_exception(exc)

    learning_result = LearningEngine(store).record_feedback(decision)

    action_result = None
    if req.decision_type in ("approved", "modified") and settings.EXECUTION_ENABLED:
        action = Action(id="", exception_id=req.exception_id, decision_id=decision.id,
            action_type=decision.final_action, action_params=exc.recommended_action_params or {},
            executed_by=req.analyst_name, execution_target=settings.EXECUTION_MODE)
        executed = get_executor().execute(action)
        store.save_action(executed)
        if executed.status == ActionStatus.COMPLETED:
            exc.status = ExceptionStatus.COMPLETED
            store.update_exception(exc)
        action_result = executed.to_dict()

    NotificationManager().notify_decision(req.exception_id, decision.final_action, req.analyst_name)
    return {"decision_id": decision.id, "exception_id": req.exception_id, "decision_type": req.decision_type,
            "action_executed": action_result, "learning": learning_result}

@router.get("/decisions")
def list_decisions(limit: int = 50):
    return [d.to_dict() for d in get_store().list_decisions(limit=limit)]