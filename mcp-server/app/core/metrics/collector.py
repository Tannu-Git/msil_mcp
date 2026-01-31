"""
Metrics Collector
Tracks tool execution metrics for analytics and monitoring
"""
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and stores metrics for tool executions"""
    
    def __init__(self):
        self._execution_log: list[Dict[str, Any]] = []
    
    @asynccontextmanager
    async def track_execution(self, tool_name: str, arguments: Dict[str, Any]):
        """
        Context manager to track tool execution
        
        Usage:
            async with metrics_collector.track_execution("tool_name", args) as execution_id:
                result = await execute_tool()
                return result
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        execution_record = {
            "execution_id": execution_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "started_at": start_time.isoformat(),
            "status": "running"
        }
        
        try:
            yield execution_id
            
            # Success
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            execution_record.update({
                "completed_at": end_time.isoformat(),
                "duration_ms": duration_ms,
                "status": "success"
            })
            
            self._execution_log.append(execution_record)
            logger.info(f"Tool execution completed: {tool_name} ({duration_ms}ms)")
            
        except Exception as e:
            # Failure
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            execution_record.update({
                "completed_at": end_time.isoformat(),
                "duration_ms": duration_ms,
                "status": "failed",
                "error_message": str(e)
            })
            
            self._execution_log.append(execution_record)
            logger.error(f"Tool execution failed: {tool_name} - {str(e)}")
            raise
    
    def get_tool_metrics(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get aggregated metrics for a tool or all tools
        
        Returns:
            Dictionary with metrics including total calls, success rate, avg duration
        """
        if tool_name:
            executions = [e for e in self._execution_log if e["tool_name"] == tool_name]
        else:
            executions = self._execution_log
        
        if not executions:
            return {
                "total_calls": 0,
                "success_calls": 0,
                "failed_calls": 0,
                "success_rate": 0.0,
                "avg_duration_ms": 0,
                "last_used": None
            }
        
        total = len(executions)
        successful = len([e for e in executions if e["status"] == "success"])
        failed = len([e for e in executions if e["status"] == "failed"])
        
        durations = [e["duration_ms"] for e in executions if "duration_ms" in e]
        avg_duration = sum(durations) // len(durations) if durations else 0
        
        last_execution = max(executions, key=lambda e: e["started_at"])
        
        return {
            "total_calls": total,
            "success_calls": successful,
            "failed_calls": failed,
            "success_rate": round((successful / total) * 100, 1) if total > 0 else 0.0,
            "avg_duration_ms": avg_duration,
            "last_used": last_execution["started_at"]
        }
    
    def get_all_tools_metrics(self) -> list[Dict[str, Any]]:
        """Get metrics for all tools that have been executed"""
        tool_names = set(e["tool_name"] for e in self._execution_log)
        
        metrics = []
        for tool_name in tool_names:
            tool_metrics = self.get_tool_metrics(tool_name)
            tool_metrics["tool_name"] = tool_name
            metrics.append(tool_metrics)
        
        # Sort by total calls descending
        metrics.sort(key=lambda x: x["total_calls"], reverse=True)
        return metrics
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Get summary metrics across all tools"""
        total_executions = len(self._execution_log)
        successful = len([e for e in self._execution_log if e["status"] == "success"])
        failed = len([e for e in self._execution_log if e["status"] == "failed"])
        
        durations = [e["duration_ms"] for e in self._execution_log if "duration_ms" in e]
        avg_duration = sum(durations) // len(durations) if durations else 0
        
        return {
            "total_requests": total_executions,
            "success_rate": round((successful / total_executions) * 100, 1) if total_executions > 0 else 0.0,
            "avg_response_time": avg_duration
        }
    
    def get_recent_executions(self, limit: int = 50) -> list[Dict[str, Any]]:
        """Get recent executions"""
        return sorted(
            self._execution_log,
            key=lambda e: e["started_at"],
            reverse=True
        )[:limit]
    
    def clear(self):
        """Clear all metrics (for testing)"""
        self._execution_log.clear()
        logger.info("Metrics cleared")


# Singleton instance
metrics_collector = MetricsCollector()
