"""
Payment Risk Agent — assesses payment risk for happy-path cases
by comparing the payment due date against the vendor's historical
average processing time.
"""
import logging
from datetime import datetime, timezone

from models.exception import PaymentRiskResult

logger = logging.getLogger(__name__)

# Risk thresholds (buffer days beyond historical processing time)
_IMMEDIATE_BUFFER = 1.0   # due_date - hist_days <= 1 day  → immediate
_TODAY_BUFFER     = 2.0   # <= 2 days buffer               → today
_WEEK_BUFFER      = 4.0   # <= 4 days buffer               → this_week


class PaymentRiskAgent:
    """
    Analyses payment due-date risk for a happy-path case.
    """

    def analyze(self, context, process_data: dict) -> PaymentRiskResult:
        """
        Args:
            context:      ExceptionContext for the current case.
            process_data: Output from ProcessAnalyzer.fetch_and_analyze().

        Returns:
            PaymentRiskResult dataclass.
        """
        vendor = context.vendor or "Unknown"
        vendor_stats = (process_data.get("vendor_stats") or {}).get(vendor, {})
        hist_days = float(vendor_stats.get("avg_cycle_days") or 3.0)

        # Derive due date from context timestamp + SLA
        due_date, days_until_due = self._compute_due_date(context)

        days_buffer = days_until_due - hist_days

        if days_until_due <= hist_days + _IMMEDIATE_BUFFER:
            risk_level = "immediate"
            insight = (
                f"Pay {vendor} immediately — processing takes {hist_days:.1f} days "
                f"but payment is due in {days_until_due} day(s)."
            )
            action = f"Initiate payment for {vendor} right now to avoid breach."
        elif days_buffer <= _TODAY_BUFFER:
            risk_level = "today"
            insight = (
                f"Pay {vendor} today — processing takes {hist_days:.1f} days, "
                f"due in {days_until_due} day(s) ({days_buffer:.1f}d buffer)."
            )
            action = f"Schedule payment for {vendor} before end of business today."
        elif days_buffer <= _WEEK_BUFFER:
            risk_level = "this_week"
            insight = (
                f"{vendor} payment due in {days_until_due} day(s), "
                f"{days_buffer:.1f}d buffer — process this week."
            )
            action = f"Process payment for {vendor} within the next {int(days_buffer)} day(s)."
        else:
            risk_level = "safe"
            insight = (
                f"{vendor} payment has {days_buffer:.1f} days buffer "
                f"(due in {days_until_due}d, processing {hist_days:.1f}d)."
            )
            action = "No immediate action required."

        logger.info(
            "[INFO] PaymentRiskAgent: case=%s vendor=%s risk_level=%s days_until_due=%d",
            context.case_id, vendor, risk_level, days_until_due,
        )

        return PaymentRiskResult(
            vendor=vendor,
            due_date=due_date,
            days_until_due=days_until_due,
            historical_processing_days=hist_days,
            days_buffer=round(days_buffer, 2),
            risk_level=risk_level,
            insight=insight,
            recommended_action=action,
        )

    # ─────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────

    def _compute_due_date(self, context):
        """Return (due_date_str, days_until_due) based on context."""
        sla_hours = context.sla_hours or 48
        try:
            created = datetime.fromisoformat(context.timestamp.replace("Z", "+00:00"))
        except Exception:
            created = datetime.now(timezone.utc)

        from datetime import timedelta
        due_dt = created + timedelta(hours=sla_hours)
        now_dt = datetime.now(timezone.utc)
        if due_dt.tzinfo is None:
            due_dt = due_dt.replace(tzinfo=timezone.utc)

        days_until_due = max(0, round((due_dt - now_dt).total_seconds() / 86400))
        return due_dt.strftime("%Y-%m-%d"), days_until_due
