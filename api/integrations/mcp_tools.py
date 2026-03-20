"""
MCP Tool implementations - Wraps integrations for agent use.
This file focuses on Teams webhook integration for now.
"""
from api.integrations.teams_webhook_client import TeamsWebhookClient
from config import settings
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class TeamsTools:
    """Tool wrapper for Teams webhook notifications."""

    def __init__(self):
        """Initialize Teams webhook client."""
        self.client = TeamsWebhookClient()
        logger.info("[OK] Teams MCP Tools initialized")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_target_channels(
        assigned_team: str,
        responsible_team: str,
        priority: int,
    ) -> List[str]:
        """
        Determine which Teams channels should receive a notification.

        Rules:
        - Always notify the assigned team's channel.
        - Also notify the responsible team if it differs from assigned.
        - Escalate to manager channel when priority >= threshold.
        - Fall back to DEFAULT if no team is resolved.
        """
        channels: set = set()

        if assigned_team:
            channels.add(assigned_team)

        if responsible_team and responsible_team != assigned_team:
            channels.add(responsible_team)

        escalation_threshold = getattr(
            settings, "TEAMS_MANAGER_ESCALATION_PRIORITY", 4
        )
        if priority >= escalation_threshold:
            channels.add("manager")

        if not channels:
            channels.add("DEFAULT")

        return list(channels)

    def notify_procurement_team(
            self,
            case_id: str,
            issue: str,
            priority: int,
            recommendation: str,
            financial_exposure: float = 0,
            exception_uuid: str = "",
            erp_recommendation: dict = None,
            assigned_team: str = "",
            responsible_team: str = "",
    ) -> Dict[str, Any]:
        """
        Tool: Send notification to procurement team(s) via Teams.

        Supports multi-channel routing:
        - Notifies assigned_team channel.
        - Also notifies responsible_team channel when different.
        - Escalates to manager channel for high-priority exceptions.

        Args:
            case_id: Exception case ID
            issue: Exception description
            priority: Priority level 1-5
            recommendation: Recommended action
            financial_exposure: Financial impact in dollars
            exception_uuid: Internal exception UUID
            erp_recommendation: Optional ERP action dict
            assigned_team: Team channel that owns this exception
            responsible_team: Additional responsible team channel

        Returns:
            Status of notification (per channel)
        """
        logger.info(f"[MCP Tool] notify_procurement_team: {case_id} (P{priority})")

        try:
            # Build Adaptive Card
            priority_color = {
                1: "good",
                2: "good",
                3: "warning",
                4: "attention",
                5: "dark",
            }.get(priority, "dark")

            priority_label = {
                1: "P1",
                2: "P2",
                3: "P3",
                4: "P4",
                5: "P5",
            }.get(priority, str(priority))

            # Core facts
            core_facts = [
                {"name": "Case ID", "value": case_id},
                {"name": "Issue", "value": issue},
                {"name": "Financial Exposure", "value": f"${financial_exposure:,.2f}"},
                {"name": "Recommended Action", "value": recommendation},
            ]
            if assigned_team:
                core_facts.append({"name": "Assigned Team", "value": assigned_team})
            if responsible_team and responsible_team != assigned_team:
                core_facts.append({"name": "Responsible Team", "value": responsible_team})

            # ERP section facts (appended when available)
            if erp_recommendation:
                erp_tx = erp_recommendation.get("transaction", "")
                erp_system = erp_recommendation.get("system", "SAP")
                erp_desc = erp_recommendation.get("description", "")
                erp_impact = erp_recommendation.get("estimated_impact", "")
                core_facts += [
                    {"name": "ERP Action", "value": f"{erp_system} Transaction {erp_tx}"},
                    {"name": "ERP Steps", "value": erp_desc},
                    {"name": "Estimated Impact", "value": erp_impact},
                    {"name": "ERP Status", "value": "Pending Approval"},
                ]

            # Action buttons
            dashboard_url = f"http://localhost:3000/exception/{exception_uuid or case_id}"
            actions = [
                {
                    "type": "Action.OpenUrl",
                    "title": "Review in Dashboard",
                    "url": dashboard_url,
                    "style": "positive",
                },
            ]
            if erp_recommendation:
                erp_approve_url = f"http://localhost:3000/exception/{exception_uuid or case_id}/approve-erp"
                actions.append({
                    "type": "Action.OpenUrl",
                    "title": "Approve ERP Action",
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
                                                "text": f"P2P Exception — Priority {priority_label}/5",
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

            # Determine target channels and send to each
            target_channels = self._get_target_channels(
                assigned_team, responsible_team, priority
            )
            results = {}
            for channel in target_channels:
                channel_map = getattr(settings, "TEAMS_CHANNEL_MAP", {})
                webhook_url = channel_map.get(channel, channel_map.get("DEFAULT", ""))
                if webhook_url:
                    result = self.client.send_adaptive_card(card, webhook_url=webhook_url)
                    results[channel] = result
                else:
                    # TODO_TEAMS_CHANNEL: Channel has no webhook configured.
                    # Add TEAMS_WEBHOOK_{CHANNEL} to .env file.
                    env_key = f"TEAMS_WEBHOOK_{channel.upper()}"
                    logger.warning(
                        f"[WARN] No webhook for channel '{channel}'. "
                        f"TODO_TEAMS_CHANNEL: Configure {env_key} in .env"
                    )
                    results[channel] = {"error": f"No webhook configured for '{channel}'"}

            logger.info(f"[INFO] Teams notification sent to {len(results)} channel(s): {list(results.keys())}")
            return {"channels": results, "case_id": case_id}

        except Exception as e:
            logger.error(f"[ERROR] notify_procurement_team: {e}")
            return {"error": str(e), "case_id": case_id}

    def send_simple_alert(self, message: str) -> Dict[str, Any]:
        """
        Tool: Send simple text alert to Teams.

        Args:
            message: Text message to send

        Returns:
            Status
        """
        logger.info("[MCP Tool] send_simple_alert")
        try:
            result = self.client.send_simple_message(message)
            return result
        except Exception as e:
            logger.error(f"[ERROR] send_simple_alert: {e}")
            return {"error": str(e)}