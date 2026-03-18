from datetime import datetime
from models import Action, ActionStatus
from execution.base import BaseExecutor

class InternalExecutor(BaseExecutor):
    def execute(self, action):
        action.status = ActionStatus.EXECUTING
        action.execution_target = "internal"
        try:
            action.status = ActionStatus.COMPLETED
            action.result = {"message": f"Action {action.action_type} executed successfully"}
            action.completed_at = datetime.now().isoformat()
        except Exception as e:
            action.status = ActionStatus.FAILED
            action.result = {"error": str(e)}
            action.completed_at = datetime.now().isoformat()
        return action

    def rollback(self, action):
        action.status = ActionStatus.ROLLED_BACK
        action.result["rollback"] = {"message": "Rolled back", "timestamp": datetime.now().isoformat()}
        action.completed_at = datetime.now().isoformat()
        return action