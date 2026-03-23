"""
Happy Path API routes — endpoints for happy path cases and process insights.
"""
from typing import Optional
from fastapi import APIRouter
from store import get_store
from agents.process_agent_recommender import ProcessAgentRecommender
from celonis.process_analyzer import ProcessAnalyzer
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Urgency sort order ──────────────────────────────────────────────────────
_URGENCY_ORDER = {"immediate": 0, "today": 1, "critical": 2, "at_risk": 3, "this_week": 4, "safe": 5, "on_track": 6}


def _urgency_key(record: dict) -> int:
    pr = (record.get("payment_risk") or {}).get("risk_level", "safe")
    sla = (record.get("sla_monitor") or {}).get("status", "on_track")
    return min(_URGENCY_ORDER.get(pr, 9), _URGENCY_ORDER.get(sla, 9))


def _is_alert(record: dict) -> bool:
    pr = (record.get("payment_risk") or {}).get("risk_level", "safe")
    sla = (record.get("sla_monitor") or {}).get("status", "on_track")
    return pr in ("immediate", "today") or sla in ("critical", "at_risk")


# ── Happy Path Cases ────────────────────────────────────────────────────────

@router.get("/happy-path")
def list_happy_path_cases(limit: int = 200, offset: int = 0):
    """Return all happy path cases with summary stats."""
    store = get_store()
    cases = store.get_happy_path_cases(limit=limit, offset=offset)
    insights_map = {r.get("case_id"): r for r in store.get_process_insights(limit=500)}

    enriched = []
    for c in cases:
        ctx = c.get("context") or {}
        case_id = ctx.get("case_id", "")
        insight = insights_map.get(case_id, {})
        sla_status = (insight.get("sla_monitor") or {}).get("status", "on_track")
        enriched.append({
            **c,
            "sla_status": sla_status,
            "payment_risk_level": (insight.get("payment_risk") or {}).get("risk_level", "safe"),
        })

    total = len(enriched)
    auto_completed = sum(1 for c in enriched if c.get("status") == "completed")
    sla_safe = sum(1 for c in enriched if c.get("sla_status") == "on_track")
    at_risk = sum(1 for c in enriched if c.get("sla_status") in ("at_risk", "critical"))

    return {
        "summary": {
            "total": total,
            "auto_completed": auto_completed,
            "sla_safe": sla_safe,
            "at_risk": at_risk,
        },
        "cases": enriched,
    }


@router.get("/happy-path/{case_id}")
def get_happy_path_case(case_id: str):
    """Return full detail for one happy path case including agent results."""
    store = get_store()
    case = store.get_happy_path_case(case_id)
    if not case:
        return {"error": "Not found"}
    insight = store.get_process_insight(case_id)
    return {**case, "process_insights": insight}


# ── Process Insights ────────────────────────────────────────────────────────

@router.get("/process-insights")
def list_process_insights(limit: int = 200):
    """Return all process insights sorted by urgency."""
    store = get_store()
    data = store.get_process_insights(limit=limit)
    return sorted(data, key=_urgency_key)


@router.get("/process-insights/alerts")
def get_process_insight_alerts():
    """Return only immediate and critical process insight records."""
    store = get_store()
    data = store.get_process_insights(limit=500)
    alerts = [r for r in data if _is_alert(r)]
    return sorted(alerts, key=_urgency_key)


# ── Process Agents ──────────────────────────────────────────────────────────

# Built-in happy-path agents
_HAPPY_PATH_AGENTS = [
    {
        "agent_name": "PaymentRiskAgent",
        "function": "Assesses payment risk based on due date vs vendor historical processing time.",
        "process_stage": "Payment Processing",
        "type": "Happy Path",
        "status": "Built",
        "inputs": ["ExceptionContext", "vendor_stats"],
        "outputs": ["PaymentRiskResult"],
    },
    {
        "agent_name": "SLAMonitorAgent",
        "function": "Measures SLA consumption percentage and flags at-risk or critical cases.",
        "process_stage": "Escalation Management",
        "type": "Happy Path",
        "status": "Built",
        "inputs": ["ExceptionContext"],
        "outputs": ["SLAMonitorResult"],
    },
    {
        "agent_name": "ProcessOptimizationAgent",
        "function": "Identifies bottleneck stages by comparing case cycle time to historical averages.",
        "process_stage": "Process Intelligence",
        "type": "Happy Path",
        "status": "Built",
        "inputs": ["ExceptionContext", "activity_stats"],
        "outputs": ["ProcessOptimizationResult"],
    },
]


@router.get("/process-agents")
def list_process_agents():
    """Return global agent recommendations including happy path and exception agents."""
    try:
        process_data = ProcessAnalyzer().fetch_and_analyze()
    except Exception as exc:
        logger.warning("[WARN] process-agents: ProcessAnalyzer unavailable: %s", exc)
        process_data = {}

    try:
        recommended = ProcessAgentRecommender().recommend(process_data)
    except Exception as exc:
        logger.error("[ERROR] process-agents: recommender failed: %s", exc)
        recommended = []

    # Tag recommended agents as exception-pipeline type
    for r in recommended:
        r.setdefault("type", "Exception")
        r.setdefault("status", "Built")

    all_agents = _HAPPY_PATH_AGENTS + recommended

    # Build a simple pipeline flowchart representation
    flowchart = [
        {"stage": "Context Building", "agent": "ContextBuilderAgent", "type": "Shared"},
        {"stage": "Path Classification", "agent": "PathClassifier", "type": "Shared"},
        {"stage": "Happy Path Pipeline", "agent": "PaymentRiskAgent / SLAMonitorAgent / ProcessOptimizationAgent", "type": "Happy Path"},
        {"stage": "Exception Pipeline", "agent": "RootCauseAgent / ClassifierAgent / ActionRecommender", "type": "Exception"},
        {"stage": "Decision Routing", "agent": "DecisionRouter", "type": "Shared"},
    ]

    return {
        "flowchart": flowchart,
        "agents": all_agents,
        "process_data_summary": {
            "case_count": process_data.get("case_count", 0),
            "process_health": process_data.get("process_health", {}),
        },
    }


@router.get("/process-agents/{case_id}")
def get_process_agents_for_case(case_id: str):
    """Return per-case agent data highlighting which agents ran."""
    store = get_store()
    case = store.get_happy_path_case(case_id)
    insight = store.get_process_insight(case_id)

    if not case and not insight:
        # Try exception pipeline case
        exc = store.get_exception(case_id)
        if not exc:
            return {"error": "Not found"}
        return {
            "case_id": case_id,
            "pipeline": "exception",
            "agents_ran": ["ContextBuilderAgent", "PathClassifier", "RootCauseAgent", "ClassifierAgent", "ActionRecommender"],
            "agents_skipped": ["PaymentRiskAgent", "SLAMonitorAgent", "ProcessOptimizationAgent"],
            "results": {},
        }

    agents_ran = []
    if insight.get("payment_risk"):
        agents_ran.append("PaymentRiskAgent")
    if insight.get("sla_monitor"):
        agents_ran.append("SLAMonitorAgent")
    if insight.get("process_optimization"):
        agents_ran.append("ProcessOptimizationAgent")

    return {
        "case_id": case_id,
        "pipeline": "happy_path",
        "agents_ran": ["ContextBuilderAgent", "PathClassifier"] + agents_ran,
        "agents_skipped": ["RootCauseAgent", "ClassifierAgent", "ActionRecommender"],
        "results": {
            "payment_risk": insight.get("payment_risk"),
            "sla_monitor": insight.get("sla_monitor"),
            "process_optimization": insight.get("process_optimization"),
        },
    }
