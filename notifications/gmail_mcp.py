import logging
import config.settings as settings
logger = logging.getLogger(__name__)

class GmailMCPNotifier:
    def __init__(self):
        self.to_addrs = [a.strip() for a in settings.GMAIL_NOTIFY_TO.split(",") if a.strip()]
        self._tools = None

    async def _get_tools(self):
        if self._tools is not None: return self._tools
        if not self.to_addrs: return []
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
            client = MultiServerMCPClient({"gmail":{"command":"npx","args":["-y","@gongrzhe/server-gmail-autoauth-mcp"],"transport":"stdio"}})
            self._tools = await client.get_tools()
            return self._tools
        except Exception as e:
            logger.error(f"Gmail MCP failed: {e}")
            return []

    async def send(self, exception_id, message, priority, category, action_url=""):
        tools = await self._get_tools()
        if not tools: return False
        send_tool = next((t for t in tools if "send" in t.name.lower()), None)
        if not send_tool: return False
        emoji = {1:"🟢",2:"🟡",3:"🟠",4:"🔴",5:"🚨"}.get(priority,"⚪")
        subject = f"{emoji} [P{priority}] P2P Exception: {category} — {exception_id[:12]}"
        body = f"P2P Exception Alert — Priority {priority}/5\n{'='*50}\n\n{message}\n"
        if action_url: body += f"\nReview: {action_url}"
        try:
            await send_tool.ainvoke({"to":", ".join(self.to_addrs),"subject":subject,"body":body})
            return True
        except Exception as e:
            logger.error(f"Gmail failed: {e}")
            return False

    async def send_simple(self, message):
        tools = await self._get_tools()
        if not tools: return False
        send_tool = next((t for t in tools if "send" in t.name.lower()), None)
        if not send_tool: return False
        try:
            await send_tool.ainvoke({"to":", ".join(self.to_addrs),"subject":"P2P Update","body":message})
            return True
        except: return False