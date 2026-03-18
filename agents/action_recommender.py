class ActionRecommenderAgent:
    DEFAULTS = {
        "payment_mismatch": "three_way_match_recheck", "quantity_mismatch": "adjust_quantity",
        "invoice_mismatch": "request_invoice_correction", "goods_receipt_mismatch": "reverse_and_repost_gr",
        "tax_code_change": "update_tax_code", "novel_exception": "escalate_to_human",
    }

    def recommend(self, context, classification, policies):
        matching = [p for p in policies if p.get("category") == classification.category]
        if not matching:
            action = self.DEFAULTS.get(classification.category, "escalate_to_human")
            return action, {"exception_id": context.case_id}, f"No policy for {classification.category}. Default: {action}."

        best = max(matching, key=lambda p: p.get("success_rate", 0) * 0.6 + (1 / max(p.get("avg_resolution_time", 1), 1)) * 0.4)
        action = best.get("action_type", "escalate_to_human")
        params = {**best.get("action_params", {}), "exception_id": context.case_id, "category": classification.category,
                  "priority": classification.priority, "financial_exposure": context.financial_exposure}
        reasoning = f"Policy matched for {classification.category}. Action: {action}. Success: {best.get('success_rate', 0):.0%}. Samples: {best.get('sample_size', 0)}."
        return action, params, reasoning