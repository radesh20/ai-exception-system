"""
Process Agent Recommender — sends full process analyzer output to GPT-4o
and returns a structured list of recommended process agents.
"""
import json
import logging
from datetime import datetime
from typing import List, Optional

import config.settings as settings

logger = logging.getLogger(__name__)


class ProcessAgentRecommender:
    """
    Analyses the full P2P process data and uses GPT-4o to recommend
    5-6 high-level process agents.  Falls back to rule-based
    recommendations when Azure OpenAI is unavailable.
    """

    def recommend(self, process_data: dict) -> List[dict]:
        """
        Args:
            process_data: Output from ProcessAnalyzer.fetch_and_analyze().

        Returns:
            List of dicts, each with:
              agent_name, function, data_justification, process_stage
        """
        if settings.AZURE_OPENAI_ENABLED:
            try:
                return self._recommend_with_gpt4o(process_data)
            except Exception as exc:
                logger.error(
                    "[ERROR] ProcessAgentRecommender GPT-4o failed: %s. Using rule-based.", exc
                )
        return self._recommend_rule_based(process_data)

    # ─────────────────────────────────────────────────────────
    # GPT-4o PATH
    # ─────────────────────────────────────────────────────────

    def _recommend_with_gpt4o(self, process_data: dict) -> List[dict]:
        from langchain_openai import AzureChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            temperature=0,
        )

        system_prompt = (
            "You are a P2P process improvement expert. "
            "Analyse the process analytics data provided and recommend exactly 5 to 6 "
            "AI process agents that would most improve the end-to-end P2P cycle. "
            "Base your recommendations purely on the data — bottlenecks, handoff delays, "
            "failure points, and recurring exception patterns. "
            "Return ONLY valid JSON as an array of objects. "
            "Each object must have exactly these keys: "
            "agent_name (string), function (string), data_justification (string), "
            "process_stage (string)."
        )

        # Summarise process data to keep token count reasonable
        summary = {
            "case_count": process_data.get("case_count", 0),
            "process_health": process_data.get("process_health", {}),
            "activity_stats": process_data.get("activity_stats", {}),
            "exception_type_stats": process_data.get("exception_type_stats", {}),
            "top_vendor_stats": dict(
                list((process_data.get("vendor_stats") or {}).items())[:5]
            ),
        }

        user_prompt = (
            "P2P process analytics summary:\n"
            + json.dumps(summary, indent=2, default=str)
            + "\n\nRecommend 5-6 AI process agents based on this data."
        )

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        return self._parse_response(response.content)

    def _parse_response(self, raw: str) -> List[dict]:
        import re
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        try:
            data = json.loads(cleaned)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            logger.warning("[WARN] ProcessAgentRecommender: invalid JSON from GPT-4o, using rule-based.")
        return self._recommend_rule_based({})

    # ─────────────────────────────────────────────────────────
    # RULE-BASED FALLBACK
    # ─────────────────────────────────────────────────────────

    def _recommend_rule_based(self, process_data: dict) -> List[dict]:
        health = process_data.get("process_health") or {}
        delay_stages = [s.get("stage") for s in (health.get("delay_causing_stages") or [])]

        recommendations = [
            {
                "agent_name": "InvoiceMatchingAgent",
                "function": (
                    "Automates 3-way matching of PO, GR, and invoice amounts. "
                    "Flags mismatches and initiates correction workflows."
                ),
                "data_justification": (
                    "Invoice-related exceptions account for the highest case volume. "
                    "Automating matching reduces manual AP effort."
                ),
                "process_stage": "Invoice Processing",
            },
            {
                "agent_name": "PaymentReleaseAgent",
                "function": (
                    "Monitors blocked payments and automatically initiates release "
                    "when 3-way match is confirmed and SLA is approaching."
                ),
                "data_justification": (
                    "Payment Open stage shows highest bottleneck frequency. "
                    "Automated release reduces SLA breaches."
                ),
                "process_stage": "Payment Processing",
            },
            {
                "agent_name": "VendorComplianceAgent",
                "function": (
                    "Tracks vendor-level compliance with P2P process requirements. "
                    "Flags high-risk vendors and recommends corrective actions."
                ),
                "data_justification": (
                    "Recurring exceptions cluster around specific vendors. "
                    "Proactive vendor monitoring reduces recurrence."
                ),
                "process_stage": "Vendor Management",
            },
            {
                "agent_name": "SLAMonitorAgent",
                "function": (
                    "Continuously monitors open cases against SLA deadlines and "
                    "triggers escalation notifications when thresholds are crossed."
                ),
                "data_justification": (
                    f"SLA compliance rate is {health.get('sla_compliance_rate', 0):.0%}. "
                    "Proactive SLA monitoring can improve on-time resolution."
                ),
                "process_stage": "Escalation Management",
            },
            {
                "agent_name": "GoodsReceiptReconcilerAgent",
                "function": (
                    "Reconciles goods receipt postings against PO quantities and "
                    "auto-corrects discrepancies within tolerance thresholds."
                ),
                "data_justification": (
                    "Goods receipt mismatches are a recurring exception type "
                    "that can be resolved algorithmically within defined tolerances."
                ),
                "process_stage": "Goods Receipt",
            },
            {
                "agent_name": "ProcessHealthReporterAgent",
                "function": (
                    "Aggregates P2P process metrics, generates daily health reports, "
                    "and surfaces trends in cycle time and exception rates."
                ),
                "data_justification": (
                    f"Average end-to-end cycle is {health.get('avg_end_to_end_days', 0):.1f} days. "
                    "Continuous health reporting enables proactive management."
                ),
                "process_stage": "Process Intelligence",
            },
        ]

        # Adjust if specific delay stages are identified
        if delay_stages:
            recommendations[0]["data_justification"] += (
                f" Key delay stages identified: {', '.join(delay_stages[:3])}."
            )

        return recommendations
