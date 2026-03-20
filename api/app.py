import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import config.settings as settings
from api.routes import exceptions, decisions, actions, stats, learning, webhooks
from api.routes import mcp

app = FastAPI(title="P2P Exception Management API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Include all routers
app.include_router(exceptions.router, prefix="/api", tags=["Exceptions"])
app.include_router(decisions.router, prefix="/api", tags=["Decisions"])
app.include_router(actions.router, prefix="/api", tags=["Actions"])
app.include_router(stats.router, prefix="/api", tags=["Statistics"])
app.include_router(learning.router, prefix="/api", tags=["Learning"])
app.include_router(webhooks.router, prefix="/api", tags=["Webhooks"])
app.include_router(mcp.router, prefix="/api/mcp", tags=["MCP Tools"])

@app.get("/api/health")
def health(): 
    return {"status": "ok"}

@app.get("/api/config")
def get_config():
    return {
        "azure_enabled": settings.AZURE_OPENAI_ENABLED, 
        "celonis_mode": settings.CELONIS_MODE,
        "storage_backend": settings.STORAGE_BACKEND, 
        "teams_enabled": settings.TEAMS_ENABLED,
        "outlook_enabled": settings.OUTLOOK_ENABLED, 
        "slack_enabled": settings.SLACK_ENABLED,
        "gmail_enabled": settings.GMAIL_ENABLED, 
        "execution_mode": settings.EXECUTION_MODE,
        "servicenow_enabled": settings.SERVICENOW_ENABLED, 
        "learning_enabled": settings.LEARNING_ENABLED
    }