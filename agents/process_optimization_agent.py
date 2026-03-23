"""
Process Optimization Agent — compares this case's cycle time against
the historical average for happy-path cases of the same vendor and
exception type to surface bottleneck stages.
"""
import logging

from models.exception import ProcessOptimizationResult

logger = logging.getLogger(__name__)

# Default historical average stage time (days) when no data is available
_DEFAULT_AVG_STAGE_DAYS = 1.0


class ProcessOptimizationAgent:
    """
    Identifies process bottlenecks for a happy-path case.
    """

    def analyze(self, context, process_data: dict) -> ProcessOptimizationResult:
        """
        Args:
            context:      ExceptionContext for the current case.
            process_data: Output from ProcessAnalyzer.fetch_and_analyze().

        Returns:
            ProcessOptimizationResult dataclass.
        """
        case_id = context.case_id
        vendor = context.vendor or "Unknown"

        # Determine the likely bottleneck stage from the actual process path
        bottleneck_stage = self._find_bottleneck(context, process_data)

        # Historical average for this stage from process data
        avg_stage_time = self._avg_stage_time(bottleneck_stage, process_data)

        # Estimate current stage time from SLA consumption vs path length
        current_stage_time = self._estimate_current_stage_time(context)

        delay_days = round(max(0.0, current_stage_time - avg_stage_time), 2)

        if delay_days >= 2.0:
            insight = (
                f"Stage '{bottleneck_stage}' for case {case_id} ({vendor}) took "
                f"{current_stage_time:.1f}d vs avg {avg_stage_time:.1f}d "
                f"— {delay_days:.1f}d delay detected."
            )
            action = (
                f"Review '{bottleneck_stage}' process for {vendor}; "
                f"consider automation or increased resource allocation."
            )
        elif delay_days >= 0.5:
            insight = (
                f"Stage '{bottleneck_stage}' is slightly slower than average "
                f"({current_stage_time:.1f}d vs {avg_stage_time:.1f}d)."
            )
            action = f"Monitor '{bottleneck_stage}' for recurrence and benchmark against peers."
        else:
            insight = (
                f"Case {case_id} processed efficiently — "
                f"'{bottleneck_stage}' completed in {current_stage_time:.1f}d "
                f"(avg {avg_stage_time:.1f}d)."
            )
            action = "No optimisation required; performance is within normal bounds."

        logger.info(
            "[INFO] ProcessOptimizationAgent: case=%s bottleneck=%s delay=%.2fd",
            case_id, bottleneck_stage, delay_days,
        )

        return ProcessOptimizationResult(
            case_id=case_id,
            bottleneck_stage=bottleneck_stage,
            avg_stage_time=round(avg_stage_time, 2),
            current_stage_time=round(current_stage_time, 2),
            delay_days=delay_days,
            insight=insight,
            recommended_action=action,
        )

    # ─────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────

    def _find_bottleneck(self, context, process_data: dict) -> str:
        """Return the stage most likely to be the bottleneck."""
        health = (process_data.get("process_health") or {})
        delay_stages = [
            s.get("stage", "") for s in (health.get("delay_causing_stages") or [])
        ]

        # Prefer a known delay stage that appears in this case's path
        for stage in delay_stages:
            if stage and stage in (context.actual_path or []):
                return stage

        # Fall back to the deviation point or the last path step
        if context.deviation_point:
            return context.deviation_point

        if context.actual_path:
            return context.actual_path[-1]

        return "Invoice Processing"

    def _avg_stage_time(self, stage: str, process_data: dict) -> float:
        """Return historical average cycle days for the given stage."""
        activity_stats = process_data.get("activity_stats") or {}
        stage_data = activity_stats.get(stage, {})
        avg = stage_data.get("avg_duration_days")
        return float(avg) if avg is not None else _DEFAULT_AVG_STAGE_DAYS

    def _estimate_current_stage_time(self, context) -> float:
        """Rough estimate of time spent at the bottleneck stage."""
        from datetime import datetime, timezone
        sla_hours = context.sla_hours or 48
        try:
            created = datetime.fromisoformat(context.timestamp.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            total_days = (now - created).total_seconds() / 86400.0
        except Exception:
            total_days = sla_hours / 24.0

        path_len = max(len(context.actual_path or []), 1)
        return round(total_days / path_len, 2)
