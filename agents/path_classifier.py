"""
Path Classifier — decides whether a case is on the happy path
or has deviated from expected P2P flow.
"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PathClassification:
    route: str           # "happy_path" or "exception"
    deviation_score: float
    reason: str
    process_context: dict  # relevant turnaround data for this case


class PathClassifier:
    """
    Classifies a case as happy-path or exception by combining:
      - Path match against expected P2P sequence
      - Deviation score from ExceptionContext
      - Whether cycle time is within normal bounds for the vendor
    """

    HAPPY_PATH_STEPS = [
        "Purchase Requisition Created",
        "Purchase Order Created",
        "Invoice Received",
        "Invoice Cleared",
    ]

    # Terminal activities that indicate a successfully completed happy path case.
    TERMINAL_ACTIVITIES = {"Invoice Cleared", "Payment Complete"}

    def classify(self, context, process_data: Optional[dict] = None) -> PathClassification:
        """
        Args:
            context: ExceptionContext for the current case.
            process_data: Output from ProcessAnalyzer.fetch_and_analyze().

        Returns:
            PathClassification dataclass.
        """
        process_data = process_data or {}

        # 1. Path match score (0 = fully deviated, 1 = perfect match)
        path_score = self._path_match_score(context.actual_path)

        # 2. Context deviation score (normalised to 0-1)
        ctx_deviation = self._context_deviation(context)

        # 3. Vendor cycle time check
        vendor_ok, vendor_context = self._vendor_cycle_ok(context, process_data)

        # 4. Blend into a single deviation score (kept for informational purposes)
        deviation_score = round(
            (1.0 - path_score) * 0.4 + ctx_deviation * 0.4 + (0.0 if vendor_ok else 0.2),
            3,
        )

        # 5. Determine route based on terminal activity and path completeness.
        # A case is happy_path only when the actual path ends with a recognised
        # terminal activity AND all expected happy-path steps are present.
        actual_terminal = (context.actual_path or [])[-1] if context.actual_path else ""
        ends_at_terminal = actual_terminal in self.TERMINAL_ACTIVITIES
        # Consider the path complete if all expected happy-path steps are
        # present (the case may contain extra activities, which is fine).
        all_steps_present = path_score >= 1.0

        if ends_at_terminal and all_steps_present:
            route = "happy_path"
            reason = (
                f"All {len(self.HAPPY_PATH_STEPS)} happy-path steps present. "
                f"Terminal activity '{actual_terminal}' confirms successful completion."
            )
        else:
            route = "exception"
            missing_reason = (
                f"terminal activity '{actual_terminal}' not in expected set"
                if not ends_at_terminal
                else f"path match only {path_score:.0%}"
            )
            reason = (
                f"Path match {path_score:.0%}, deviation {deviation_score:.2f}, "
                f"{missing_reason}."
            )

        logger.info(
            "[INFO] PathClassifier: case=%s route=%s deviation=%.3f",
            context.case_id, route, deviation_score,
        )

        return PathClassification(
            route=route,
            deviation_score=deviation_score,
            reason=reason,
            process_context=vendor_context,
        )

    # ─────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────

    def _path_match_score(self, actual_path: list) -> float:
        """Fraction of happy-path steps present in the actual path."""
        if not actual_path:
            return 0.0
        matches = sum(1 for step in self.HAPPY_PATH_STEPS if step in actual_path)
        return round(matches / len(self.HAPPY_PATH_STEPS), 3)

    def _context_deviation(self, context) -> float:
        """Derive a 0-1 deviation signal from ExceptionContext fields."""
        score = 0.0
        # Severity score is already 0-1
        if context.severity_score is not None:
            score += context.severity_score * 0.5
        # Compliance flag adds a fixed penalty
        if context.compliance_flag:
            score += 0.3
        # Large financial exposure relative to threshold
        if context.financial_exposure and context.financial_exposure > 100000:
            score += 0.2
        elif context.financial_exposure and context.financial_exposure > 50000:
            score += 0.1
        return round(min(score, 1.0), 3)

    def _vendor_cycle_ok(self, context, process_data: dict):
        """
        Check if vendor's historical average cycle days is within
        reasonable range.  Returns (bool, context_dict).
        """
        vendor = context.vendor or "Unknown"
        vendor_stats = (process_data.get("vendor_stats") or {}).get(vendor, {})
        avg_cycle = vendor_stats.get("avg_cycle_days")
        sla_days = (context.sla_hours or 48) / 24.0

        ctx = {
            "vendor": vendor,
            "avg_cycle_days": avg_cycle,
            "sla_days": sla_days,
            "vendor_stats": vendor_stats,
        }

        if avg_cycle is None:
            # No data — assume ok to avoid false positives
            return True, ctx

        # If vendor historically takes longer than the SLA, flag as exception
        within_bounds = avg_cycle <= sla_days * 1.5
        return within_bounds, ctx
