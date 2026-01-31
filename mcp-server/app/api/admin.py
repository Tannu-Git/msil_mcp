"""
Admin API Endpoints
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.tools.registry import tool_registry
from app.db.repositories import get_metrics, get_recent_executions
from app.core.audit import audit_service
from app.core.auth.oauth2_provider import get_current_user, require_admin
from app.core.auth.models import UserInfo
from app.config import settings

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


# ============================================
# Settings Management Endpoints
# ============================================

class SettingUpdate(BaseModel):
    """Model for updating a setting"""
    value: Any


@router.get("/settings")
async def get_all_settings(current_user: UserInfo = Depends(require_admin)):
    """
    Get all configurable settings (admin only).
    Returns current values from the settings object.
    """
    try:
        return {
            "authentication": {
                "oauth2_enabled": settings.OAUTH2_ENABLED,
                "jwt_algorithm": settings.JWT_ALGORITHM,
                "jwt_access_token_expire_minutes": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
                "jwt_refresh_token_expire_days": settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
            },
            "policy": {
                "opa_enabled": settings.OPA_ENABLED,
                "opa_url": settings.OPA_URL,
            },
            "audit": {
                "audit_enabled": settings.AUDIT_ENABLED,
                "audit_s3_bucket": settings.AUDIT_S3_BUCKET,
                "audit_retention_days": settings.AUDIT_RETENTION_DAYS,
            },
            "resilience": {
                "circuit_breaker_failure_threshold": settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                "circuit_breaker_recovery_timeout": settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
                "retry_max_attempts": settings.RETRY_MAX_ATTEMPTS,
                "retry_exponential_base": settings.RETRY_EXPONENTIAL_BASE,
            },
            "rate_limiting": {
                "rate_limit_enabled": settings.RATE_LIMIT_ENABLED,
                "rate_limit_per_user": settings.RATE_LIMIT_PER_USER,
                "rate_limit_per_tool": settings.RATE_LIMIT_PER_TOOL,
            },
            "batch": {
                "batch_max_concurrency": settings.BATCH_MAX_CONCURRENCY,
                "batch_max_size": settings.BATCH_MAX_SIZE,
            },
            "cache": {
                "redis_enabled": settings.REDIS_ENABLED,
                "redis_url": settings.REDIS_URL,
                "cache_ttl": settings.CACHE_TTL,
            },
            "api_gateway": {
                "api_gateway_mode": settings.API_GATEWAY_MODE,
                "mock_api_base_url": settings.MOCK_API_BASE_URL,
                "msil_apim_base_url": settings.MSIL_APIM_BASE_URL,
            },
            "database": {
                "database_url": _mask_sensitive_url(settings.DATABASE_URL),
                "database_pool_size": settings.DATABASE_POOL_SIZE,
                "database_max_overflow": settings.DATABASE_MAX_OVERFLOW,
            },
            "openai": {
                "openai_model": settings.OPENAI_MODEL,
                "openai_max_tokens": settings.OPENAI_MAX_TOKENS,
            },
            "system": {
                "app_name": settings.APP_NAME,
                "app_version": settings.APP_VERSION,
                "debug": settings.DEBUG,
                "log_level": settings.LOG_LEVEL,
            }
        }
    except Exception as e:
        logger.error(f"Get settings error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings/{category}")
async def get_settings_by_category(
    category: str,
    current_user: UserInfo = Depends(require_admin)
):
    """Get settings for a specific category."""
    all_settings = await get_all_settings(current_user)
    
    if category not in all_settings:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
    
    return all_settings[category]


@router.put("/settings/{category}/{key}")
async def update_setting(
    category: str,
    key: str,
    update: SettingUpdate,
    current_user: UserInfo = Depends(require_admin)
):
    """
    Update a specific setting (admin only).
    
    Note: This updates the runtime value. For persistent changes,
    update the .env file or environment variables.
    """
    try:
        # Map of category.key to settings attribute
        setting_map = {
            "authentication.oauth2_enabled": "OAUTH2_ENABLED",
            "authentication.jwt_access_token_expire_minutes": "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
            "authentication.jwt_refresh_token_expire_days": "JWT_REFRESH_TOKEN_EXPIRE_DAYS",
            "policy.opa_enabled": "OPA_ENABLED",
            "policy.opa_url": "OPA_URL",
            "audit.audit_enabled": "AUDIT_ENABLED",
            "audit.audit_s3_bucket": "AUDIT_S3_BUCKET",
            "audit.audit_retention_days": "AUDIT_RETENTION_DAYS",
            "resilience.circuit_breaker_failure_threshold": "CIRCUIT_BREAKER_FAILURE_THRESHOLD",
            "resilience.circuit_breaker_recovery_timeout": "CIRCUIT_BREAKER_RECOVERY_TIMEOUT",
            "resilience.retry_max_attempts": "RETRY_MAX_ATTEMPTS",
            "resilience.retry_exponential_base": "RETRY_EXPONENTIAL_BASE",
            "rate_limiting.rate_limit_enabled": "RATE_LIMIT_ENABLED",
            "rate_limiting.rate_limit_per_user": "RATE_LIMIT_PER_USER",
            "rate_limiting.rate_limit_per_tool": "RATE_LIMIT_PER_TOOL",
            "batch.batch_max_concurrency": "BATCH_MAX_CONCURRENCY",
            "batch.batch_max_size": "BATCH_MAX_SIZE",
            "cache.redis_enabled": "REDIS_ENABLED",
            "cache.redis_url": "REDIS_URL",
            "cache.cache_ttl": "CACHE_TTL",
            "api_gateway.api_gateway_mode": "API_GATEWAY_MODE",
            "api_gateway.mock_api_base_url": "MOCK_API_BASE_URL",
            "api_gateway.msil_apim_base_url": "MSIL_APIM_BASE_URL",
            "database.database_pool_size": "DATABASE_POOL_SIZE",
            "database.database_max_overflow": "DATABASE_MAX_OVERFLOW",
            "openai.openai_model": "OPENAI_MODEL",
            "openai.openai_max_tokens": "OPENAI_MAX_TOKENS",
            "system.debug": "DEBUG",
            "system.log_level": "LOG_LEVEL",
        }
        
        setting_key = f"{category}.{key}"
        
        if setting_key not in setting_map:
            raise HTTPException(
                status_code=400,
                detail=f"Setting '{setting_key}' is not configurable or does not exist"
            )
        
        attr_name = setting_map[setting_key]
        
        # Validate and update the setting
        try:
            setattr(settings, attr_name, update.value)
            logger.info(f"Setting {attr_name} updated to {update.value} by {current_user.email}")
            
            # Log to audit
            await audit_service.log_config_change(
                user_id=current_user.email,
                config_key=attr_name,
                old_value=None,  # We don't track old value in this simple implementation
                new_value=str(update.value),
                correlation_id=f"config-update-{datetime.utcnow().timestamp()}"
            )
            
            return {
                "success": True,
                "message": f"Setting {setting_key} updated successfully",
                "new_value": update.value,
                "note": "This is a runtime change. Update .env file for persistence."
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid value for {setting_key}: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update setting error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/reset/{category}")
async def reset_category_settings(
    category: str,
    current_user: UserInfo = Depends(require_admin)
):
    """
    Reset all settings in a category to default values.
    
    Note: This requires server restart to load from .env file.
    """
    logger.warning(f"Settings reset requested for category '{category}' by {current_user.email}")
    return {
        "success": False,
        "message": "Settings reset requires server restart and .env file reload",
        "action": "Please restart the server to reload settings from environment"
    }


def _mask_sensitive_url(url: str) -> str:
    """Mask sensitive parts of URLs (passwords, tokens)."""
    if not url or "://" not in url:
        return url
    
    try:
        # Simple masking for postgresql://user:password@host/db
        if "@" in url:
            parts = url.split("@")
            prefix = parts[0]
            suffix = "@".join(parts[1:])
            
            if ":" in prefix:
                protocol_user = prefix.rsplit(":", 1)[0]
                return f"{protocol_user}:***@{suffix}"
        
        return url
    except:
        return url
