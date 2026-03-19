"""
MCP Client for calling MCP tools from agents.

Usage:
    from mcp_client import MCPClient
    client = MCPClient()
    result = client.notify_teams(case_id="PO-2024-0001", ...)
"""
import requests
from typing import Dict, Any
import logging
from config import settings

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for calling MCP tools from agents."""

    def __init__(self, base_url: str = ""):
        """Initialize with API base URL."""
        base = base_url or f"http://localhost:{settings.API_PORT}"
        self.mcp_url = f"{base}/api/mcp"
        logger.info(f" MCPClient initialized: {self.mcp_url}")

    def invoke(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Invoke a tool on the MCP server.

        Args:
            tool_name: Name of tool (e.g., "notify_procurement_team")
            **kwargs: Tool arguments

        Returns:
            Tool result or error dict
        """
        url = f"{self.mcp_url}/invoke"
        payload = {
            "tool": tool_name,
            "arguments": kwargs,
        }

        try:
            logger.debug(f"📤 [MCPClient] Invoking: {tool_name}")
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            if result.get("status") == "success":
                logger.info(f"✅ [MCPClient] {tool_name} succeeded")
                return result.get("result", {})
            else:
                error_msg = result.get("error", "Unknown error")
                logger.warning(f"⚠️ [MCPClient] {tool_name} failed: {error_msg}")
                return {"error": error_msg}

        except requests.RequestException as e:
            logger.error(f"❌ [MCPClient] Request failed: {e}")
            return {"error": str(e)}

    # Convenience methods

    def notify_teams(
            self,
            case_id: str,
            issue: str,
            priority: int,
            recommendation: str,
            financial_exposure: float = 0,
            exception_uuid: str = "",
            erp_recommendation: dict = None,
    ) -> Dict[str, Any]:
        """Send Teams notification."""
        kwargs = dict(
            case_id=case_id,
            issue=issue,
            priority=priority,
            recommendation=recommendation,
            financial_exposure=financial_exposure,
            exception_uuid=exception_uuid,
        )
        if erp_recommendation:
            kwargs["erp_recommendation"] = erp_recommendation
        return self.invoke("notify_procurement_team", **kwargs)

    def send_teams_alert(self, message: str) -> Dict[str, Any]:
        """Send simple Teams alert."""
        return self.invoke("send_simple_alert", message=message)