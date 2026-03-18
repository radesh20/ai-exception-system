import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config.settings as settings

def get_executor():
    if settings.EXECUTION_MODE == "servicenow" and settings.SERVICENOW_ENABLED:
        from execution.servicenow_executor import ServiceNowExecutor
        return ServiceNowExecutor()
    from execution.internal_executor import InternalExecutor
    return InternalExecutor()