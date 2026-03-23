import uuid
from datetime import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field


class ExceptionStatus(str, Enum):
    NEW = "new"
    ANALYZING = "analyzing"
    PENDING_DECISION = "pending_decision"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExceptionContext:
    case_id: str
    exception_type: str
    financial_exposure: float
    severity_score: float
    deviation_point: str
    actual_path: list
    happy_path: list
    assigned_team: str
    vendor: str
    sla_hours: int
    compliance_flag: bool
    timestamp: str
    raw_data: dict = field(default_factory=dict)


@dataclass
class RootCauseAnalysis:
    hypothesis: str
    confidence: float
    supporting_cases: list
    pattern_description: str
    causal_factors: list


@dataclass
class Classification:
    category: str
    priority: int
    is_novel: bool
    routing: str
    confidence: float
    responsible_team: str = ""


@dataclass
class PaymentRiskResult:
    vendor: str
    due_date: str
    days_until_due: int
    historical_processing_days: float
    days_buffer: float
    risk_level: str         # "immediate" / "today" / "this_week" / "safe"
    insight: str
    recommended_action: str


@dataclass
class SLAMonitorResult:
    case_id: str
    sla_hours_total: int
    sla_hours_consumed: float
    sla_consumption_pct: float
    status: str             # "on_track" / "at_risk" / "critical"
    insight: str
    recommended_action: str


@dataclass
class ProcessOptimizationResult:
    case_id: str
    bottleneck_stage: str
    avg_stage_time: float
    current_stage_time: float
    delay_days: float
    insight: str
    recommended_action: str


class ExceptionModel:
    def __init__(self, id="", status=ExceptionStatus.NEW, context=None,
                 root_cause=None, classification=None, recommended_action=None,
                 recommended_action_params=None, ai_reasoning="",
                 created_at="", updated_at="",
                 prompt_package=None, erp_recommendation=None,
                 erp_execution_status=None):
        self.id = id or str(uuid.uuid4())
        self.status = status
        self.context = context
        self.root_cause = root_cause
        self.classification = classification
        self.recommended_action = recommended_action
        self.recommended_action_params = recommended_action_params or {}
        self.ai_reasoning = ai_reasoning
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.prompt_package = prompt_package  # Dict: AI-generated prompts used
        self.erp_recommendation = erp_recommendation  # Dict: suggested ERP action
        self.erp_execution_status = erp_execution_status  # "pending"/"approved"/"rejected"/"executed"

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status.value if isinstance(self.status, ExceptionStatus) else self.status,
            "context": self.context.__dict__ if self.context else None,
            "root_cause": self.root_cause.__dict__ if self.root_cause else None,
            "classification": self.classification.__dict__ if self.classification else None,
            "recommended_action": self.recommended_action,
            "recommended_action_params": self.recommended_action_params,
            "ai_reasoning": self.ai_reasoning,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "prompt_package": self.prompt_package,
            "erp_recommendation": self.erp_recommendation,
            "erp_execution_status": self.erp_execution_status,
        }

    @classmethod
    def from_dict(cls, d):
        ctx = None
        if d.get("context"):
            c = d["context"]
            ctx = ExceptionContext(
                case_id=c.get("case_id", ""), exception_type=c.get("exception_type", ""),
                financial_exposure=c.get("financial_exposure", 0), severity_score=c.get("severity_score", 0),
                deviation_point=c.get("deviation_point", ""), actual_path=c.get("actual_path", []),
                happy_path=c.get("happy_path", []), assigned_team=c.get("assigned_team", ""),
                vendor=c.get("vendor", ""), sla_hours=c.get("sla_hours", 48),
                compliance_flag=c.get("compliance_flag", False), timestamp=c.get("timestamp", ""),
                raw_data=c.get("raw_data", {}))

        rc = None
        if d.get("root_cause"):
            r = d["root_cause"]
            rc = RootCauseAnalysis(
                hypothesis=r.get("hypothesis", ""), confidence=r.get("confidence", 0),
                supporting_cases=r.get("supporting_cases", []),
                pattern_description=r.get("pattern_description", ""),
                causal_factors=r.get("causal_factors", []))

        cl = None
        if d.get("classification"):
            x = d["classification"]
            cl = Classification(
                category=x.get("category", ""), priority=x.get("priority", 1),
                is_novel=x.get("is_novel", False), routing=x.get("routing", "human"),
                confidence=x.get("confidence", 0),
                responsible_team=x.get("responsible_team", ""))

        return cls(
            id=d.get("id", ""), status=ExceptionStatus(d.get("status", "new")),
            context=ctx, root_cause=rc, classification=cl,
            recommended_action=d.get("recommended_action"),
            recommended_action_params=d.get("recommended_action_params", {}),
            ai_reasoning=d.get("ai_reasoning", ""),
            created_at=d.get("created_at", ""), updated_at=d.get("updated_at", ""),
            prompt_package=d.get("prompt_package"),
            erp_recommendation=d.get("erp_recommendation"),
            erp_execution_status=d.get("erp_execution_status"),
        )