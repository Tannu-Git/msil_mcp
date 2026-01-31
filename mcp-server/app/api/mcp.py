"""
MCP Protocol Handler - JSON-RPC over HTTP
Implements Model Context Protocol for tool discovery and execution
"""
import logging
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

from app.config import settings
from app.core.tools.registry import tool_registry
from app.core.tools.executor import tool_executor

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# MCP Protocol Models
# ============================================

class MCPRequest(BaseModel):
    """MCP JSON-RPC Request"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """MCP JSON-RPC Response"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class MCPError(BaseModel):
    """MCP Error Object"""
    code: int
    message: str
    data: Optional[Any] = None


class ToolDefinition(BaseModel):
    """MCP Tool Definition"""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class ToolCallResult(BaseModel):
    """MCP Tool Call Result"""
    content: List[Dict[str, Any]]
    isError: bool = False


# ============================================
# MCP Endpoints
# ============================================

@router.post("/mcp")
async def mcp_handler(
    request: MCPRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
) -> MCPResponse:
    """
    Main MCP Protocol Handler
    Supports: tools/list, tools/call
    """
    correlation_id = x_correlation_id or str(uuid.uuid4())
    logger.info(f"[{correlation_id}] MCP Request: {request.method}")
    
    # Simple API key validation for MVP
    if settings.API_KEY and x_api_key != settings.API_KEY:
        # For MVP, allow requests without API key in dev mode
        if not settings.DEBUG:
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32001,
                    "message": "Unauthorized: Invalid API Key"
                }
            )
    
    try:
        if request.method == "tools/list":
            result = await handle_tools_list(correlation_id)
        elif request.method == "tools/call":
            result = await handle_tools_call(request.params, correlation_id)
        elif request.method == "initialize":
            result = await handle_initialize()
        else:
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32601,
                    "message": f"Method not found: {request.method}"
                }
            )
        
        return MCPResponse(
            jsonrpc="2.0",
            id=request.id,
            result=result
        )
        
    except Exception as e:
        logger.error(f"[{correlation_id}] MCP Error: {str(e)}")
        return MCPResponse(
            jsonrpc="2.0",
            id=request.id,
            error={
                "code": -32000,
                "message": str(e)
            }
        )


async def handle_initialize() -> Dict[str, Any]:
    """Handle MCP initialize request"""
    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION
        },
        "capabilities": {
            "tools": {}
        }
    }


async def handle_tools_list(correlation_id: str) -> Dict[str, Any]:
    """
    Handle tools/list request
    Returns list of available tools with their schemas
    """
    logger.info(f"[{correlation_id}] Listing tools")
    
    tools = await tool_registry.list_tools()
    
    tool_definitions = []
    for tool in tools:
        tool_definitions.append({
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.input_schema
        })
    
    logger.info(f"[{correlation_id}] Found {len(tool_definitions)} tools")
    return {"tools": tool_definitions}


async def handle_tools_call(
    params: Optional[Dict[str, Any]],
    correlation_id: str
) -> Dict[str, Any]:
    """
    Handle tools/call request
    Executes the specified tool with given arguments
    """
    if not params:
        raise ValueError("Missing params for tools/call")
    
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    if not tool_name:
        raise ValueError("Missing tool name")
    
    logger.info(f"[{correlation_id}] Calling tool: {tool_name}")
    logger.debug(f"[{correlation_id}] Arguments: {arguments}")
    
    # Execute the tool
    result = await tool_executor.execute(
        tool_name=tool_name,
        arguments=arguments,
        correlation_id=correlation_id
    )
    
    return {
        "content": [
            {
                "type": "text",
                "text": str(result)
            }
        ],
        "isError": False
    }


# ============================================
# Direct REST Endpoints (for easier testing)
# ============================================

@router.get("/mcp/tools")
async def list_tools_rest():
    """REST endpoint to list tools (for testing)"""
    tools = await tool_registry.list_tools()
    return {
        "tools": [
            {
                "name": t.name,
                "display_name": t.display_name,
                "description": t.description,
                "category": t.category,
                "input_schema": t.input_schema
            }
            for t in tools
        ]
    }


@router.post("/mcp/tools/{tool_name}/call")
async def call_tool_rest(
    tool_name: str,
    arguments: Dict[str, Any],
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """REST endpoint to call a tool (for testing)"""
    correlation_id = x_correlation_id or str(uuid.uuid4())
    
    result = await tool_executor.execute(
        tool_name=tool_name,
        arguments=arguments,
        correlation_id=correlation_id
    )
    
    return {
        "tool_name": tool_name,
        "result": result,
        "correlation_id": correlation_id
    }
