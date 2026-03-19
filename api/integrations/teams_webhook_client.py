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
            logger.warning("⚠️  Teams webhook URL not configured")

    def send_adaptive_card(self, card: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send Adaptive Card to Teams channel.

        Args:
            card: Adaptive Card JSON object

        Returns:
            Success/failure response
        """
        if not self.webhook_url:
            return {"error": "Teams webhook URL not configured"}

        try:
            logger.info("��� Sending Teams card via webhook...")

            payload = {"type": "message", "attachments": [
                {"contentType": "application/vnd.microsoft.card.adaptive", "contentUrl": None, "content": card}]}

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            response.raise_for_status()
            logger.info("✅ Teams card sent successfully")
            return {"status": "sent", "message": "Card delivered to Teams"}

        except requests.RequestException as e:
            logger.error(f"❌ Failed to send Teams card: {e}")
            return {"error": f"Failed to send: {e}"}

    def send_simple_message(self, text: str) -> Dict[str, Any]:
        """Send simple text message to Teams."""
        if not self.webhook_url:
            return {"error": "Teams webhook URL not configured"}

        try:
            payload = {"text": text}
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("✅ Teams message sent")
            return {"status": "sent"}

        except requests.RequestException as e:
            logger.error(f"❌ Failed to send Teams message: {e}")
            return {"error": str(e)}