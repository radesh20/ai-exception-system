import os, asyncio, logging
import config.settings as settings
logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        self.notifiers = []
        if settings.TEAMS_ENABLED:
            from notifications.teams_webhook import TeamsWebhookNotifier
            self.notifiers.append(TeamsWebhookNotifier())
            logger.info("✅ Teams enabled")
        if settings.OUTLOOK_ENABLED:
            from notifications.outlook_notifier import OutlookNotifier
            self.notifiers.append(OutlookNotifier())
            logger.info("✅ Outlook enabled")
        if settings.SLACK_ENABLED:
            from notifications.slack_mcp import SlackMCPNotifier
            self.notifiers.append(SlackMCPNotifier())
            logger.info("✅ Slack enabled")
        if settings.GMAIL_ENABLED:
            from notifications.gmail_mcp import GmailMCPNotifier
            self.notifiers.append(GmailMCPNotifier())
            logger.info("✅ Gmail enabled")

    def notify(self, exception_id, message, priority, category, action_url=""):
        results = {}
        for n in self.notifiers:
            name = n.__class__.__name__
            try:
                ok = asyncio.run(n.send(exception_id, message, priority, category, action_url))
                results[name] = "sent" if ok else "failed"
            except Exception as e:
                results[name] = f"error: {e}"
        return results

    def notify_decision(self, exception_id, action, analyst):
        msg = f"✅ Decision: {exception_id[:12]} → {action} by {analyst}"
        for n in self.notifiers:
            try: asyncio.run(n.send_simple(msg))
            except: pass