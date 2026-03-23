"""
Agent Interaction Tracer — captures full prompt/response pairs for
every agent step in the exception pipeline.

This is an additive companion to agents/tracer.py.
The existing AgentTracer is NOT modified or replaced.
"""
import uuid
import time
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class AgentInteractionTracer:
    """
    Records the full prompt sent into each agent and the full response
    that came out, together with timing and handoff metadata.

    Usage:
        tracer = AgentInteractionTracer(exception_id="abc123")
        tracer.record(
            agent_name="Root Cause Agent",
            prompt="Analyze this exception...",
            response="Hypothesis: ...",
            duration_ms=120,
        )
        # Optionally persist via a JsonStore instance
        tracer.flush(store)
    """

    def __init__(self, exception_id: str = ""):
        self.trace_id = str(uuid.uuid4())[:12]
        self.exception_id = exception_id
        self.steps: list = []
        self.start_time = time.time()

    def record(
        self,
        agent_name: str,
        prompt: str,
        response: str,
        duration_ms: int = 0,
        output_used_as_input_by: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        """
        Capture one agent step.

        Args:
            agent_name: Human-readable agent label.
            prompt: The full prompt text sent to the agent.
            response: The full response text produced by the agent.
            duration_ms: Wall-clock time the agent took.
            output_used_as_input_by: Name of the next agent that receives
                                     this step's output as its input.
            metadata: Any extra key/value pairs to store with this step.
        """
        step = {
            "step_number": len(self.steps) + 1,
            "trace_id": self.trace_id,
            "exception_id": self.exception_id,
            "agent_name": agent_name,
            "prompt": prompt,
            "response": response,
            "duration_ms": duration_ms,
            "output_used_as_input_by": output_used_as_input_by,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        self.steps.append(step)
        logger.info(
            "[INFO] AgentInteractionTracer: trace=%s step=%d agent=%s %dms",
            self.trace_id, step["step_number"], agent_name, duration_ms,
        )

    def get_summary(self) -> dict:
        """Return a summary of all recorded steps."""
        total_ms = int((time.time() - self.start_time) * 1000)
        return {
            "trace_id": self.trace_id,
            "exception_id": self.exception_id,
            "total_steps": len(self.steps),
            "total_duration_ms": total_ms,
            "started_at": datetime.fromtimestamp(self.start_time).isoformat(),
            "steps": self.steps,
        }

    def flush(self, store):
        """
        Persist all recorded steps to the store as a single interaction record.

        Args:
            store: A JsonStore instance that has save_agent_interaction().
        """
        if not self.steps:
            return
        try:
            record = {
                "id": self.trace_id,
                "exception_id": self.exception_id,
                "recorded_at": datetime.now().isoformat(),
                "total_steps": len(self.steps),
                "total_duration_ms": int((time.time() - self.start_time) * 1000),
                "steps": self.steps,
            }
            store.save_agent_interaction(record)
            logger.info(
                "[OK] AgentInteractionTracer: flushed %d steps for exception=%s",
                len(self.steps), self.exception_id,
            )
        except Exception as exc:
            logger.error("[ERROR] AgentInteractionTracer: flush failed: %s", exc)
