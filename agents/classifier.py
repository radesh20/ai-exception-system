from datetime import datetime, timedelta
import logging
from models import ExceptionContext, RootCauseAnalysis, Classification

logger = logging.getLogger(__name__)

class ClassifierAgent:
    KNOWN = {"payment_mismatch", "quantity_mismatch", "invoice_mismatch", "goods_receipt_mismatch", "tax_code_change"}
    LOW_CONFIDENCE_THRESHOLD = 0.6

    # Vendor short-code → expected exception type mapping
    VENDOR_TYPE_MAP = {
        "N14": "quantity_mismatch",
        "I9": "payment_mismatch",
    }

    def classify(self, context, root_cause, prompt_package=None):
        cat = self._normalize_exception_type(context.exception_type)
        is_novel = self._is_truly_novel(cat, root_cause)
        if is_novel:
            cat = "novel_exception"
        priority = self._priority(context)
        vendor_boost = self._get_vendor_boost(context, root_cause)
        effective_confidence = min(1.0, root_cause.confidence + vendor_boost)
        # Route to human when there is no historical evidence and confidence is still low
        low_confidence_no_history = effective_confidence < self.LOW_CONFIDENCE_THRESHOLD and not root_cause.supporting_cases
        routing = "human" if (is_novel or priority >= 4 or context.compliance_flag or context.financial_exposure > 100000 or low_confidence_no_history) else "auto"

        # Use prompt_package guidance to validate borderline routing decisions
        if prompt_package and prompt_package.classifier_prompt:
            routing, priority = self._apply_prompt_guidance(
                routing, priority, effective_confidence, prompt_package
            )
            logger.info("[INFO] ClassifierAgent: applied prompt_package guidance.")

        return Classification(category=cat, priority=priority, is_novel=is_novel, routing=routing, confidence=effective_confidence)

    def _normalize_exception_type(self, exception_type):
        return exception_type.lower().replace(" ", "_")

    def _is_truly_novel(self, cat, root_cause):
        """Return True only when the type is unknown AND there are no supporting historical cases."""
        return cat not in self.KNOWN and not root_cause.supporting_cases

    def _get_vendor_boost(self, context, root_cause):
        """Return a confidence boost when the vendor pattern matches the exception type."""
        expected_type = self.VENDOR_TYPE_MAP.get(context.vendor)
        if expected_type and self._normalize_exception_type(context.exception_type) == expected_type:
            return 0.2
        return 0.0

    def _priority(self, ctx):
        p = 1
        if ctx.financial_exposure > 100000: p += 2
        elif ctx.financial_exposure > 50000: p += 1
        if ctx.severity_score > 0.8: p += 1
        if ctx.compliance_flag: p += 1
        try:
            triggered = datetime.fromisoformat(ctx.timestamp.replace("Z", "+00:00"))
            hrs = (triggered + timedelta(hours=ctx.sla_hours) - datetime.now()).total_seconds() / 3600
            if hrs <= 24: p += 2
            elif hrs <= 48: p += 1
        except: pass
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