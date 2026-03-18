from datetime import datetime
import config.settings as settings
from models import DecisionType

class LearningEngine:
    def __init__(self, store):
        self.store = store

    def record_feedback(self, decision):
        exc = self.store.get_exception(decision.exception_id)
        if not exc: return {"error": "Exception not found"}
        cat = exc.classification.category if exc.classification else "unknown"
        was_approved = decision.decision_type == DecisionType.APPROVED
        if settings.LEARNING_ENABLED:
            self.store.update_policy_stats(cat, decision.original_recommendation, was_approved)
            self.store.save_historical_case({
                "case_id": exc.id, "exception_type": exc.context.exception_type if exc.context else "",
                "actual_path": exc.context.actual_path if exc.context else [],
                "deviation_point": exc.context.deviation_point if exc.context else "",
                "financial_exposure": exc.context.financial_exposure if exc.context else 0,
                "recommended_action": decision.original_recommendation, "final_action": decision.final_action,
                "was_approved": was_approved, "analyst": decision.analyst_name, "timestamp": datetime.now().isoformat(),
            })
        return {"category": cat, "was_approved": was_approved, "learning_updated": settings.LEARNING_ENABLED}

    def get_insights(self):
        decisions = self.store.list_decisions(limit=1000)
        total = len(decisions)
        approved = sum(1 for d in decisions if d.decision_type == DecisionType.APPROVED)
        by_cat = {}
        for d in decisions:
            exc = self.store.get_exception(d.exception_id)
            if not exc or not exc.classification: continue
            cat = exc.classification.category
            if cat not in by_cat: by_cat[cat] = {"approved": 0, "rejected": 0, "total": 0}
            by_cat[cat]["total"] += 1
            if d.decision_type == DecisionType.APPROVED: by_cat[cat]["approved"] += 1
            elif d.decision_type == DecisionType.REJECTED: by_cat[cat]["rejected"] += 1
        needs_attention = []
        for cat, s in by_cat.items():
            if s["total"] >= settings.LEARNING_MIN_SAMPLES:
                rate = s["approved"] / s["total"]
                if rate < settings.LEARNING_CONFIDENCE_THRESHOLD:
                    needs_attention.append({"category": cat, "approval_rate": round(rate, 3), "sample_size": s["total"]})
        return {"total_decisions": total, "overall_approval_rate": round(approved / max(total, 1), 3),
                "by_category": by_cat, "policies_count": len(self.store.get_policies()),
                "needs_attention": needs_attention, "learning_enabled": settings.LEARNING_ENABLED}