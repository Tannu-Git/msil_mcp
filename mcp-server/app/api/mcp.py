"""
MCP Protocol Handler - JSON-RPC over HTTP
Implements Model Context Protocol for tool discovery and execution
"""
import logging
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.config import settings
from app.core.tools.registry import tool_registry
from app.core.tools.executor import tool_executor
from app.core.exposure.manager import exposure_manager
from app.core.batch.batch_executor import batch_executor, BatchRequest as CoreBatchRequest
from app.core.response.shaper import response_shaper, ResponseConfig
from app.core.streaming.sse import create_sse_response, send_tool_progress, send_tool_result
from app.core.policy.engine import policy_engine
from app.core.policy.risk_policy import risk_policy_manager
from app.core.cache.rate_limiter import rate_limiter
from app.core.audit import audit_service
from app.core.request_context import RequestContext, get_request_context
from app.core.exceptions import AuthorizationError, PolicyError

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
    context: RequestContext = Depends(get_request_context),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> MCPResponse:
    """
    Main MCP Protocol Handler
    Supports: tools/list, tools/call
    
    NEW: Includes exposure governance (Layer B)
    - tools/list is filtered by user's exposed tools
    - tools/call validates tool is exposed (defense-in-depth)
    """
    correlation_id = context.correlation_id or str(uuid.uuid4())
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
    
    user_context = {
        "user_id": context.user_id,
        "roles": context.roles,
        "correlation_id": correlation_id
    }
    
    try:
        if request.method == "tools/list":
            result = await handle_tools_list(correlation_id, user_context)
        elif request.method == "tools/call":
            result = await handle_tools_call(request.params, correlation_id, context, idempotency_key)
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
        
    except HTTPException:
        raise
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


async def handle_tools_list(correlation_id: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle tools/list request
    
    PHASE 1 NEW: Applies exposure filtering before returning tools.
    Only returns tools user is exposed to based on role assignments.
    
    Returns list of available tools with their schemas
    """
    user_id = user_context.get("user_id", "anonymous")
    roles = user_context.get("roles", [])
    
    logger.info(f"[{correlation_id}] Listing tools for user {user_id} (roles={roles})")
    
    # Apply per-user rate limit if enabled
    if settings.RATE_LIMIT_ENABLED and user_id:
        user_limit = settings.RATE_LIMIT_PER_USER
        rate = await rate_limiter.check_user_rate_limit(user_id, user_limit)
        if not rate.allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(rate.retry_after or 0)}
            )

    # Get all active tools from registry
    all_tools = await tool_registry.list_tools()
    
    # PHASE 1 NEW: Apply exposure filtering
    if user_id and roles:
        exposed_tools = await exposure_manager.filter_tools(
            all_tools, user_id, roles
        )
        logger.info(
            f"[{correlation_id}] Exposure filter: {len(all_tools)} → {len(exposed_tools)} tools"
        )
    else:
        # Fallback if no user context (shouldn't happen in practice)
        exposed_tools = all_tools
        logger.warning(f"[{correlation_id}] No user context for exposure filtering, returning all tools")
    
    # Apply policy engine for discovery
    policy_filtered = []
    for tool in exposed_tools:
        decision = await policy_engine.evaluate(
            action="read",
            resource=tool.name,
            context={"roles": roles, "user_id": user_id, "tool": tool}
        )
        if decision.allowed:
            policy_filtered.append(tool)
        else:
            await audit_service.log_policy_decision(
                decision={"allowed": decision.allowed, "reason": decision.reason},
                context={"user_id": user_id, "tool_name": tool.name, "action": "read"},
                correlation_id=correlation_id
            )

    # Build tool definitions for response
    tool_definitions = []
    for tool in policy_filtered:
        tool_definitions.append({
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.input_schema,
            "bundle": tool.bundle_name  # Include bundle metadata
        })
    
    logger.info(f"[{correlation_id}] Returning {len(tool_definitions)} exposed tools")
    return {"tools": tool_definitions}


async def handle_tools_call(
    params: Optional[Dict[str, Any]],
    correlation_id: str,
    context: RequestContext,
    idempotency_key: Optional[str]
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

    tool = await tool_registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    # Exposure check (Layer B)
    exposed_refs = await exposure_manager.get_exposed_tools_for_user(
        context.user_id or "anonymous",
        context.roles
    )
    if not exposure_manager.is_tool_exposed(tool.name, tool.bundle_name, exposed_refs):
        raise HTTPException(status_code=403, detail="Tool not exposed for this role")

    # Policy check (Layer A)
    decision = await policy_engine.evaluate(
        action="invoke",
        resource=tool.name,
        context={"roles": context.roles, "user_id": context.user_id, "tool": tool}
    )
    if not decision.allowed:
        await audit_service.log_policy_decision(
            decision={"allowed": decision.allowed, "reason": decision.reason},
            context={"user_id": context.user_id, "tool_name": tool.name, "action": "invoke"},
            correlation_id=correlation_id
        )
        raise HTTPException(status_code=403, detail=decision.reason)

    # Rate limiting
    if settings.RATE_LIMIT_ENABLED and context.user_id:
        rate_multiplier = risk_policy_manager.get_rate_limit_multiplier(tool.rate_limit_tier)
        user_limit = int(settings.RATE_LIMIT_PER_USER * rate_multiplier)
        tool_limit = int(settings.RATE_LIMIT_PER_TOOL * rate_multiplier)

        user_rate = await rate_limiter.check_user_rate_limit(context.user_id, user_limit)
        if not user_rate.allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(user_rate.retry_after or 0)}
            )

        tool_rate = await rate_limiter.check_tool_rate_limit(tool.name, tool_limit)
        if not tool_rate.allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(tool_rate.retry_after or 0)}
            )
    
    # Execute the tool
    try:
        result = await tool_executor.execute(
            tool_name=tool_name,
            arguments=arguments,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            user_id=context.user_id,
            user_roles=context.roles,
            is_elevated=context.is_elevated
        )
        await audit_service.log_tool_call(
            tool_name=tool_name,
            params=arguments,
            result=result,
            latency=result.get("execution_time_ms", 0) / 1000.0,
            correlation_id=correlation_id,
            user_id=context.user_id or "unknown",
            status="success"
        )
    except (AuthorizationError, PolicyError) as e:
        await audit_service.log_tool_call(
            tool_name=tool_name,
            params=arguments,
            result={},
            latency=0,
            correlation_id=correlation_id,
            user_id=context.user_id or "unknown",
            status="failure",
            error=str(e)
        )
        status_code = 403 if isinstance(e, AuthorizationError) else 409
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        await audit_service.log_tool_call(
            tool_name=tool_name,
            params=arguments,
            result={},
            latency=0,
            correlation_id=correlation_id,
            user_id=context.user_id or "unknown",
            status="failure",
            error=str(e)
        )
        raise
    
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
    context: RequestContext = Depends(get_request_context),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """REST endpoint to call a tool (for testing)"""
    correlation_id = x_correlation_id or str(uuid.uuid4())
    
    try:
        result = await tool_executor.execute(
            tool_name=tool_name,
            arguments=arguments,
            correlation_id=correlation_id,
            user_id=context.user_id,
            user_roles=context.roles,
            is_elevated=context.is_elevated
        )
    except (AuthorizationError, PolicyError) as e:
        status_code = 403 if isinstance(e, AuthorizationError) else 409
        raise HTTPException(status_code=status_code, detail=str(e))
    
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
    context: RequestContext = Depends(get_request_context),
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
        results = await batch_executor.execute_batch(
            batch_requests,
            correlation_id,
            user_id=context.user_id,
            user_roles=context.roles,
            is_elevated=context.is_elevated
        )
    else:
        results = await batch_executor.execute_batch_sequential(
            batch_requests,
            correlation_id,
            user_id=context.user_id,
            user_roles=context.roles,
            is_elevated=context.is_elevated,
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


# ============================================
# P2 Features: SSE Streaming Support
# ============================================

@router.get("/mcp/stream/{stream_id}")
async def stream_tool_execution(stream_id: str, request: Request):
    """
    Server-Sent Events stream for real-time tool execution updates
    
    Usage:
    1. Create stream: GET /mcp/stream/{stream_id}
    2. Execute tool with stream_id parameter
    3. Receive progress updates in real-time
    
    Events:
    - connected: Initial connection
    - tool_progress: Progress updates (0-100%)
    - tool_result: Final result
    - tool_error: Error occurred
    """
    return await create_sse_response(stream_id, request)


@router.post("/mcp/tools/{tool_name}/call-stream")
async def call_tool_with_stream(
    tool_name: str,
    arguments: Dict[str, Any],
    stream_id: Optional[str] = None,
    context: RequestContext = Depends(get_request_context),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """
    Execute tool with SSE streaming progress updates
    
    Returns immediately with stream_id. Progress sent via SSE.
    """
    correlation_id = x_correlation_id or str(uuid.uuid4())
    stream_id = stream_id or f"stream-{uuid.uuid4()}"
    
    # Start async execution (would use background task in production)
    import asyncio
    
    async def execute_with_progress():
        try:
            # Send progress: starting
            await send_tool_progress(
                stream_id=stream_id,
                tool_name=tool_name,
                progress=0,
                message="Tool execution starting"
            )
            
            # Send progress: 50%
            await send_tool_progress(
                stream_id=stream_id,
                tool_name=tool_name,
                progress=50,
                message="Executing tool"
            )
            
            # Execute tool
            result = await tool_executor.execute(
                tool_name=tool_name,
                arguments=arguments,
                correlation_id=correlation_id,
                user_id=context.user_id,
                user_roles=context.roles,
                is_elevated=context.is_elevated
            )
            
            # Send result
            await send_tool_result(
                stream_id=stream_id,
                tool_name=tool_name,
                result=result,
                success=True
            )
            
        except Exception as e:
            await send_tool_result(
                stream_id=stream_id,
                tool_name=tool_name,
                result=None,
                success=False,
                error=str(e)
            )
    
    # Start background execution
    asyncio.create_task(execute_with_progress())
    
    return {
        "stream_id": stream_id,
        "message": "Tool execution started. Connect to SSE stream for updates.",
        "stream_url": f"/api/mcp/stream/{stream_id}"
    }

