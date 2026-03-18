from fastapi import APIRouter
from store import get_store
from agents import LearningEngine

router = APIRouter()

@router.get("/learning")
def get_insights():
    return LearningEngine(get_store()).get_insights()

@router.get("/learning/policies")
def get_policy_perf():
    return [{"category": p.get("category"), "action_type": p.get("action_type"),
        "success_rate": round(p.get("success_rate", 0) * 100, 1), "sample_size": p.get("sample_size", 0),
        "confidence": "high" if p.get("sample_size", 0) >= 20 else "medium" if p.get("sample_size", 0) >= 5 else "low"}
        for p in get_store().get_policies()]

@router.get("/learning/history")
def get_history(limit: int = 100):
    return get_store().get_historical_cases()[-limit:]