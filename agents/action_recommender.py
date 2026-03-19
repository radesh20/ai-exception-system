import logging

logger = logging.getLogger(__name__)

class ActionRecommenderAgent:
    DEFAULTS = {
        "payment_mismatch": "three_way_match_recheck", "quantity_mismatch": "adjust_quantity",
        "invoice_mismatch": "request_invoice_correction", "goods_receipt_mismatch": "reverse_and_repost_gr",
        "tax_code_change": "update_tax_code", "novel_exception": "escalate_to_human",
    }

    # ERP transaction lookup per exception category
    ERP_TRANSACTIONS = {
        "payment_mismatch": {
            "transaction": "F-53",
            "description": "Open F-53 in SAP, locate the payment block, verify 3-way match (PO/GR/Invoice), and release the block once amounts reconcile.",
            "system": "SAP",
            "requires_approval": True,
        },
        "quantity_mismatch": {
            "transaction": "ME22N",
            "description": "Open ME22N in SAP, navigate to the relevant PO line item, adjust the ordered quantity to match the goods receipt quantity.",
            "system": "SAP",
            "requires_approval": True,
        },
        "invoice_mismatch": {
            "transaction": "MIRO",
            "description": "Open MIRO in SAP, cancel the existing invoice posting, correct the invoice amount, and repost against the PO.",
            "system": "SAP",
            "requires_approval": False,
        },
        "goods_receipt_mismatch": {
            "transaction": "MIGO",
            "description": "Open MIGO in SAP, reverse the incorrect goods receipt, and repost with the correct quantity and delivery note.",
            "system": "SAP",
            "requires_approval": False,
        },
        "tax_code_change": {
            "transaction": "FB60",
            "description": "Open FB60 in SAP, update the tax code on the invoice line item to match the PO tax configuration.",
            "system": "SAP",
            "requires_approval": False,
        },
        "novel_exception": {
            "transaction": "SM30",
            "description": "Log the exception in SM30 for manual review. Escalate to the AP Team manager for manual investigation.",
            "system": "SAP",
            "requires_approval": True,
        },
    }

    def recommend(self, context, classification, policies, prompt_package=None):
        matching = [p for p in policies if p.get("category") == classification.category]
        if not matching:
            action = self.DEFAULTS.get(classification.category, "escalate_to_human")
            reasoning = f"No policy for {classification.category}. Default: {action}."
            erp = self._build_erp_recommendation(classification.category, context, prompt_package)
            return action, {"exception_id": context.case_id}, reasoning, erp

        best = max(matching, key=lambda p: p.get("success_rate", 0) * 0.6 + (1 / max(p.get("avg_resolution_time", 1), 1)) * 0.4)
        action = best.get("action_type", "escalate_to_human")
        params = {**best.get("action_params", {}), "exception_id": context.case_id, "category": classification.category,
                  "priority": classification.priority, "financial_exposure": context.financial_exposure}
        reasoning = f"Policy matched for {classification.category}. Action: {action}. Success: {best.get('success_rate', 0):.0%}. Samples: {best.get('sample_size', 0)}."

        if prompt_package and prompt_package.action_prompt:
            reasoning = f"{reasoning} [AI guidance: {prompt_package.action_prompt}]"
            logger.info("[INFO] ActionRecommenderAgent: applied prompt_package guidance.")

        erp = self._build_erp_recommendation(classification.category, context, prompt_package)
        return action, params, reasoning, erp

    def _build_erp_recommendation(self, category, context, prompt_package):
        """Build an ERP recommendation dict for the given exception category."""
        erp_info = self.ERP_TRANSACTIONS.get(category, self.ERP_TRANSACTIONS["novel_exception"])
        estimated_impact = f"${context.financial_exposure:,.2f}"
        return {
            "transaction": erp_info["transaction"],
            "description": erp_info["description"],
            "system": erp_info["system"],
            "requires_approval": erp_info["requires_approval"],
            "estimated_impact": estimated_impact,
        }