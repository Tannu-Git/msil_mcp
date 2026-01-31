"""
Monitoring and Observability Service
Provides Prometheus metrics, health checks, and performance monitoring
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from typing import Dict, Any
import time
import psutil
import logging

logger = logging.getLogger(__name__)

# Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

mcp_tool_calls_total = Counter(
    'mcp_tool_calls_total',
    'Total MCP tool calls',
    ['tool_name', 'status']
)

mcp_tool_duration_seconds = Histogram(
    'mcp_tool_duration_seconds',
    'MCP tool execution duration in seconds',
    ['tool_name']
)

openai_requests_total = Counter(
    'openai_requests_total',
    'Total OpenAI API requests',
    ['model', 'status']
)

openai_tokens_used = Counter(
    'openai_tokens_used',
    'Total OpenAI tokens used',
    ['model', 'token_type']
)

openai_request_duration_seconds = Histogram(
    'openai_request_duration_seconds',
    'OpenAI API request duration in seconds',
    ['model']
)

database_connections_active = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

redis_connections_active = Gauge(
    'redis_connections_active',
    'Number of active Redis connections'
)

chat_sessions_active = Gauge(
    'chat_sessions_active',
    'Number of active chat sessions'
)

system_cpu_usage = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

system_memory_usage = Gauge(
    'system_memory_usage_percent',
    'System memory usage percentage'
)


class MonitoringService:
    """Service for monitoring and metrics collection"""
    
    def __init__(self):
        self.start_time = time.time()
    
    def get_metrics(self) -> Response:
        """Generate Prometheus metrics"""
        # Update system metrics
        self.update_system_metrics()
        
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            system_cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            system_memory_usage.set(memory.percent)
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float
    ):
        """Record HTTP request metrics"""
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_tool_call(
        self,
        tool_name: str,
        success: bool,
        duration: float
    ):
        """Record MCP tool call metrics"""
        status = "success" if success else "failure"
        mcp_tool_calls_total.labels(
            tool_name=tool_name,
            status=status
        ).inc()
        
        mcp_tool_duration_seconds.labels(
            tool_name=tool_name
        ).observe(duration)
    
    def record_openai_request(
        self,
        model: str,
        success: bool,
        duration: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0
    ):
        """Record OpenAI API request metrics"""
        status = "success" if success else "failure"
        openai_requests_total.labels(
            model=model,
            status=status
        ).inc()
        
        openai_request_duration_seconds.labels(
            model=model
        ).observe(duration)
        
        if prompt_tokens > 0:
            openai_tokens_used.labels(
                model=model,
                token_type="prompt"
            ).inc(prompt_tokens)
        
        if completion_tokens > 0:
            openai_tokens_used.labels(
                model=model,
                token_type="completion"
            ).inc(completion_tokens)
    
    def set_database_connections(self, count: int):
        """Set active database connections count"""
        database_connections_active.set(count)
    
    def set_redis_connections(self, count: int):
        """Set active Redis connections count"""
        redis_connections_active.set(count)
    
    def set_active_sessions(self, count: int):
        """Set active chat sessions count"""
        chat_sessions_active.set(count)
    
    def get_uptime(self) -> float:
        """Get service uptime in seconds"""
        return time.time() - self.start_time
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        uptime = self.get_uptime()
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "status": "healthy",
            "uptime_seconds": uptime,
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024 * 1024 * 1024)
            },
            "process": {
                "pid": psutil.Process().pid,
                "memory_mb": psutil.Process().memory_info().rss / (1024 * 1024),
                "num_threads": psutil.Process().num_threads()
            }
        }
    
    async def get_readiness_status(
        self,
        db_healthy: bool,
        redis_healthy: bool
    ) -> Dict[str, Any]:
        """Get readiness status"""
        ready = db_healthy and redis_healthy
        
        return {
            "status": "ready" if ready else "not_ready",
            "checks": {
                "database": "healthy" if db_healthy else "unhealthy",
                "redis": "healthy" if redis_healthy else "unhealthy"
            }
        }


# Global monitoring service instance
monitoring_service = MonitoringService()
