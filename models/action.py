import uuid
from datetime import datetime
from enum import Enum


class ActionStatus(str, Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class Action:
    def __init__(self, id="", exception_id="", decision_id="", action_type="",
                 action_params=None, status=ActionStatus.PENDING, result=None,
                 executed_by="", execution_target="internal", external_id="",
                 created_at="", completed_at=""):
        self.id = id or str(uuid.uuid4())
        self.exception_id = exception_id
        self.decision_id = decision_id
        self.action_type = action_type
        self.action_params = action_params or {}
        self.status = status
        self.result = result or {}
        self.executed_by = executed_by
        self.execution_target = execution_target
        self.external_id = external_id
        self.created_at = created_at or datetime.now().isoformat()
        self.completed_at = completed_at or ""

    def to_dict(self):
        return {
            "id": self.id, "exception_id": self.exception_id,
            "decision_id": self.decision_id, "action_type": self.action_type,
            "action_params": self.action_params,
            "status": self.status.value if isinstance(self.status, ActionStatus) else self.status,
            "result": self.result, "executed_by": self.executed_by,
            "execution_target": self.execution_target, "external_id": self.external_id,
            "created_at": self.created_at, "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            id=d.get("id", ""), exception_id=d.get("exception_id", ""),
            decision_id=d.get("decision_id", ""), action_type=d.get("action_type", ""),
            action_params=d.get("action_params", {}),
            status=ActionStatus(d.get("status", "pending")),
            result=d.get("result", {}), executed_by=d.get("executed_by", ""),
            execution_target=d.get("execution_target", "internal"),
            external_id=d.get("external_id", ""),
            created_at=d.get("created_at", ""), completed_at=d.get("completed_at", ""))