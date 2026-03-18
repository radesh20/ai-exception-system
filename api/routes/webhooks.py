import json
from fastapi import APIRouter, Request
from store import get_store
from models import Decision, DecisionType, ExceptionStatus

router = APIRouter()

@router.post("/webhooks/slack")
async def slack_webhook(request: Request):
    try:
        form = await request.form()
        payload = json.loads(form.get("payload", "{}"))
    except:
        try: payload = json.loads(await request.body())
        except: return {"text": "Invalid payload"}

    actions = payload.get("actions", [])
    if not actions: return {"text": "No actions"}

    action = actions[0]
    exc_id = action.get("value", "")
    action_id = action.get("action_id", "").lower()
    user = payload.get("user", {}).get("name", "slack_user")
    store = get_store()
    exc = store.get_exception(exc_id)
    if not exc: return {"text": "Exception not found"}

    dec_type = DecisionType.APPROVED if "approve" in action_id else DecisionType.REJECTED
    decision = Decision(id="", exception_id=exc_id, decision_type=dec_type, analyst_name=user,
        notes=f"Via Slack", original_recommendation=exc.recommended_action or "", final_action=exc.recommended_action or "")
    store.save_decision(decision)
    exc.status = ExceptionStatus.APPROVED if "approve" in action_id else ExceptionStatus.REJECTED
    store.update_exception(exc)
    emoji = "✅" if "approve" in action_id else "❌"
    return {"text": f"{emoji} {dec_type.value.title()} by {user}"}