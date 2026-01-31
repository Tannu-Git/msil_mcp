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
from app.core.batch.batch_executor import batch_executor, BatchRequest as CoreBatchRequest
from app.core.response.shaper import response_shaper, ResponseConfig

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


# ============================================
# P1 Features: Batch Execution & Response Shaping
# ============================================

class BatchToolRequest(BaseModel):
    """Single tool request in a batch"""
    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    request_id: Optional[str] = Field(None, description="Optional request ID for tracking")


class BatchExecutionRequest(BaseModel):
    """Batch tool execution request"""
    requests: List[BatchToolRequest] = Field(..., description="List of tool requests", max_length=20)
    parallel: bool = Field(default=True, description="Execute in parallel (True) or sequential (False)")
    stop_on_error: bool = Field(default=False, description="Stop on first error (sequential mode only)")


class BatchToolResult(BaseModel):
    """Result of a single tool in batch"""
    request_id: str
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: int


class BatchExecutionResponse(BaseModel):
    """Batch execution response"""
    results: List[BatchToolResult]
    statistics: Dict[str, Any]
    correlation_id: str


@router.post("/mcp/batch", response_model=BatchExecutionResponse)
async def execute_batch_tools(
    request: BatchExecutionRequest,
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """
    Execute multiple tools in parallel or sequential
    
    Max 20 tools per batch for safety
    """
    correlation_id = x_correlation_id or str(uuid.uuid4())
    
    # Validate batch size
    if len(request.requests) > settings.BATCH_MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size exceeds maximum of {settings.BATCH_MAX_SIZE}"
        )
    
    # Convert to core batch requests
    batch_requests = [
        CoreBatchRequest(
            tool_name=req.tool_name,
            arguments=req.arguments,
            request_id=req.request_id or str(uuid.uuid4())
        )
        for req in request.requests
    ]
    
    # Execute batch
    if request.parallel:
        results = await batch_executor.execute_batch(batch_requests, correlation_id)
    else:
        results = await batch_executor.execute_batch_sequential(
            batch_requests,
            correlation_id,
            stop_on_error=request.stop_on_error
        )
    
    # Get statistics
    stats = batch_executor.get_statistics(results)
    
    return BatchExecutionResponse(
        results=[
            BatchToolResult(
                request_id=r.request_id,
                tool_name=r.tool_name,
                success=r.success,
                data=r.data,
                error=r.error,
                execution_time_ms=r.execution_time_ms
            )
            for r in results
        ],
        statistics=stats,
        correlation_id=correlation_id
    )


class ResponseShapeRequest(BaseModel):
    """Request to shape API response"""
    data: Dict[str, Any] = Field(..., description="Original response data")
    include_fields: Optional[List[str]] = Field(None, description="Include only these fields")
    exclude_fields: Optional[List[str]] = Field(None, description="Exclude these fields")
    max_array_size: Optional[int] = Field(None, description="Limit array sizes", ge=1, le=1000)
    compact: bool = Field(default=True, description="Remove nulls and empty objects")


@router.post("/mcp/shape-response")
async def shape_response(request: ResponseShapeRequest):
    """
    Shape API response for token optimization
    
    Features:
    - Field selection (whitelist/blacklist)
    - Array size limiting
    - Null/empty value removal
    - Token count estimation
    """
    config = ResponseConfig(
        include_fields=request.include_fields,
        exclude_fields=request.exclude_fields,
        max_array_size=request.max_array_size,
        compact=request.compact
    )
    
    # Shape the response
    shaped_data = response_shaper.shape(request.data, config)
    
    # Estimate token savings
    original_tokens = response_shaper.estimate_token_count(request.data)
    shaped_tokens = response_shaper.estimate_token_count(shaped_data)
    
    return {
        "shaped_data": shaped_data,
        "original_token_estimate": original_tokens,
        "shaped_token_estimate": shaped_tokens,
        "token_savings": original_tokens - shaped_tokens,
        "savings_percentage": round((1 - shaped_tokens / original_tokens) * 100, 1) if original_tokens > 0 else 0
    }

