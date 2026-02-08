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
        all_tools = await tool_registry.list_tools(active_only=False)
        total_tools = len(all_tools)
        active_tools = sum(1 for tool in all_tools if tool.is_active)
        
        # Get real metrics from collector
        real_metrics = metrics_collector.get_summary_metrics()
        
        # Get time-filtered metrics
        last_hour_metrics = metrics_collector.get_metrics_by_timeframe(hours=1)
        last_24h_metrics = metrics_collector.get_metrics_by_timeframe(hours=24)
        last_7d_metrics = metrics_collector.get_metrics_by_timeframe(hours=168)
        
        metrics = {
            "total_tools": total_tools,
            "active_tools": active_tools,
            "total_requests": real_metrics["total_requests"],
            "success_rate": real_metrics["success_rate"],
            "avg_response_time": int(real_metrics["avg_response_time"]),  # ms
            "total_conversations": metrics_collector.get_conversation_count(),
            "tools_by_status": {
                "active": active_tools,
                "inactive": total_tools - active_tools
            },
            "recent_activity": {
                "last_hour": last_hour_metrics["total_requests"],
                "last_24_hours": last_24h_metrics["total_requests"],
                "last_7_days": last_7d_metrics["total_requests"]
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
    timeline = []
    executions = metrics_collector.get_all_executions()
    base_date = datetime.now() - timedelta(days=days)

    counts = {}
    for exec_item in executions:
        started_at = exec_item.get("started_at")
        if not started_at:
            continue
        try:
            ts = datetime.fromisoformat(started_at)
        except ValueError:
            continue
        if ts < base_date:
            continue
        key = ts.strftime("%Y-%m-%d")
        if key not in counts:
            counts[key] = {"requests": 0, "success": 0, "errors": 0}
        counts[key]["requests"] += 1
        if exec_item.get("status") == "success":
            counts[key]["success"] += 1
        else:
            counts[key]["errors"] += 1

    for i in range(days):
        date = base_date + timedelta(days=i)
        key = date.strftime("%Y-%m-%d")
        day_counts = counts.get(key, {"requests": 0, "success": 0, "errors": 0})
        timeline.append({
            "date": key,
            "requests": day_counts["requests"],
            "success": day_counts["success"],
            "errors": day_counts["errors"]
        })

    return timeline


@router.get("/metrics/performance")
async def get_performance_metrics() -> Dict[str, Any]:
    """Get performance metrics"""
    executions = metrics_collector.get_all_executions()
    durations = [e.get("duration_ms", 0) for e in executions if e.get("duration_ms") is not None]
    durations.sort()

    def _percentile(values: list[int], pct: int) -> int:
        if not values:
            return 0
        idx = int(round((pct / 100) * (len(values) - 1)))
        return int(values[max(0, min(idx, len(values) - 1))])

    total = len(executions)
    failed = len([e for e in executions if e.get("status") == "failed"])
    error_rate = round((failed / total) * 100, 1) if total > 0 else 0.0

    # Throughput over last 60 seconds
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=60)
    recent = 0
    for exec_item in executions:
        started_at = exec_item.get("started_at")
        if not started_at:
            continue
        try:
            ts = datetime.fromisoformat(started_at)
        except ValueError:
            continue
        if ts >= window_start:
            recent += 1

    return {
        "response_time": {
            "p50": _percentile(durations, 50),
            "p95": _percentile(durations, 95),
            "p99": _percentile(durations, 99),
            "max": int(durations[-1]) if durations else 0
        },
        "throughput": {
            "requests_per_second": round(recent / 60, 2),
            "concurrent_connections": 0
        },
        "errors": {
            "total": failed,
            "rate": error_rate,
            "by_type": {
                "failed": failed
            }
        }
    }


@router.get("/metrics/recent-activity")
async def get_recent_activity(
    limit: int = Query(default=10, le=50)
) -> List[Dict[str, Any]]:
    """Get recent tool executions for dashboard activity feed"""

    try:
        recent = metrics_collector.get_recent_executions(limit=limit)
        return [
            {
                "execution_id": item.get("execution_id"),
                "tool_name": item.get("tool_name"),
                "status": item.get("status"),
                "started_at": item.get("started_at"),
                "duration_ms": item.get("duration_ms")
            }
            for item in recent
        ]
    except Exception as e:
        logger.error(f"Failed to fetch recent activity: {e}")
        return []


@router.get("/tools/list")
async def get_tools_list(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, le=100)
) -> Dict[str, Any]:
    """Get paginated list of tools"""
    
    try:
        # Get tools from registry
        all_tools = await tool_registry.list_tools(active_only=False)
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
                "bundle_name": tool.bundle_name,
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
        tool = await tool_registry.get_tool(tool_name)
        
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
            "bundle_name": tool.bundle_name,
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
