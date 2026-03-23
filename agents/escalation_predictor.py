"""
Escalation Predictor — predicts whether an open exception will escalate
if not resolved within a given timeframe.
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class EscalationPrediction:
    will_escalate: bool
    escalation_risk_score: float   # 0.0 to 1.0
    days_until_escalation: int
    reason: str
    recommended_urgency: str       # "immediate" / "today" / "this_week"


class EscalationPredictor:
    """
    Predicts escalation risk based on:
      - Days the exception has already been open
      - Historical resolution time for this exception type / vendor
      - Remaining SLA time
      - Financial exposure trend for the vendor
    """

    def predict(self, context, process_data: Optional[dict] = None) -> EscalationPrediction:
        """
        Args:
            context: ExceptionContext for the current case.
            process_data: Output from ProcessAnalyzer.fetch_and_analyze().

        Returns:
            EscalationPrediction dataclass.
        """
        process_data = process_data or {}

        days_open = self._days_open(context)
        sla_days = (context.sla_hours or 48) / 24.0
        remaining_sla = max(sla_days - days_open, 0.0)

        # Historical resolution time for this vendor / exception type
        hist_resolution = self._historical_resolution(context, process_data)

        # Financial exposure contribution
        exposure_factor = self._exposure_factor(context, process_data)

        # SLA consumption ratio
        sla_consumed = min(days_open / sla_days, 1.0) if sla_days > 0 else 1.0

        # Risk score components
        # 1. SLA consumption: higher consumption → higher risk
        sla_risk = sla_consumed

        # 2. Resolution time vs remaining SLA
        if hist_resolution is not None and remaining_sla > 0:
            resolution_risk = min(hist_resolution / remaining_sla, 1.0)
        elif hist_resolution is not None and remaining_sla <= 0:
            resolution_risk = 1.0
        else:
            resolution_risk = 0.5  # unknown history — moderate risk

        # 3. Financial exposure risk
        fin_risk = exposure_factor

        # Blend
        risk_score = round(
            sla_risk * 0.4 + resolution_risk * 0.4 + fin_risk * 0.2, 3
        )

        # Estimate days until escalation
        if remaining_sla <= 0:
            days_until = 0
        elif hist_resolution is not None and hist_resolution > remaining_sla:
            days_until = 0
        else:
            days_until = max(int(remaining_sla), 0)

        will_escalate = risk_score >= 0.6 or days_until <= 1

        # Recommended urgency
        if days_until <= 0 or risk_score >= 0.85:
            urgency = "immediate"
        elif days_until <= 1 or risk_score >= 0.65:
            urgency = "today"
        else:
            urgency = "this_week"

        reason = self._build_reason(
            context, days_open, sla_days, remaining_sla,
            hist_resolution, risk_score, days_until,
        )

        logger.info(
            "[INFO] EscalationPredictor: case=%s risk=%.3f urgency=%s",
            context.case_id, risk_score, urgency,
        )

        return EscalationPrediction(
            will_escalate=will_escalate,
            escalation_risk_score=risk_score,
            days_until_escalation=days_until,
            reason=reason,
            recommended_urgency=urgency,
        )

    # ─────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _days_open(context) -> float:
        """Days since the exception was triggered."""
        try:
            if context.timestamp:
                ts = context.timestamp.replace("Z", "").replace("+00:00", "")
                triggered = datetime.fromisoformat(ts)
                return max((datetime.now() - triggered).total_seconds() / 86400, 0.0)
        except Exception:
            pass
        return 0.0

    @staticmethod
    def _historical_resolution(context, process_data: dict) -> Optional[float]:
        """Return average resolution days for this exception type + vendor."""
        exc_stats = (process_data.get("exception_type_stats") or {}).get(
            context.exception_type, {}
        )
        avg = exc_stats.get("avg_resolution_days")
        if avg and avg > 0:
            return float(avg)

        vendor_stats = (process_data.get("vendor_stats") or {}).get(
            context.vendor or "Unknown", {}
        )
        avg_cycle = vendor_stats.get("avg_cycle_days")
        if avg_cycle and avg_cycle > 0:
            return float(avg_cycle)

        return None

    @staticmethod
    def _exposure_factor(context, process_data: dict) -> float:
        """Normalised financial exposure risk 0-1."""
        exposure = context.financial_exposure or 0.0
        if exposure >= 200000:
            return 1.0
        if exposure >= 100000:
            return 0.8
        if exposure >= 50000:
            return 0.5
        if exposure >= 10000:
            return 0.3
        return 0.1

    @staticmethod
    def _build_reason(
        context, days_open, sla_days, remaining_sla, hist_resolution, risk, days_until
    ) -> str:
        parts = [
            f"Exception open for {days_open:.1f}d (SLA: {sla_days:.1f}d, remaining: {remaining_sla:.1f}d)."
        ]
        if hist_resolution is not None:
            parts.append(
                f"Historical resolution for {context.exception_type} at {context.vendor}: "
                f"{hist_resolution:.1f}d average."
            )
        if context.financial_exposure:
            parts.append(f"Financial exposure: ${context.financial_exposure:,.2f}.")
        parts.append(f"Escalation risk score: {risk:.2f}.")
        if days_until <= 0:
            parts.append("SLA already exhausted — immediate escalation required.")
        elif days_until <= 1:
            parts.append("Less than 1 day before projected escalation.")
        return " ".join(parts)
