"""
Analytics and Metrics API
Provides data for admin dashboard
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.db.database import get_db
from app.core.tools.registry import Tool, tool_registry
from app.core.metrics.collector import metrics_collector

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/metrics/summary")
async def get_metrics_summary() -> Dict[str, Any]:
    """Get high-level metrics for dashboard KPIs"""
    
    try:
        # Get tools from registry
        all_tools = tool_registry.list_tools()
        total_tools = len(all_tools)
        active_tools = sum(1 for tool in all_tools if tool.is_active)
        
        # Get real metrics from collector
        real_metrics = metrics_collector.get_summary_metrics()
        
        metrics = {
            "total_tools": total_tools,
            "active_tools": active_tools,
            "total_requests": real_metrics["total_requests"],
            "success_rate": real_metrics["success_rate"],
            "avg_response_time": int(real_metrics["avg_response_time"]),  # ms
            "total_conversations": 0,  # TODO: Track conversations
            "tools_by_status": {
                "active": active_tools,
                "inactive": total_tools - active_tools
            },
            "recent_activity": {
                "last_hour": 0,  # TODO: Time-filtered metrics
                "last_24_hours": real_metrics["total_requests"],
                "last_7_days": real_metrics["total_requests"]
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to fetch metrics summary: {e}")
        return {
            "total_tools": 0,
            "active_tools": 0,
            "total_requests": 0,
            "success_rate": 0,
            "avg_response_time": 0,
            "total_conversations": 0,
            "tools_by_status": {"active": 0, "inactive": 0},
            "recent_activity": {"last_hour": 0, "last_24_hours": 0, "last_7_days": 0}
        }


@router.get("/metrics/tools-usage")
async def get_tools_usage(
    limit: int = Query(default=10, le=50)
) -> List[Dict[str, Any]]:
    """Get tool usage statistics"""
    
    try:
        # Get real metrics from collector
        tools_metrics = metrics_collector.get_all_tools_metrics()
        
        # Convert to list and sort by total calls
        usage_data = []
        for tool_name, metrics in sorted(
            tools_metrics.items(), 
            key=lambda x: x[1]["total_calls"], 
            reverse=True
        )[:limit]:
            usage_data.append({
                "tool_name": tool_name,
                "total_calls": metrics["total_calls"],
                "success_calls": metrics["success_calls"],
                "failed_calls": metrics["failed_calls"],
                "avg_duration_ms": int(metrics["avg_duration_ms"]),
                "last_used": metrics["last_used"].isoformat() if metrics["last_used"] else None
            })
        
        return usage_data
        
    except Exception as e:
        logger.error(f"Failed to fetch tools usage: {e}")
        return []


@router.get("/metrics/requests-timeline")
async def get_requests_timeline(
    days: int = Query(default=7, le=30)
) -> List[Dict[str, Any]]:
    """Get request timeline data for charts"""
    
    # Mock timeline data
    timeline = []
    base_date = datetime.now() - timedelta(days=days)
    
    for i in range(days):
        date = base_date + timedelta(days=i)
        timeline.append({
            "date": date.strftime("%Y-%m-%d"),
            "requests": 100 + (i * 20),  # Mock
            "success": 95 + (i * 19),  # Mock
            "errors": 5 + i  # Mock
        })
    
    return timeline


@router.get("/metrics/performance")
async def get_performance_metrics() -> Dict[str, Any]:
    """Get performance metrics"""
    
    return {
        "response_time": {
            "p50": 85,  # Mock (ms)
            "p95": 145,  # Mock (ms)
            "p99": 250,  # Mock (ms)
            "max": 450  # Mock (ms)
        },
        "throughput": {
            "requests_per_second": 12.5,  # Mock
            "concurrent_connections": 8  # Mock
        },
        "errors": {
            "total": 31,  # Mock
            "rate": 1.5,  # Mock (%)
            "by_type": {
                "timeout": 12,
                "validation": 10,
                "server_error": 9
            }
        }
    }


@router.get("/tools/list")
async def get_tools_list(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, le=100)
) -> Dict[str, Any]:
    """Get paginated list of tools"""
    
    try:
        # Get tools from registry
        all_tools = tool_registry.list_tools()
        total = len(all_tools)
        
        # Paginate
        tools = all_tools[skip:skip + limit]
        
        # Convert to dict
        tools_list = []
        for tool in tools:
            tools_list.append({
                "id": str(tool.id),
                "name": tool.name,
                "description": tool.description,
                "api_endpoint": tool.api_endpoint,
                "http_method": tool.http_method,
                "is_active": tool.is_active,
                "created_at": tool.created_at.isoformat() if tool.created_at else None,
                "updated_at": tool.updated_at.isoformat() if tool.updated_at else None,
                "category": tool.category,
                "tags": []  # Not in current Tool model
            })
        
        return {
            "total": total,
            "items": tools_list,
            "page": skip // limit + 1,
            "page_size": limit
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch tools list: {e}")
        return {
            "total": 0,
            "items": [],
            "page": 1,
            "page_size": limit
        }


@router.get("/tools/{tool_name}")
async def get_tool_details(
    tool_name: str
) -> Dict[str, Any]:
    """Get detailed information about a specific tool"""
    
    try:
        tool = tool_registry.get_tool(tool_name)
        
        if not tool:
            return {"error": "Tool not found"}
        
        # Get real usage metrics for this tool
        tool_metrics = metrics_collector.get_tool_metrics(tool_name)
        
        return {
            "id": str(tool.id),
            "name": tool.name,
            "description": tool.description,
            "api_endpoint": tool.api_endpoint,
            "http_method": tool.http_method,
            "input_schema": tool.input_schema,
            "output_schema": tool.output_schema,
            "is_active": tool.is_active,
            "created_at": tool.created_at.isoformat() if tool.created_at else None,
            "updated_at": tool.updated_at.isoformat() if tool.updated_at else None,
            "category": tool.category,
            "tags": [],
            "usage_stats": {
                "total_calls": tool_metrics["total_calls"],
                "success_rate": tool_metrics["success_rate"],
                "avg_duration_ms": int(tool_metrics["avg_duration_ms"]),
                "last_used": tool_metrics["last_used"].isoformat() if tool_metrics["last_used"] else None
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch tool details: {e}")
        return {"error": str(e)}
