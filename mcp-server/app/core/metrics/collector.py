"""
Metrics Collector
Tracks tool execution metrics for analytics and monitoring
"""
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and stores metrics for tool executions"""
    
    def __init__(self):
        self._execution_log: list[Dict[str, Any]] = []
        self._conversation_log: list[Dict[str, Any]] = []
        self._total_conversations = 0
    
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
    
    def log_conversation_start(self, session_id: str, user_id: Optional[str] = None) -> None:
        """
        Log the start of a new conversation
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier (optional)
        """
        conversation = {
            "session_id": session_id,
            "user_id": user_id or "anonymous",
            "started_at": datetime.utcnow().isoformat(),
            "message_count": 0
        }
        self._conversation_log.append(conversation)
        self._total_conversations += 1
        logger.info(f"Conversation started: {session_id}")
    
    def get_conversation_count(self) -> int:
        """Get total number of conversations tracked"""
        return self._total_conversations
    
    def get_metrics_by_timeframe(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get metrics filtered by time window
        
        Args:
            hours: Number of hours to look back (default 24)
            
        Returns:
            Dictionary with metrics for the time window
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_executions = []
        for e in self._execution_log:
            try:
                exec_time = datetime.fromisoformat(e["started_at"].replace("Z", "+00:00"))
                if exec_time >= cutoff_time:
                    recent_executions.append(e)
            except (ValueError, KeyError):
                continue
        
        if not recent_executions:
            return {
                "total_requests": 0,
                "success_rate": 0.0,
                "avg_response_time": 0,
                "timeframe_hours": hours
            }
        
        total = len(recent_executions)
        successful = len([e for e in recent_executions if e["status"] == "success"])
        durations = [e["duration_ms"] for e in recent_executions if "duration_ms" in e]
        avg_duration = sum(durations) // len(durations) if durations else 0
        
        return {
            "total_requests": total,
            "success_rate": round((successful / total) * 100, 1) if total > 0 else 0.0,
            "avg_response_time": avg_duration,
            "timeframe_hours": hours
        }
    
    def get_recent_executions(self, limit: int = 50) -> list[Dict[str, Any]]:
        """Get recent executions"""
        return sorted(
            self._execution_log,
            key=lambda e: e["started_at"],
            reverse=True
        )[:limit]

    def get_all_executions(self) -> list[Dict[str, Any]]:
        """Get all executions (for analytics aggregation)."""
        return list(self._execution_log)
    
    def get_recent_conversations(self, limit: int = 20) -> list[Dict[str, Any]]:
        """Get recent conversations"""
        return sorted(
            self._conversation_log,
            key=lambda c: c["started_at"],
            reverse=True
        )[:limit]
    
    def clear(self):
        """Clear all metrics (for testing)"""
        self._execution_log.clear()
        self._conversation_log.clear()
        self._total_conversations = 0
        logger.info("Metrics cleared")


# Singleton instance
metrics_collector = MetricsCollector()
