"""
MCP Tool Endpoints - Teams Webhook Integration
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
from api.integrations.mcp_tools import TeamsTools

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Teams tools
teams_tools = TeamsTools()


# ═══════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════

class ToolInvocationRequest(BaseModel):
    """MCP tool invocation request."""
    tool: str
    arguments: Dict[str, Any]


class ToolInvocationResponse(BaseModel):
    """MCP tool invocation response."""
    status: str  # "success" or "error"
    tool: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ═══════════════════════════════════════════════════════════
# TOOL REGISTRY
# ═══════════════════════════════════════════════════════════

TOOL_REGISTRY = {
    "notify_procurement_team": {
        "tool": teams_tools.notify_procurement_team,
        "description": "Send Teams notification to procurement team",
        "params": ["case_id", "issue", "priority", "recommendation", "financial_exposure"],
    },
    "send_simple_alert": {
        "tool": teams_tools.send_simple_alert,
        "description": "Send simple text alert to Teams",
        "params": ["message"],
    },
}


# ═══════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/tools")
async def list_tools():
    """
    List available MCP tools.

    Returns tools with input schemas for agent discovery.
    """
    tools = []

    for tool_name, tool_meta in TOOL_REGISTRY.items():
        tool_def = {
            "name": tool_name,
            "description": tool_meta["description"],
            "inputSchema": {
                "type": "object",
                "properties": {
                    param: {"type": "string", "description": param}
                    for param in tool_meta["params"]
                },
                "required": tool_meta["params"],
            },
        }
        tools.append(tool_def)

    logger.info(f"[INFO] MCP Tool discovery: {len(tools)} tools available")
    return {"tools": tools}


@router.post("/invoke", response_model=ToolInvocationResponse)
async def invoke_tool(request: ToolInvocationRequest):
    """
    Invoke a tool (MCP protocol).

    This is the main endpoint agents call to execute tools.

    Example request:
    {
        "tool": "notify_procurement_team",
        "arguments": {
            "case_id": "PO-2024-0001",
            "issue": "Payment Blocked",
            "priority": 4,
            "recommendation": "three_way_match_recheck",
            "financial_exposure": 85000.00
        }
    }
    """
    tool_name = request.tool
    arguments = request.arguments

    logger.info(f"[MCP] Invoking tool: {tool_name}")

    # Check if tool exists
    if tool_name not in TOOL_REGISTRY:
        logger.error(f"[MCP] Tool not found: {tool_name}")
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    try:
        # Get tool function
        tool_func = TOOL_REGISTRY[tool_name]["tool"]

        # Call tool with arguments
        result = tool_func(**arguments)

        # Check for errors in result
        if isinstance(result, dict) and "error" in result:
            logger.warning(f"[MCP] Tool {tool_name} error: {result['error']}")
            return ToolInvocationResponse(
                status="error",
                tool=tool_name,
                error=result["error"],
            )

        logger.info(f"[OK] [MCP] Tool {tool_name} succeeded")
        return ToolInvocationResponse(
            status="success",
            tool=tool_name,
            result=result,
        )

    except Exception as e:
        logger.error(f"[ERROR] [MCP] Tool {tool_name} failed: {e}")
        return ToolInvocationResponse(
            status="error",
            tool=tool_name,
            error=str(e),
        )


# ═══════════════════════════════════════════════════════════
# CONVENIENCE REST ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.post("/teams/notify")
async def teams_notify(
        case_id: str,
        issue: str,
        priority: int,
        recommendation: str,
        financial_exposure: float = 0,
        exception_uuid: str = "",
):
    """Send Teams notification (REST endpoint)."""
    result = teams_tools.notify_procurement_team(
        case_id, issue, priority, recommendation, financial_exposure, exception_uuid
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/teams/alert")
async def teams_alert(message: str):
    """Send simple Teams alert (REST endpoint)."""
    result = teams_tools.send_simple_alert(message)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result