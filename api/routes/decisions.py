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


# ── ERP Action Endpoints ──────────────────────────────────────────────────────

class ErpDecisionRequest(BaseModel):
    analyst_name: str = "analyst"
    notes: str = ""

@router.get("/exceptions/{exception_id}/erp-recommendation")
def get_erp_recommendation(exception_id: str):
    """Return the ERP recommendation stored on an exception."""
    store = get_store()
    exc = store.get_exception(exception_id)
    if not exc:
        return {"error": "Exception not found"}
    return {
        "exception_id": exception_id,
        "erp_recommendation": exc.erp_recommendation,
        "erp_execution_status": exc.erp_execution_status,
    }

@router.post("/exceptions/{exception_id}/erp-approve")
def approve_erp_action(exception_id: str, req: ErpDecisionRequest = ErpDecisionRequest()):
    """Human approves the ERP recommendation for this exception."""
    store = get_store()
    exc = store.get_exception(exception_id)
    if not exc:
        return {"error": "Exception not found"}
    if not exc.erp_recommendation:
        return {"error": "No ERP recommendation found for this exception"}

    exc.erp_execution_status = "approved"
    exc.updated_at = datetime.now().isoformat()
    store.update_exception(exc)

    # Record feedback via learning engine
    try:
        decision = Decision(
            id="",
            exception_id=exception_id,
            decision_type=DecisionType("approved"),
            analyst_name=req.analyst_name,
            notes=f"ERP action approved. {req.notes}".strip(),
            original_recommendation=exc.recommended_action or "",
            final_action=exc.erp_recommendation.get("transaction", ""),
        )
        store.save_decision(decision)
        LearningEngine(store).record_feedback(decision)
    except Exception:
        pass

    # Send Teams notification
    try:
        erp = exc.erp_recommendation
        msg = (
            f"ERP action approved by {req.analyst_name}. "
            f"Transaction: {erp.get('transaction')} ({erp.get('system', 'SAP')}). "
            f"Ready for execution when ERP access available."
        )
        NotificationManager().notify_decision(exception_id, msg, req.analyst_name)
    except Exception:
        pass

    return {
        "exception_id": exception_id,
        "erp_execution_status": exc.erp_execution_status,
        "erp_recommendation": exc.erp_recommendation,
        "message": f"ERP action approved by {req.analyst_name}.",
    }

@router.post("/exceptions/{exception_id}/erp-reject")
def reject_erp_action(exception_id: str, req: ErpDecisionRequest = ErpDecisionRequest()):
    """Human rejects the ERP recommendation for this exception."""
    store = get_store()
    exc = store.get_exception(exception_id)
    if not exc:
        return {"error": "Exception not found"}
    if not exc.erp_recommendation:
        return {"error": "No ERP recommendation found for this exception"}

    exc.erp_execution_status = "rejected"
    exc.updated_at = datetime.now().isoformat()
    store.update_exception(exc)

    # Record feedback via learning engine
    try:
        decision = Decision(
            id="",
            exception_id=exception_id,
            decision_type=DecisionType("rejected"),
            analyst_name=req.analyst_name,
            notes=f"ERP action rejected. {req.notes}".strip(),
            original_recommendation=exc.recommended_action or "",
            final_action="",
        )
        store.save_decision(decision)
        LearningEngine(store).record_feedback(decision)
    except Exception:
        pass

    # Send Teams notification
    try:
        NotificationManager().notify_decision(
            exception_id,
            f"ERP action rejected by {req.analyst_name}. Alternative action required.",
            req.analyst_name,
        )
    except Exception:
        pass

    return {
        "exception_id": exception_id,
        "erp_execution_status": exc.erp_execution_status,
        "erp_recommendation": exc.erp_recommendation,
        "message": f"ERP action rejected by {req.analyst_name}. Alternative action required.",
    }