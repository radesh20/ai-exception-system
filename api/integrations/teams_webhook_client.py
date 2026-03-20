"""
Teams Webhook Client for MCP Integration
Sends Adaptive Cards to Teams via webhook URL
"""
import requests
import logging
from typing import Dict, Any
from config import settings

logger = logging.getLogger(__name__)


class TeamsWebhookClient:
    """Send messages to Teams via webhook."""

    def __init__(self, webhook_url: str = ""):
        """Initialize with webhook URL."""
        self.webhook_url = webhook_url or settings.TEAMS_WEBHOOK_URL
        if not self.webhook_url:
            logger.warning("[WARN] Teams webhook URL not configured")

    def send_to_team(self, team_name: str, card: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send Adaptive Card to a named Teams channel.

        Looks up the webhook URL from TEAMS_CHANNEL_MAP using team_name.
        Falls back to DEFAULT channel if the team is not configured.
        Logs a TODO_TEAMS_CHANNEL warning when no URL is found.

        Args:
            team_name: Channel key from TEAMS_CHANNEL_MAP (e.g. "AP_Team_AC33").
            card: Adaptive Card JSON object.

        Returns:
            Success/failure response.
        """
        channel_map = getattr(settings, "TEAMS_CHANNEL_MAP", {})
        webhook_url = channel_map.get(team_name, "")

        if not webhook_url:
            # Fallback to DEFAULT channel
            webhook_url = channel_map.get("DEFAULT", self.webhook_url)

        if not webhook_url:
            env_key = f"TEAMS_WEBHOOK_{team_name.upper()}"
            logger.warning(
                f"[WARN] No webhook configured for channel '{team_name}'. "
                f"TODO_TEAMS_CHANNEL: Add {env_key} to .env file"
            )
            return {"error": f"No webhook configured for channel '{team_name}'"}

        return self.send_adaptive_card(card, webhook_url=webhook_url)

    def send_adaptive_card(self, card: Dict[str, Any], webhook_url: str = "") -> Dict[str, Any]:
        """
        Send Adaptive Card to Teams channel.

        Args:
            card: Adaptive Card JSON object
            webhook_url: Optional override URL; uses instance default when empty.

        Returns:
            Success/failure response
        """
        url = webhook_url or self.webhook_url
        if not url:
            return {"error": "Teams webhook URL not configured"}

        try:
            logger.info("[INFO] Sending Teams card via webhook...")

            payload = {"type": "message", "attachments": [
                {"contentType": "application/vnd.microsoft.card.adaptive", "contentUrl": None, "content": card}]}

            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            response.raise_for_status()
            logger.info("[OK] Teams card sent successfully")
            return {"status": "sent", "message": "Card delivered to Teams"}

        except requests.RequestException as e:
            logger.error(f"[ERROR] Failed to send Teams card: {e}")
            return {"error": f"Failed to send: {e}"}

    def send_simple_message(self, text: str) -> Dict[str, Any]:
        """Send simple text message to Teams."""
        if not self.webhook_url:
            return {"error": "Teams webhook URL not configured"}

        try:
            payload = {"text": text}
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("[OK] Teams message sent")
            return {"status": "sent"}

        except requests.RequestException as e:
            logger.error(f"[ERROR] Failed to send Teams message: {e}")
            return {"error": str(e)}