# agents/tracer.py
import time
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentTracer:
    def __init__(self):
        self.trace_id = str(uuid.uuid4())[:8]
        self.steps = []
        self.start_time = time.time()

    def record(self, agent_name, input_summary, output_summary,
               details=None, duration_ms=0, status="success"):
        step = {
            "step_number": len(self.steps) + 1,
            "agent": agent_name,
            "input": input_summary,
            "output": output_summary,
            "details": details or {},
            "duration_ms": duration_ms,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }
        self.steps.append(step)
        logger.info(
            "Agent step | trace=%s | step=%d | agent=%s | status=%s | %dms",
            self.trace_id, step["step_number"], agent_name, status, duration_ms
        )

    def record_connection(self, from_agent, to_agent, message, data_passed=None):
        connection = {
            "step_number": len(self.steps) + 1,
            "agent": f"{from_agent} → {to_agent}",
            "input": f"Output of {from_agent}",
            "output": message,
            "details": {
                "from": from_agent,
                "to": to_agent,
                "data_keys": list((data_passed or {}).keys()),
                "message": message,
            },
            "duration_ms": 0,
            "status": "connection",
            "timestamp": datetime.now().isoformat(),
        }
        self.steps.append(connection)

    def get_summary(self):
        total_ms = int((time.time() - self.start_time) * 1000)
        return {
            "trace_id": self.trace_id,
            "total_steps": len(self.steps),
            "total_duration_ms": total_ms,
            "started_at": datetime.fromtimestamp(self.start_time).isoformat(),
            "steps": self.steps,
        }