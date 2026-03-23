"""
SLA Monitor Agent — checks how much of the SLA time has been consumed
for a happy-path case and flags at-risk or critical cases.
"""
import logging
from datetime import datetime, timezone

from models.exception import SLAMonitorResult

logger = logging.getLogger(__name__)

# SLA consumption thresholds
_CRITICAL_PCT  = 80.0   # >=80% consumed → critical
_AT_RISK_PCT   = 60.0   # >=60% consumed → at_risk


class SLAMonitorAgent:
    """
    Measures SLA consumption for a happy-path case.
    """

    def analyze(self, context, process_data: dict) -> SLAMonitorResult:
        """
        Args:
            context:      ExceptionContext for the current case.
            process_data: Output from ProcessAnalyzer.fetch_and_analyze().

        Returns:
            SLAMonitorResult dataclass.
        """
        case_id = context.case_id
        sla_hours_total = context.sla_hours or 48

        hours_consumed = self._hours_elapsed(context)
        # Cap at total SLA to avoid >100%
        hours_consumed = min(hours_consumed, float(sla_hours_total))
        consumption_pct = round((hours_consumed / sla_hours_total) * 100.0, 1) if sla_hours_total else 0.0

        if consumption_pct >= _CRITICAL_PCT:
            status = "critical"
            insight = (
                f"Case {case_id} has consumed {consumption_pct:.1f}% of its "
                f"{sla_hours_total}h SLA — critical risk of breach."
            )
            action = "Escalate immediately and fast-track resolution."
        elif consumption_pct >= _AT_RISK_PCT:
            status = "at_risk"
            insight = (
                f"Case {case_id} has consumed {consumption_pct:.1f}% of its "
                f"{sla_hours_total}h SLA — at risk."
            )
            action = "Prioritise this case and complete within the remaining SLA window."
        else:
            status = "on_track"
            insight = (
                f"Case {case_id} has consumed {consumption_pct:.1f}% of its "
                f"{sla_hours_total}h SLA — on track."
            )
            action = "No immediate escalation required; continue normal processing."

        logger.info(
            "[INFO] SLAMonitorAgent: case=%s consumed=%.1f%% status=%s",
            case_id, consumption_pct, status,
        )

        return SLAMonitorResult(
            case_id=case_id,
            sla_hours_total=sla_hours_total,
            sla_hours_consumed=round(hours_consumed, 2),
            sla_consumption_pct=consumption_pct,
            status=status,
            insight=insight,
            recommended_action=action,
        )

    # ─────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────

    def _hours_elapsed(self, context) -> float:
        """Return hours elapsed since the case was created."""
        try:
            created = datetime.fromisoformat(context.timestamp.replace("Z", "+00:00"))
        except Exception:
            return 0.0

        now = datetime.now(timezone.utc)
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)

        return (now - created).total_seconds() / 3600.0
