"""
Process-Aware Prompt Builder — enriches PromptEngineerAgent with
vendor turnaround context before prompt generation.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class ProcessAwarePromptBuilder:
    """
    Builds a human-readable process context summary from vendor
    turnaround data and the current ExceptionContext.

    The output is passed as `process_context` to PromptEngineerAgent.generate().
    """

    def build(self, context, process_data: Optional[dict] = None) -> str:
        """
        Args:
            context: ExceptionContext for the current case.
            process_data: Output from ProcessAnalyzer.fetch_and_analyze().

        Returns:
            A human-readable process context string.
        """
        if not process_data:
            return ""

        vendor = context.vendor or "Unknown"
        vendor_stats = (process_data.get("vendor_stats") or {}).get(vendor, {})
        exc_type = context.exception_type or "unknown"
        exc_stats = (process_data.get("exception_type_stats") or {}).get(exc_type, {})
        health = process_data.get("process_health") or {}

        parts = []

        # Vendor average cycle
        avg_cycle = vendor_stats.get("avg_cycle_days")
        if avg_cycle is not None:
            parts.append(
                f"Vendor {vendor} historically takes {avg_cycle:.1f} days for end-to-end payment."
            )

        # SLA proximity
        sla_days = (context.sla_hours or 48) / 24.0
        if avg_cycle is not None and sla_days > 0:
            days_remaining = sla_days  # simplified — full context would use triggered_at
            if avg_cycle >= days_remaining:
                parts.append(
                    f"Historical cycle ({avg_cycle:.1f}d) meets or exceeds remaining SLA "
                    f"({days_remaining:.1f}d) — immediate action recommended."
                )
            else:
                buffer = days_remaining - avg_cycle
                parts.append(
                    f"Remaining SLA is {days_remaining:.1f}d; vendor typically needs "
                    f"{avg_cycle:.1f}d, leaving {buffer:.1f}d buffer."
                )

        # Exception type average resolution
        avg_resolution = exc_stats.get("avg_resolution_days")
        if avg_resolution and avg_resolution > 0:
            parts.append(
                f"Similar {exc_type.replace('_', ' ')} exceptions resolve in "
                f"{avg_resolution:.1f} days on average for {vendor}."
            )

        # Payment delay frequency
        delay_freq = vendor_stats.get("payment_delay_frequency")
        if delay_freq is not None:
            pct = round(delay_freq * 100)
            if pct > 50:
                parts.append(
                    f"Vendor {vendor} has payment delays in {pct}% of cases — "
                    f"elevated risk of recurrence."
                )

        # Stage-level delay insight
        stage_days = vendor_stats.get("avg_stage_days") or {}
        slowest = max(stage_days.items(), key=lambda x: x[1]) if stage_days else None
        if slowest:
            parts.append(
                f"Slowest stage for {vendor}: '{slowest[0]}' at {slowest[1]:.1f} days average."
            )

        # Process health context
        sla_rate = health.get("sla_compliance_rate")
        if sla_rate is not None:
            parts.append(
                f"Overall P2P SLA compliance: {sla_rate:.0%}."
            )

        if not parts:
            return (
                f"No historical turnaround data available for vendor {vendor}. "
                f"Proceed with standard exception handling."
            )

        logger.info("[INFO] ProcessAwarePromptBuilder: built context for vendor=%s", vendor)
        return " ".join(parts)
