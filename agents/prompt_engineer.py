"""
Prompt Engineer Agent - Stage 0 of the pipeline.

Reads exception context and uses GPT-4o to generate custom prompts
for downstream agents (Root Cause, Classifier, Action Recommender).
Falls back to rule-based prompts when Azure OpenAI is disabled or
if the GPT-4o call fails.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import logging
import config.settings as settings

logger = logging.getLogger(__name__)


@dataclass
class PromptPackage:
    root_cause_prompt: str
    classifier_prompt: str
    action_prompt: str
    context_summary: str
    risk_flags: List[str]
    generated_by: str  # "gpt4o" or "rule_based"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self):
        return {
            "root_cause_prompt": self.root_cause_prompt,
            "classifier_prompt": self.classifier_prompt,
            "action_prompt": self.action_prompt,
            "context_summary": self.context_summary,
            "risk_flags": self.risk_flags,
            "generated_by": self.generated_by,
            "timestamp": self.timestamp,
        }


class PromptEngineerAgent:
    """
    Generates contextual prompts for downstream agents using GPT-4o.
    Falls back to rule-based prompts if Azure OpenAI is unavailable.
    """

    # ERP transaction mapping used for rule-based fallback
    ERP_MAP = {
        "quantity_mismatch": ("ME22N", "Adjust PO quantity to match goods receipt"),
        "payment_mismatch": ("F-53", "Recheck 3-way match and release payment block"),
        "invoice_mismatch": ("MIRO", "Correct and repost invoice against PO"),
        "goods_receipt_mismatch": ("MIGO", "Reverse and repost goods receipt"),
        "tax_code_change": ("FB60", "Update tax code on invoice"),
        "novel_exception": ("SM30", "Manual review and escalation required"),
    }

    def generate(self, context, historical_cases=None, process_context: str = "") -> PromptPackage:
        """
        Generate a PromptPackage for the given exception context.
        Tries GPT-4o first; falls back to rule-based on any failure.

        Args:
            context: ExceptionContext for the current exception.
            historical_cases: Optional list of historical case dicts used for
                              vendor pattern analysis. When provided, vendor
                              intelligence is included in the prompts.
            process_context: Optional process-aware context string produced by
                             ProcessAwarePromptBuilder.  When provided it is
                             included in both GPT-4o system prompt and the
                             rule-based fallback so downstream agents receive
                             process-aware instructions.
        """
        if settings.AZURE_OPENAI_ENABLED:
            try:
                return self._generate_with_gpt4o(context, historical_cases, process_context)
            except Exception as e:
                logger.error(f"[ERROR] PromptEngineerAgent GPT-4o failed: {e}. Falling back to rule-based.")

        return self._generate_rule_based(context, historical_cases, process_context)

    # ------------------------------------------------------------------
    # GPT-4o path
    # ------------------------------------------------------------------

    def _generate_with_gpt4o(self, context, historical_cases=None, process_context: str = "") -> PromptPackage:
        from langchain_openai import AzureChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            temperature=0,
        )

        vendor_pattern = self._analyze_vendor_history(context.vendor, historical_cases)

        system_prompt = (
            "You are a P2P (Procure-to-Pay) exception management expert. "
            "Your job is to generate precise instructions for three downstream AI agents "
            "that will analyze a financial exception. "
            "Return ONLY valid JSON with exactly these keys: "
            "root_cause_prompt, classifier_prompt, action_prompt, context_summary, risk_flags. "
            "risk_flags must be a JSON array of strings. "
            "Be concise and specific to the exception data provided.\n\n"
            "VENDOR HISTORY GUIDANCE:\n"
            "Use vendor history to determine confidence boost. "
            "Mixed vendor types -> conservative routing -> prefer human. "
            "Consistent vendor pattern -> can boost confidence by up to 0.2. "
            "Unknown vendor -> always route to human."
        )

        if process_context:
            system_prompt += f"\n\nPROCESS CONTEXT:\n{process_context}"

        user_prompt = (
            f"Exception context:\n"
            f"- case_id: {context.case_id}\n"
            f"- exception_type: {context.exception_type}\n"
            f"- vendor: {context.vendor}\n"
            f"- financial_exposure: ${context.financial_exposure:,.2f}\n"
            f"- deviation_point: {context.deviation_point}\n"
            f"- actual_path: {' -> '.join(context.actual_path)}\n"
            f"- happy_path: {' -> '.join(context.happy_path)}\n"
            f"- severity_score: {context.severity_score}\n"
            f"- compliance_flag: {context.compliance_flag}\n\n"
            f"Vendor history:\n{vendor_pattern}\n\n"
            "Generate focused instructions for:\n"
            "1. root_cause_prompt: How should the Root Cause Agent focus its analysis?\n"
            "2. classifier_prompt: What factors should guide priority and routing decisions?\n"
            "3. action_prompt: What specific actions/ERP transactions should be recommended?\n"
            "4. context_summary: One sentence human-readable summary.\n"
            "5. risk_flags: List of identified risk factors (strings).\n"
        )

        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        return self._parse_gpt4o_response(response.content, context, historical_cases)

    def _parse_gpt4o_response(self, raw: str, context, historical_cases=None) -> PromptPackage:
        import json, re

        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("[INFO] PromptEngineerAgent: GPT-4o response not valid JSON, using rule-based.")
            return self._generate_rule_based(context, historical_cases)

        risk_flags = data.get("risk_flags", [])
        if isinstance(risk_flags, str):
            risk_flags = [risk_flags]

        return PromptPackage(
            root_cause_prompt=data.get("root_cause_prompt", ""),
            classifier_prompt=data.get("classifier_prompt", ""),
            action_prompt=data.get("action_prompt", ""),
            context_summary=data.get("context_summary", ""),
            risk_flags=risk_flags,
            generated_by="gpt4o",
        )

    # ------------------------------------------------------------------
    # Rule-based fallback
    # ------------------------------------------------------------------

    def _generate_rule_based(self, context, historical_cases=None, process_context: str = "") -> PromptPackage:
        exc_type = context.exception_type.lower().replace(" ", "_")
        vendor = context.vendor or "unknown"
        exposure = context.financial_exposure
        deviation = context.deviation_point

        erp_tx, erp_desc = self.ERP_MAP.get(exc_type, ("SM30", "Manual review required"))

        vendor_pattern = self._analyze_vendor_history(vendor, historical_cases)

        process_note = f" Process context: {process_context}" if process_context else ""

        root_cause_prompt = (
            f"Analyze {exc_type} for vendor {vendor}. "
            f"Focus on the deviation at '{deviation}'. "
            f"Check historical cases for the same vendor and exception type. "
            f"Financial exposure is ${exposure:,.2f} - flag if unusually high. "
            f"Vendor context: {vendor_pattern}"
            f"{process_note}"
        )

        classifier_prompt = (
            f"Vendor {vendor} has a {exc_type} exception with ${exposure:,.2f} exposure. "
            f"Deviation occurred at '{deviation}'. "
            f"Adjust priority based on exposure level and vendor compliance history. "
            f"Route to human if confidence is below 0.6 or exposure exceeds $50,000. "
            f"Vendor pattern: {vendor_pattern}"
            f"{process_note}"
        )

        action_prompt = (
            f"For {exc_type} exceptions, consider SAP transaction {erp_tx} ({erp_desc}). "
            f"Vendor {vendor} exposure is ${exposure:,.2f}. "
            f"If unresolved within 48 hours escalate to the assigned team manager."
            f"{process_note}"
        )

        context_summary = (
            f"{exc_type.replace('_', ' ').title()} for vendor {vendor} "
            f"with ${exposure:,.2f} financial exposure deviating at '{deviation}'."
        )

        risk_flags = self._build_risk_flags(context)

        return PromptPackage(
            root_cause_prompt=root_cause_prompt,
            classifier_prompt=classifier_prompt,
            action_prompt=action_prompt,
            context_summary=context_summary,
            risk_flags=risk_flags,
            generated_by="rule_based",
        )

    def _analyze_vendor_history(self, vendor: str, historical_cases) -> str:
        """
        Analyse historical cases for a vendor and return a human-readable summary
        suitable for inclusion in GPT-4o prompts or rule-based classifier prompts.

        Args:
            vendor: Vendor code (e.g. "I9", "N14", "X99").
            historical_cases: List of historical case dicts (may be None or empty).

        Returns:
            Human-readable string describing the vendor's exception pattern.
            For unknown vendors returns a safe "no history" message.
        """
        if not vendor or not historical_cases:
            return (
                f"Vendor {vendor or 'unknown'} has no historical cases. "
                "New/rare vendor — recommend human review until pattern emerges."
            )

        vendor_cases = [c for c in historical_cases if c.get("vendor") == vendor]
        if not vendor_cases:
            # TODO_VENDOR_PATTERN: Vendor has no historical cases yet — route to human.
            return (
                f"Vendor {vendor} has no historical cases. "
                "New/rare vendor — recommend human review until pattern emerges."
            )

        # Count exception types
        type_counts: dict = {}
        type_success: dict = {}
        type_total: dict = {}
        for case in vendor_cases:
            exc_type = case.get("exception_type", "unknown")
            type_counts[exc_type] = type_counts.get(exc_type, 0) + 1
            # Track resolution success when available
            resolved = case.get("resolved", case.get("status") in ("completed", "approved"))
            type_total[exc_type] = type_total.get(exc_type, 0) + 1
            if resolved:
                type_success[exc_type] = type_success.get(exc_type, 0) + 1

        total = len(vendor_cases)
        dominant_type = max(type_counts, key=type_counts.get)
        dominant_count = type_counts[dominant_type]
        dominant_pct = dominant_count / total * 100
        is_mixed = dominant_pct < 80  # < 80% dominant = mixed

        lines = [f"Vendor {vendor} pattern ({total} historical cases):"]
        for exc_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            pct = count / total * 100
            success_rate = (
                type_success.get(exc_type, 0) / type_total[exc_type] * 100
                if type_total.get(exc_type, 0) > 0
                else 0
            )
            lines.append(
                f"  - {exc_type}: {count} cases ({pct:.0f}%) | success: {success_rate:.0f}%"
            )

        lines.append(f"Most common: {dominant_type} ({dominant_pct:.0f}%)")
        variance = "HIGH" if dominant_pct >= 80 else "MEDIUM" if dominant_pct >= 60 else "LOW"
        lines.append(f"Variance: {variance} — {'single type detected' if not is_mixed else 'mixed types detected'}")
        if is_mixed:
            lines.append(f"Note: Do not assume single exception type for this vendor")

        return "\n".join(lines)

    def _build_risk_flags(self, context) -> List[str]:
        flags = []
        if context.financial_exposure > 100000:
            flags.append(f"High financial exposure: ${context.financial_exposure:,.2f}")
        elif context.financial_exposure > 50000:
            flags.append(f"Elevated financial exposure: ${context.financial_exposure:,.2f}")
        if context.compliance_flag:
            flags.append("Compliance flag raised")
        if context.deviation_point and context.deviation_point.lower() in ("payment open", "payment blocked"):
            flags.append(f"Payment deviation: {context.deviation_point}")
        if context.severity_score and context.severity_score > 0.8:
            flags.append(f"High severity score: {context.severity_score:.2f}")
        if not flags:
            flags.append("Standard risk level")
        return flags
