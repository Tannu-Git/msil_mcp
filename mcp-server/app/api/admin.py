"""
Admin API Endpoints
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime, timedelta

from app.core.tools.registry import tool_registry
from app.db.repositories import get_metrics, get_recent_executions
from app.core.audit import audit_service
from app.core.auth.oauth2_provider import get_current_user, require_admin
from app.core.auth.models import UserInfo

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard")
async def get_dashboard():
    """Get dashboard metrics"""
    try:
        # For MVP, return mock metrics - will connect to real data later
        return {
            "total_tools": await tool_registry.count_tools(),
            "active_tools": await tool_registry.count_tools(active_only=True),
            "total_executions_today": 156,
            "successful_executions": 148,
            "failed_executions": 8,
            "average_response_time_ms": 245,
            "active_sessions": 12,
            "bookings_created_today": 23
        }
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_tools(
    category: Optional[str] = Query(None),
    active_only: bool = Query(True)
):
    """List all tools with optional filtering"""
    try:
        tools = await tool_registry.list_tools(
            category=category,
            active_only=active_only
        )
        return {
            "tools": [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "display_name": t.display_name,
                    "description": t.description,
                    "category": t.category,
                    "api_endpoint": t.api_endpoint,
                    "http_method": t.http_method,
                    "is_active": t.is_active,
                    "version": t.version,
                    "created_at": t.created_at.isoformat() if t.created_at else None
                }
                for t in tools
            ],
            "total": len(tools)
        }
    except Exception as e:
        logger.error(f"List tools error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/{tool_name}")
async def get_tool(tool_name: str):
    """Get tool details"""
    try:
        tool = await tool_registry.get_tool(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        
        return {
            "id": str(tool.id),
            "name": tool.name,
            "display_name": tool.display_name,
            "description": tool.description,
            "category": tool.category,
            "api_endpoint": tool.api_endpoint,
            "http_method": tool.http_method,
            "input_schema": tool.input_schema,
            "output_schema": tool.output_schema,
            "is_active": tool.is_active,
            "version": tool.version,
            "created_at": tool.created_at.isoformat() if tool.created_at else None,
            "updated_at": tool.updated_at.isoformat() if tool.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get tool error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions")
async def list_executions(
    limit: int = Query(50, ge=1, le=100),
    tool_name: Optional[str] = Query(None)
):
    """Get recent tool executions"""
    try:
        # For MVP, return mock data
        return {
            "executions": [
                {
                    "id": "exec-001",
                    "tool_name": "create_service_booking",
                    "status": "success",
                    "execution_time_ms": 234,
                    "created_at": datetime.utcnow().isoformat()
                },
                {
                    "id": "exec-002",
                    "tool_name": "resolve_vehicle",
                    "status": "success",
                    "execution_time_ms": 156,
                    "created_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat()
                },
                {
                    "id": "exec-003",
                    "tool_name": "get_nearby_dealers",
                    "status": "success",
                    "execution_time_ms": 312,
                    "created_at": (datetime.utcnow() - timedelta(minutes=10)).isoformat()
                }
            ],
            "total": 3
        }
    except Exception as e:
        logger.error(f"List executions error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def list_categories():
    """List all tool categories"""
    try:
        tools = await tool_registry.list_tools()
        categories = list(set(t.category for t in tools if t.category))
        return {
            "categories": categories,
            "total": len(categories)
        }
    except Exception as e:
        logger.error(f"List categories error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Audit Log Endpoints
# ============================================

@router.get("/audit-logs")
async def get_audit_logs(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    tool_name: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get audit logs with filters.
    
    Query Parameters:
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        tool_name: Filter by tool name
        user_id: Filter by user ID
        status: Filter by status (success, failure, denied)
        event_type: Filter by event type (tool_call, policy_decision, auth_event, config_change)
        limit: Maximum number of logs to return
        offset: Pagination offset
    """
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Get logs from audit service
        result = await audit_service.get_logs(
            start_date=start_dt,
            end_date=end_dt,
            tool_name=tool_name,
            user_id=user_id,
            status=status,
            event_type=event_type,
            limit=limit,
            offset=offset
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Get audit logs error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-logs/{event_id}")
async def get_audit_log_detail(event_id: str):
    """Get detailed audit log entry.
    
    Args:
        event_id: Unique event ID
    """
    try:
        # Get all logs and find the specific event
        result = await audit_service.get_logs(limit=1000)
        logs = result.get("logs", [])
        
        log = next((log for log in logs if log["event_id"] == event_id), None)
        
        if not log:
            raise HTTPException(status_code=404, detail="Audit log not found")
        
        return log
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get audit log detail error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-logs/stats/summary")
async def get_audit_stats():
    """Get audit log statistics summary."""
    try:
        result = await audit_service.get_logs(limit=10000)
        logs = result.get("logs", [])
        
        # Calculate statistics
        total = len(logs)
        by_type = {}
        by_status = {}
        
        for log in logs:
            event_type = log.get("event_type", "unknown")
            status = log.get("status", "unknown")
            
            by_type[event_type] = by_type.get(event_type, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total_events": total,
            "by_type": by_type,
            "by_status": by_status
        }
        
    except Exception as e:
        logger.error(f"Get audit stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

