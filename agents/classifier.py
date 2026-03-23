from datetime import datetime, timedelta
import logging
from models import ExceptionContext, RootCauseAnalysis, Classification

logger = logging.getLogger(__name__)

class ClassifierAgent:
    KNOWN = {"payment_mismatch", "quantity_mismatch", "invoice_mismatch", "goods_receipt_mismatch", "tax_code_change"}
    LOW_CONFIDENCE_THRESHOLD = 0.6

    # VENDOR_TYPE_MAP has been removed — vendor patterns are learned dynamically
    # from historical data. See _analyze_vendor_pattern() below.
    # TODO_VENDOR_PATTERN: Add manual hints here ONLY when historical confidence is HIGH
    # e.g. after observing 50+ consistent cases for a vendor.

    def classify(self, context, root_cause, prompt_package=None, historical_cases=None, process_data: dict = None):
        cat = self._normalize_exception_type(context.exception_type)
        is_novel = self._is_truly_novel(cat, root_cause)
        if is_novel:
            cat = "novel_exception"
        priority = self._priority(context, process_data)

        # Confidence boost comes ONLY from prompt_package (vendor intelligence
        # from GPT-4o or rule-based path — NOT from hardcoded vendor assumptions).
        effective_confidence = root_cause.confidence
        if prompt_package and getattr(prompt_package, "confidence_boost", 0):
            effective_confidence = min(1.0, effective_confidence + prompt_package.confidence_boost)

        # Route to human when there is no historical evidence and confidence is still low
        low_confidence_no_history = effective_confidence < self.LOW_CONFIDENCE_THRESHOLD and not root_cause.supporting_cases
        routing = "human" if (is_novel or priority >= 4 or context.compliance_flag or context.financial_exposure > 100000 or low_confidence_no_history) else "auto"

        # Use prompt_package guidance to validate borderline routing decisions
        if prompt_package and prompt_package.classifier_prompt:
            routing, priority = self._apply_prompt_guidance(
                routing, priority, effective_confidence, prompt_package
            )
            logger.info("[INFO] ClassifierAgent: applied prompt_package guidance.")

        # Derive responsible_team from vendor pattern analysis (dynamic, no hardcoding)
        responsible_team = self._derive_responsible_team(context, historical_cases or [])

        return Classification(
            category=cat,
            priority=priority,
            is_novel=is_novel,
            routing=routing,
            confidence=effective_confidence,
            responsible_team=responsible_team,
        )

    def _normalize_exception_type(self, exception_type):
        return exception_type.lower().replace(" ", "_")

    def _is_truly_novel(self, cat, root_cause):
        """Return True only when the type is unknown AND there are no supporting historical cases."""
        return cat not in self.KNOWN and not root_cause.supporting_cases

    def _analyze_vendor_pattern(self, vendor, historical_cases):
        """
        Dynamically analyse historical cases for a vendor.

        Returns a dict with:
          - dominant_type: most common exception type for this vendor (or None)
          - consistency_score: fraction of cases that match the dominant type (0.0-1.0)
          - total_cases: number of historical cases for this vendor
          - type_counts: {exception_type: count} breakdown

        Works for ANY vendor including new ones.
        Returns None/unknown safely for new vendors.
        """
        if not vendor or not historical_cases:
            return None

        vendor_cases = [c for c in historical_cases if c.get("vendor") == vendor]
        if not vendor_cases:
            # TODO_VENDOR_PATTERN: Vendor {vendor} has no historical cases yet.
            # Route to human until enough data accumulates.
            return None

        type_counts = {}
        for case in vendor_cases:
            exc_type = case.get("exception_type", "unknown")
            type_counts[exc_type] = type_counts.get(exc_type, 0) + 1

        dominant_type = max(type_counts, key=type_counts.get)
        consistency_score = type_counts[dominant_type] / len(vendor_cases)

        return {
            "dominant_type": dominant_type,
            "consistency_score": round(consistency_score, 3),
            "total_cases": len(vendor_cases),
            "type_counts": type_counts,
        }

    def _derive_responsible_team(self, context, historical_cases):
        """
        Derive the responsible team from historical data for this vendor/type combination.
        Falls back to the assigned team from context.
        """
        if not historical_cases:
            return context.assigned_team or ""

        vendor_cases = [
            c for c in historical_cases
            if c.get("vendor") == context.vendor
            and c.get("exception_type") == context.exception_type
        ]
        if not vendor_cases:
            vendor_cases = [c for c in historical_cases if c.get("vendor") == context.vendor]

        if vendor_cases:
            # Use the most frequently seen team for this vendor+type combination
            team_counts = {}
            for case in vendor_cases:
                team = case.get("assigned_team") or case.get("team", "")
                if team:
                    team_counts[team] = team_counts.get(team, 0) + 1
            if team_counts:
                return max(team_counts, key=team_counts.get)

        return context.assigned_team or ""

    def _priority(self, ctx, process_data: dict = None):
        p = 1
        if ctx.financial_exposure > 100000: p += 2
        elif ctx.financial_exposure > 50000: p += 1
        if ctx.severity_score is not None and ctx.severity_score > 0.8: p += 1
        if ctx.compliance_flag: p += 1

        # SLA — only for recent exceptions (within 30 days).
        # Celonis has historical data from 2024 — don't penalize old data
        # by treating them as always-overdue against datetime.now() in 2026+.
        try:
            if ctx.timestamp:
                ts = ctx.timestamp.replace("Z", "").replace("+00:00", "")
                triggered = datetime.fromisoformat(ts)
                now = datetime.now()
                age_days = (now - triggered).days

                if age_days <= 30:  # Only recent exceptions
                    deadline = triggered + timedelta(hours=ctx.sla_hours)
                    hrs_remaining = (deadline - now).total_seconds() / 3600
                    if hrs_remaining <= 0:
                        p += 2  # overdue
                    elif hrs_remaining <= 24:
                        p += 2  # critical
                    elif hrs_remaining <= 48:
                        p += 1  # warning

                    # Urgency factor: how much of the SLA has been consumed
                    # SLA consumption >= 80% triggers a priority boost.
                    # 80% is chosen as the inflection point where remaining buffer (20%)
                    # is typically insufficient to complete investigation + remediation.
                    # This mirrors industry-standard escalation triggers in AP workflows.
                    total_sla_hrs = ctx.sla_hours or 48
                    consumed_hrs = total_sla_hrs - hrs_remaining
                    sla_consumption = consumed_hrs / total_sla_hrs if total_sla_hrs else 0.0
                    if sla_consumption >= 0.8:
                        p += 1  # >=80% SLA consumed — boost priority
                        logger.info(
                            "[INFO] ClassifierAgent: SLA consumption %.0f%% — priority boosted for case %s",
                            sla_consumption * 100, ctx.case_id,
                        )
                else:
                    logger.info(
                        f"[INFO] SLA skipped: {age_days}d old (historical Celonis data)"
                    )
        except Exception as e:
            logger.warning(f"[WARN] SLA calc failed: {e}")

        # Historical resolution time urgency: if case has been open longer than
        # the historical average resolution time for this vendor/exception type.
        if process_data:
            hist_urgency = self._historical_urgency_boost(ctx, process_data)
            p += hist_urgency

        return max(1, min(5, p))

    def _apply_prompt_guidance(self, routing, priority, confidence, prompt_package):
        """
        Use classifier_prompt from prompt_package to refine routing/priority
        when confidence is in the borderline range (0.4 - 0.7).
        """
        if 0.4 <= confidence <= 0.7:
            prompt_lower = prompt_package.classifier_prompt.lower()
            if "escalate" in prompt_lower or "human" in prompt_lower:
                routing = "human"
            elif "auto" in prompt_lower and routing == "human":
                # Only override to auto when explicitly stated and confidence is mid-range
                if confidence >= 0.55:
                    routing = "auto"
            if "high priority" in prompt_lower or "critical" in prompt_lower:
                priority = min(5, priority + 1)
        return routing, priority

    def _historical_urgency_boost(self, ctx, process_data: dict) -> int:
        """
        Return +1 priority boost when the case has been open longer than
        the historical average resolution time for this exception type / vendor.
        """
        try:
            exc_stats = (process_data.get("exception_type_stats") or {}).get(
                ctx.exception_type, {}
            )
            hist_days = exc_stats.get("avg_resolution_days")
            if not hist_days or hist_days <= 0:
                return 0

            if ctx.timestamp:
                ts = ctx.timestamp.replace("Z", "").replace("+00:00", "")
                triggered = datetime.fromisoformat(ts)
                age_days = (datetime.now() - triggered).total_seconds() / 86400
                if age_days > hist_days:
                    logger.info(
                        "[INFO] ClassifierAgent: case open %.1fd exceeds historical avg %.1fd — priority +1",
                        age_days, hist_days,
                    )
                    return 1
        except Exception as exc:
            logger.warning("[WARN] ClassifierAgent: historical urgency calc failed: %s", exc)
        return 0