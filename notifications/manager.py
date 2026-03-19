# notifications/manager.py
import os
import time
import asyncio
import logging
import config.settings as settings

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self, store=None):
        """
        Initialize the notification hub.
        
        Args:
            store: The database store instance to log notification history.
        """
        self.store = store
        self.notifiers = []
        # Get retry settings from .env or defaults
        self.max_retries = getattr(settings, 'NOTIFICATION_MAX_RETRIES', 3)
        self.retry_delay = getattr(settings, 'NOTIFICATION_RETRY_DELAY', 5)

        # Register Microsoft Channels
        if settings.TEAMS_ENABLED:
            from notifications.teams_webhook import TeamsWebhookNotifier
            self.notifiers.append(("teams", TeamsWebhookNotifier()))
            logger.info("✅ Teams notifications enabled")

        if settings.OUTLOOK_ENABLED:
            from notifications.outlook_notifier import OutlookNotifier
            self.notifiers.append(("outlook", OutlookNotifier()))
            logger.info("✅ Outlook notifications enabled")

        # Register Non-Microsoft Channels
        if settings.SLACK_ENABLED:
            from notifications.slack_mcp import SlackMCPNotifier
            self.notifiers.append(("slack", SlackMCPNotifier()))
            logger.info("✅ Slack MCP enabled")

        if settings.GMAIL_ENABLED:
            from notifications.gmail_mcp import GmailMCPNotifier
            self.notifiers.append(("gmail", GmailMCPNotifier()))
            logger.info("✅ Gmail MCP enabled")

    def notify(self, exception_id, message, priority, category, action_url=""):
        """Send notification to all enabled channels with retry logic."""
        results = {}

        for channel_name, notifier in self.notifiers:
            success = False
            last_error = ""

            # Attempt send with retries
            for attempt in range(1, self.max_retries + 1):
                try:
                    # Notifiers usually have async send methods
                    ok = asyncio.run(notifier.send(
                        exception_id, message, priority, category, action_url
                    ))
                    if ok:
                        success = True
                        break
                    else:
                        last_error = "Notifier returned False"
                except Exception as e:
                    last_error = str(e)
                
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

            status = "sent" if success else "failed"
            results[channel_name] = status

            # PILOT READY: Log notification status to Database for Audit Trail
            if self.store and hasattr(self.store, 'save_notification_log'):
                try:
                    self.store.save_notification_log(
                        exception_id=exception_id,
                        channel=channel_name,
                        status=status,
                        attempts=attempt,
                        error=last_error if not success else ""
                    )
                except Exception as e:
                    logger.error(f"Failed to log notification to DB: {e}")

        return results

    def notify_decision(self, exception_id, action, analyst):
        """Broadcast that a decision has been made."""
        msg = f"✅ Decision recorded: {exception_id[:12]} -> {action} by {analyst}"
        for channel_name, notifier in self.notifiers:
            try:
                # Use simple notification for decision updates
                asyncio.run(notifier.send_simple(msg))
            except Exception as e:
                logger.error(f"Decision alert failed for {channel_name}: {e}")