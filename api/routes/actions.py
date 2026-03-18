from fastapi import APIRouter
from store import get_store
from execution import get_executor
from models import ActionStatus

router = APIRouter()

@router.get("/actions")
def list_actions(limit: int = 50):
    return [a.to_dict() for a in get_store().list_actions(limit=limit)]

@router.get("/actions/{exception_id}")
def get_actions(exception_id: str):
    return [a.to_dict() for a in get_store().get_actions(exception_id)]