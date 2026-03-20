import os
from dotenv import load_dotenv

load_dotenv(override=True)


def _bool(val):
    return str(val).lower().strip() in ("true", "1", "yes")


AZURE_OPENAI_ENABLED     = _bool(os.getenv("AZURE_OPENAI_ENABLED", "false"))
AZURE_OPENAI_API_KEY     = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT    = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
AZURE_OPENAI_DEPLOYMENT  = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

CELONIS_ENABLED       = _bool(os.getenv("CELONIS_ENABLED", "false"))
CELONIS_MODE          = os.getenv("CELONIS_MODE", "mock")
CELONIS_BASE_URL      = os.getenv("CELONIS_BASE_URL", "")
CELONIS_API_TOKEN     = os.getenv("CELONIS_API_TOKEN", "")
CELONIS_DATA_POOL_ID  = os.getenv("CELONIS_DATA_POOL_ID", "")
CELONIS_DATA_MODEL_ID = os.getenv("CELONIS_DATA_MODEL_ID", "")

STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "json")
STORAGE_PATH    = os.getenv("STORAGE_PATH", "data/db")

TEAMS_ENABLED     = _bool(os.getenv("TEAMS_ENABLED", "true"))
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL", "")

OUTLOOK_ENABLED       = _bool(os.getenv("OUTLOOK_ENABLED", "false"))
OUTLOOK_TENANT_ID     = os.getenv("OUTLOOK_TENANT_ID", "")
OUTLOOK_CLIENT_ID     = os.getenv("OUTLOOK_CLIENT_ID", "")
OUTLOOK_CLIENT_SECRET = os.getenv("OUTLOOK_CLIENT_SECRET", "")
OUTLOOK_FROM_EMAIL    = os.getenv("OUTLOOK_FROM_EMAIL", "")
OUTLOOK_TO_EMAILS     = os.getenv("OUTLOOK_TO_EMAILS", "")

SLACK_ENABLED   = _bool(os.getenv("SLACK_ENABLED", "false"))
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL   = os.getenv("SLACK_CHANNEL", "#p2p-exceptions")

GMAIL_ENABLED   = _bool(os.getenv("GMAIL_ENABLED", "false"))
GMAIL_NOTIFY_TO = os.getenv("GMAIL_NOTIFY_TO", "")

EXECUTION_ENABLED    = _bool(os.getenv("EXECUTION_ENABLED", "true"))
EXECUTION_MODE       = os.getenv("EXECUTION_MODE", "internal")
SERVICENOW_ENABLED   = _bool(os.getenv("SERVICENOW_ENABLED", "false"))
SERVICENOW_INSTANCE  = os.getenv("SERVICENOW_INSTANCE", "")
SERVICENOW_USER      = os.getenv("SERVICENOW_USER", "")
SERVICENOW_PASSWORD  = os.getenv("SERVICENOW_PASSWORD", "")
SERVICENOW_TABLE     = os.getenv("SERVICENOW_TABLE", "incident")

LEARNING_ENABLED              = _bool(os.getenv("LEARNING_ENABLED", "true"))
LEARNING_MIN_SAMPLES          = int(os.getenv("LEARNING_MIN_SAMPLES", "5"))
LEARNING_CONFIDENCE_THRESHOLD = float(os.getenv("LEARNING_CONFIDENCE_THRESHOLD", "0.7"))

API_HOST     = os.getenv("API_HOST", "0.0.0.0")
API_PORT     = int(os.getenv("API_PORT", "8000"))
CORS_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")]




# ═════════════════════════════════════════════════════════════
# SERVICENOW CONFIGURATION
# ═════════════════════════════════════════════════════════════

SERVICENOW_URL = os.getenv("SERVICENOW_URL", "")

SERVICENOW_USER = os.getenv("SERVICENOW_USER", "")

SERVICENOW_PASS = os.getenv("SERVICENOW_PASS", "")


# ═════════════════════════════════════════════════════════════
# ACTION AGENT CONFIGURATION
# ═════════════════════════════════════════════════════════════

ACTION_AGENT_ENABLED = os.getenv("ACTION_AGENT_ENABLED", "true").lower() == "true"
AUTO_CREATE_INCIDENT = os.getenv("AUTO_CREATE_INCIDENT", "true").lower() == "true"
AUTO_MONITOR_INTERVAL = int(os.getenv("AUTO_MONITOR_INTERVAL", "300"))  # 5 minutes
AUTO_CLOSE_ON_RESOLVE = os.getenv("AUTO_CLOSE_ON_RESOLVE", "true").lower() == "true"