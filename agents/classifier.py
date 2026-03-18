from datetime import datetime, timedelta
from models import ExceptionContext, RootCauseAnalysis, Classification

class ClassifierAgent:
    KNOWN = {"payment_mismatch", "quantity_mismatch", "invoice_mismatch", "goods_receipt_mismatch", "tax_code_change"}

    def classify(self, context, root_cause):
        cat = context.exception_type.lower().replace(" ", "_")
        if cat not in self.KNOWN: cat = "novel_exception"
        is_novel = root_cause.confidence < 0.6
        if is_novel: cat = "novel_exception"
        priority = self._priority(context)
        routing = "human" if (is_novel or priority >= 4 or context.compliance_flag or context.financial_exposure > 100000) else "auto"
        return Classification(category=cat, priority=priority, is_novel=is_novel, routing=routing, confidence=root_cause.confidence)

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