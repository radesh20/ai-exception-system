import logging
import config.settings as settings
logger = logging.getLogger(__name__)

class SlackMCPNotifier:
    def __init__(self):
        self.channel = settings.SLACK_CHANNEL
        self._tools = None

    async def _get_tools(self):
        if self._tools is not None: return self._tools
        if not settings.SLACK_BOT_TOKEN: return []
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
            client = MultiServerMCPClient({"slack":{"command":"npx","args":["-y","@modelcontextprotocol/server-slack"],
                "transport":"stdio","env":{"SLACK_BOT_TOKEN":settings.SLACK_BOT_TOKEN}}})
            self._tools = await client.get_tools()
            return self._tools
        except Exception as e:
            logger.error(f"Slack MCP failed: {e}")
            return []

    async def send(self, exception_id, message, priority, category, action_url=""):
        tools = await self._get_tools()
        if not tools: return False
        post = next((t for t in tools if "post" in t.name.lower() or "send" in t.name.lower()), None)
        if not post: return False
        emoji = {1:"🟢",2:"🟡",3:"🟠",4:"🔴",5:"🚨"}.get(priority,"⚪")
        text = f"{emoji} *P2P Exception — P{priority}/5*\n*ID:* `{exception_id[:16]}`\n*Category:* {category}\n───\n{message[:1500]}\n───\n"
        if action_url: text += f"<{action_url}|🔗 Review & Decide>"
        try:
            await post.ainvoke({"channel": self.channel, "text": text})
            return True
        except Exception as e:
            logger.error(f"Slack send failed: {e}")
            return False

    async def send_simple(self, message):
        tools = await self._get_tools()
        if not tools: return False
        post = next((t for t in tools if "post" in t.name.lower() or "send" in t.name.lower()), None)
        if not post: return False
        try:
            await post.ainvoke({"channel": self.channel, "text": message})
            return True
        except: return False