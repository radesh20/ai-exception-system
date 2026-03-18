import os, requests, logging
logger = logging.getLogger(__name__)

class OutlookNotifier:
    def __init__(self):
        self.tenant = os.getenv("OUTLOOK_TENANT_ID", "")
        self.client_id = os.getenv("OUTLOOK_CLIENT_ID", "")
        self.client_secret = os.getenv("OUTLOOK_CLIENT_SECRET", "")
        self.from_email = os.getenv("OUTLOOK_FROM_EMAIL", "")
        self.to_emails = [e.strip() for e in os.getenv("OUTLOOK_TO_EMAILS", "").split(",") if e.strip()]
        self._token = None

    def _get_token(self):
        if self._token: return self._token
        try:
            import msal
            app = msal.ConfidentialClientApplication(self.client_id,
                authority=f"https://login.microsoftonline.com/{self.tenant}", client_credential=self.client_secret)
            result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
            self._token = result.get("access_token", "")
            return self._token
        except Exception as e:
            logger.error(f"Outlook token failed: {e}")
            return ""

    async def send(self, exception_id, message, priority, category, action_url=""):
        token = self._get_token()
        if not token or not self.to_emails: return False
        emoji = {1:"🟢",2:"🟡",3:"🟠",4:"🔴",5:"🚨"}.get(priority,"⚪")
        subject = f"{emoji} [P{priority}] P2P Exception: {category} — {exception_id[:12]}"
        body = f"P2P Exception Alert — Priority {priority}/5\n{'='*50}\n\n{message}\n"
        if action_url: body += f"\nReview: {action_url}"
        payload = {"message":{"subject":subject,"body":{"contentType":"Text","content":body},
            "toRecipients":[{"emailAddress":{"address":a}} for a in self.to_emails]}}
        try:
            requests.post(f"https://graph.microsoft.com/v1.0/users/{self.from_email}/sendMail",
                headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"}, json=payload, timeout=15).raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Outlook failed: {e}")
            return False

    async def send_simple(self, message):
        token = self._get_token()
        if not token or not self.to_emails: return False
        try:
            requests.post(f"https://graph.microsoft.com/v1.0/users/{self.from_email}/sendMail",
                headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},
                json={"message":{"subject":"P2P Update","body":{"contentType":"Text","content":message},
                    "toRecipients":[{"emailAddress":{"address":a}} for a in self.to_emails]}}, timeout=15)
            return True
        except: return False