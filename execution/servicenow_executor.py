import requests
from datetime import datetime
import config.settings as settings
from models import Action, ActionStatus
from execution.base import BaseExecutor

class ServiceNowExecutor(BaseExecutor):
    def __init__(self):
        self.instance = settings.SERVICENOW_INSTANCE
        self.auth = (settings.SERVICENOW_USER, settings.SERVICENOW_PASSWORD)
        self.table = settings.SERVICENOW_TABLE

    def execute(self, action):
        if not settings.SERVICENOW_ENABLED:
            action.status = ActionStatus.FAILED
            action.result = {"error": "ServiceNow disabled"}
            return action
        action.status = ActionStatus.EXECUTING
        action.execution_target = "servicenow"
        try:
            r = requests.post(f"https://{self.instance}/api/now/table/{self.table}",
                json={"short_description": f"P2P Exception: {action.action_type}",
                      "description": f"Exception ID: {action.exception_id}\nAction: {action.action_type}",
                      "priority": {5:1,4:2,3:3,2:4,1:5}.get(action.action_params.get("priority",3), 3)},
                auth=self.auth, headers={"Content-Type":"application/json"}, timeout=30)
            r.raise_for_status()
            result = r.json().get("result", {})
            action.status = ActionStatus.COMPLETED
            action.external_id = result.get("sys_id", "")
            action.result = {"message": "ServiceNow ticket created", "number": result.get("number", "")}
        except Exception as e:
            action.status = ActionStatus.FAILED
            action.result = {"error": str(e)}
        action.completed_at = datetime.now().isoformat()
        return action

    def rollback(self, action):
        action.status = ActionStatus.ROLLED_BACK
        action.completed_at = datetime.now().isoformat()
        return action