import uuid
from datetime import datetime
from enum import Enum


class DecisionType(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    ESCALATED = "escalated"


class Decision:
    def __init__(self, id="", exception_id="", decision_type=DecisionType.APPROVED,
                 analyst_name="", notes="", original_recommendation="",
                 final_action="", created_at=""):
        self.id = id or str(uuid.uuid4())
        self.exception_id = exception_id
        self.decision_type = decision_type
        self.analyst_name = analyst_name
        self.notes = notes
        self.original_recommendation = original_recommendation
        self.final_action = final_action
        self.created_at = created_at or datetime.now().isoformat()

    def to_dict(self):
        return {
            "id": self.id, "exception_id": self.exception_id,
            "decision_type": self.decision_type.value if isinstance(self.decision_type, DecisionType) else self.decision_type,
            "analyst_name": self.analyst_name, "notes": self.notes,
            "original_recommendation": self.original_recommendation,
            "final_action": self.final_action, "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            id=d.get("id", ""), exception_id=d.get("exception_id", ""),
            decision_type=DecisionType(d.get("decision_type", "approved")),
            analyst_name=d.get("analyst_name", ""), notes=d.get("notes", ""),
            original_recommendation=d.get("original_recommendation", ""),
            final_action=d.get("final_action", ""), created_at=d.get("created_at", ""))