"""
MCP Tool implementations - Wraps integrations for agent use.
This file focuses on Teams webhook integration for now.
"""
from api.integrations.teams_webhook_client import TeamsWebhookClient
from config import settings
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TeamsTools:
    """Tool wrapper for Teams webhook notifications."""

    def __init__(self):
        """Initialize Teams webhook client."""
        self.client = TeamsWebhookClient()
        logger.info("✅ Teams MCP Tools initialized")

    def notify_procurement_team(
            self,
            case_id: str,
            issue: str,
            priority: int,
            recommendation: str,
            financial_exposure: float = 0,
            exception_uuid: str = "",
            erp_recommendation: dict = None,
    ) -> Dict[str, Any]:
        """
        Tool: Send notification to procurement team via Teams.

        Args:
            case_id: Exception case ID
            issue: Exception description
            priority: Priority level 1-5
            recommendation: Recommended action
            financial_exposure: Financial impact in dollars
            exception_uuid: Internal exception UUID
            erp_recommendation: Optional ERP action dict

        Returns:
            Status of notification
        """
        logger.info(f"[MCP Tool] notify_procurement_team: {case_id} (P{priority})")

        try:
            # Build Adaptive Card
            priority_color = {
                1: "good",  # Green
                2: "good",  # Green
                3: "warning",  # Orange
                4: "attention",  # Red
                5: "dark",  # Dark Red
            }.get(priority, "dark")

            # Priority emoji
            priority_emoji = {
                1: "🟢",
                2: "🟢",
                3: "🟡",
                4: "🔴",
                5: "🔴",
            }.get(priority, "🔴")

            # Core facts
            core_facts = [
                {"name": "📋 Case ID", "value": case_id},
                {"name": "⚠️ Issue", "value": issue},
                {"name": "💰 Financial Exposure", "value": f"${financial_exposure:,.2f}"},
                {"name": "✅ Recommended Action", "value": recommendation},
            ]

            # ERP section facts (appended when available)
            if erp_recommendation:
                erp_tx = erp_recommendation.get("transaction", "")
                erp_system = erp_recommendation.get("system", "SAP")
                erp_desc = erp_recommendation.get("description", "")
                erp_impact = erp_recommendation.get("estimated_impact", "")
                core_facts += [
                    {"name": "🏭 ERP Action", "value": f"{erp_system} Transaction {erp_tx}"},
                    {"name": "📝 ERP Steps", "value": erp_desc},
                    {"name": "💡 Estimated Impact", "value": erp_impact},
                    {"name": "⚡ ERP Status", "value": "Pending Approval"},
                ]

            # Action buttons
            dashboard_url = f"http://localhost:3000/exception/{exception_uuid or case_id}"
            actions = [
                {
                    "type": "Action.OpenUrl",
                    "title": "📊 Review in Dashboard",
                    "url": dashboard_url,
                    "style": "positive",
                },
            ]
            if erp_recommendation:
                erp_approve_url = f"http://localhost:3000/exception/{exception_uuid or case_id}"
                actions.append({
                    "type": "Action.OpenUrl",
                    "title": "🏭 Approve ERP Action",
                    "url": erp_approve_url,
                    "style": "positive",
                })

            card = {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {
                        "type": "Container",
                        "style": "emphasis",
                        "items": [
                            {
                                "type": "ColumnSet",
                                "columns": [
                                    {
                                        "width": "stretch",
                                        "items": [
                                            {
                                                "type": "TextBlock",
                                                "text": f"{priority_emoji} P2P Exception — Priority {priority}/5",
                                                "weight": "bolder",
                                                "size": "large",
                                                "color": priority_color,
                                            },
                                        ],
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "type": "Container",
                        "items": [
                            {
                                "type": "FactSet",
                                "facts": core_facts,
                            },
                        ],
                    },
                    {
                        "type": "Container",
                        "separator": True,
                        "items": [
                            {
                                "type": "ActionSet",
                                "actions": actions,
                            },
                        ],
                    },
                ],
            }

            # Send via webhook
            result = self.client.send_adaptive_card(card)

            logger.info(f"[MCP Result] {result}")
            return result

        except Exception as e:
            logger.error(f"[MCP Error] notify_procurement_team: {e}")
            return {"error": str(e), "case_id": case_id}

    def send_simple_alert(self, message: str) -> Dict[str, Any]:
        """
        Tool: Send simple text alert to Teams.

        Args:
            message: Text message to send

        Returns:
            Status
        """
        logger.info(f"[MCP Tool] send_simple_alert")
        try:
            result = self.client.send_simple_message(message)
            return result
        except Exception as e:
            logger.error(f"[MCP Error] send_simple_alert: {e}")
            return {"error": str(e)}