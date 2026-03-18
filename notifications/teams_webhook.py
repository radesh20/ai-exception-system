import os, requests, logging
logger = logging.getLogger(__name__)

class TeamsWebhookNotifier:
    def __init__(self):
        self.url = os.getenv("TEAMS_WEBHOOK_URL", "")

    async def send(self, exception_id, message, priority, category, action_url=""):
        if not self.url: return False
        emoji = {1:"🟢",2:"🟡",3:"🟠",4:"🔴",5:"🚨"}.get(priority,"⚪")
        color = {1:"Good",2:"Good",3:"Warning",4:"Attention",5:"Attention"}.get(priority,"Default")
        card = {"type":"message","attachments":[{"contentType":"application/vnd.microsoft.card.adaptive","content":{
            "$schema":"http://adaptivecards.io/schemas/adaptive-card.json","type":"AdaptiveCard","version":"1.4",
            "body":[
                {"type":"TextBlock","size":"Large","weight":"Bolder","color":color,"text":f"{emoji} P2P Exception — P{priority}/5"},
                {"type":"FactSet","facts":[{"title":"ID","value":exception_id[:20]},{"title":"Category","value":category}]},
                {"type":"TextBlock","text":message[:1000],"wrap":True,"size":"Small"}],
            "actions":[{"type":"Action.OpenUrl","title":"Review & Decide","url":action_url}] if action_url else []}}]}
        try:
            requests.post(self.url, json=card, timeout=15).raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Teams failed: {e}")
            return False

    async def send_simple(self, message):
        if not self.url: return False
        try:
            requests.post(self.url, json={"type":"message","attachments":[{"contentType":"application/vnd.microsoft.card.adaptive",
                "content":{"type":"AdaptiveCard","version":"1.4","body":[{"type":"TextBlock","text":message,"wrap":True}]}}]}, timeout=15)
            return True
        except: return False