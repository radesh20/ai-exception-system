from fastapi import APIRouter
from store import get_store

router = APIRouter()

@router.get("/stats")
def get_stats():
    store = get_store()
    stats = store.get_stats()
    stats["policies"] = [{"category": p.get("category"), "action_type": p.get("action_type"),
        "success_rate": p.get("success_rate", 0), "sample_size": p.get("sample_size", 0)} for p in store.get_policies()]
    return stats

@router.get("/stats/variants")
def get_variants():
    from celonis import get_celonis_client
    return get_celonis_client().get_process_variants()