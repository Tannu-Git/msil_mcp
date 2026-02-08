"""
Admin API Endpoints
"""
import logging
import uuid
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.core.tools.registry import tool_registry, Tool
from app.core.policy.engine import policy_engine
from app.core.exposure.manager import exposure_manager
from app.db.repositories import get_metrics, get_recent_executions
from app.core.audit import audit_service
from app.core.auth.oauth2_provider import get_current_user, require_admin
from app.core.auth.models import UserInfo
from app.core.auth.user_manager import user_manager
from app.config import settings
from app.db.database import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter()


class ToolCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=64)
    display_name: str = Field(..., min_length=3, max_length=128)
    description: str = Field(..., min_length=10, max_length=500)
    category: Optional[str] = None
    bundle_name: Optional[str] = None
    api_endpoint: str
    http_method: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    auth_type: Optional[str] = None
    is_active: bool = True
    version: str = "1.0.0"
    risk_level: Optional[str] = None
    requires_elevation: Optional[bool] = None
    requires_confirmation: Optional[bool] = None
    rate_limit_tier: Optional[str] = None


class ToolUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    bundle_name: Optional[str] = None
    api_endpoint: Optional[str] = None
    http_method: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    auth_type: Optional[str] = None
    is_active: Optional[bool] = None
    version: Optional[str] = None
    risk_level: Optional[str] = None
    requires_elevation: Optional[bool] = None
    requires_confirmation: Optional[bool] = None
    rate_limit_tier: Optional[str] = None


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    permissions: List[str] = []


class RolePermissionsUpdate(BaseModel):
    permissions: List[str]


class PermissionUpdate(BaseModel):
    permission: str


class UserRolesUpdate(BaseModel):
    roles: List[str]


class PolicyTestRequest(BaseModel):
    user: str
    action: str
    resource: str


class PolicyContent(BaseModel):
    content: str


class OpenAPIImportRequest(BaseModel):
    spec: Dict[str, Any] = Field(..., description="OpenAPI or Swagger specification")
    tool_names: Optional[List[str]] = Field(None, description="Specific tools to import (if None, imports all)")
    category: str = Field(default="imported", description="Category for imported tools")
    base_url_override: Optional[str] = Field(None, description="Override base URL from spec")


class OpenAPIToolPreview(BaseModel):
    name: str
    display_name: str
    description: str
    http_method: str
    api_endpoint: str
    input_params: List[Dict[str, Any]]
    required_params: List[str]
    security_requirements: List[str]


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
                    "bundle_name": t.bundle_name,
                    "api_endpoint": t.api_endpoint,
                    "http_method": t.http_method,
                    "is_active": t.is_active,
                    "version": t.version,
                    "risk_level": t.risk_level,
                    "requires_elevation": t.requires_elevation,
                    "requires_confirmation": t.requires_confirmation,
                    "rate_limit_tier": t.rate_limit_tier,
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
            "bundle_name": tool.bundle_name,
            "api_endpoint": tool.api_endpoint,
            "http_method": tool.http_method,
            "input_schema": tool.input_schema,
            "output_schema": tool.output_schema,
            "is_active": tool.is_active,
            "version": tool.version,
            "risk_level": tool.risk_level,
            "requires_elevation": tool.requires_elevation,
            "requires_confirmation": tool.requires_confirmation,
            "rate_limit_tier": tool.rate_limit_tier,
            "created_at": tool.created_at.isoformat() if tool.created_at else None,
            "updated_at": tool.updated_at.isoformat() if tool.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get tool error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools")
async def create_tool(
    payload: ToolCreate,
    current_user: UserInfo = Depends(require_admin)
):
    """Create a new tool (admin only)"""
    try:
        existing = await tool_registry.get_tool(payload.name)
        if existing:
            raise HTTPException(status_code=409, detail="Tool already exists")

        tool = Tool(
            id=uuid.uuid4(),
            name=payload.name,
            display_name=payload.display_name,
            description=payload.description,
            category=payload.category or "",
            bundle_name=payload.bundle_name,
            api_endpoint=payload.api_endpoint,
            http_method=payload.http_method,
            input_schema=payload.input_schema,
            output_schema=payload.output_schema,
            headers=payload.headers or {},
            auth_type=payload.auth_type or "none",
            is_active=payload.is_active,
            version=payload.version,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            risk_level=payload.risk_level or "read",
            requires_elevation=payload.requires_elevation or False,
            requires_confirmation=payload.requires_confirmation or False,
            rate_limit_tier=payload.rate_limit_tier or "standard"
        )

        await tool_registry.register_tool(tool)

        try:
            async with get_db_session() as session:
                await session.execute(
                    text(
                        """
                        INSERT INTO tools (
                            name, display_name, description, category,
                            api_endpoint, http_method, input_schema, output_schema,
                            headers, auth_type, is_active, version, created_at, updated_at
                        ) VALUES (
                            :name, :display_name, :description, :category,
                            :api_endpoint, :http_method, :input_schema, :output_schema,
                            :headers, :auth_type, :is_active, :version, :created_at, :updated_at
                        )
                        """
                    ),
                    {
                        "name": tool.name,
                        "display_name": tool.display_name,
                        "description": tool.description,
                        "category": tool.category,
                        "api_endpoint": tool.api_endpoint,
                        "http_method": tool.http_method,
                        "input_schema": tool.input_schema,
                        "output_schema": tool.output_schema,
                        "headers": tool.headers,
                        "auth_type": tool.auth_type,
                        "is_active": tool.is_active,
                        "version": tool.version,
                        "created_at": tool.created_at,
                        "updated_at": tool.updated_at
                    }
                )
        except Exception as db_error:
            logger.warning(f"Tool created in memory but DB insert failed: {db_error}")

        return {
            "success": True,
            "message": "Tool created successfully",
            "tool": {
                "name": tool.name,
                "display_name": tool.display_name,
                "category": tool.category,
                "api_endpoint": tool.api_endpoint,
                "http_method": tool.http_method,
                "is_active": tool.is_active,
                "version": tool.version
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create tool error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tools/{tool_name}")
async def update_tool(
    tool_name: str,
    payload: ToolUpdate,
    current_user: UserInfo = Depends(require_admin)
):
    """Update an existing tool (admin only)"""
    try:
        updates = payload.dict(exclude_unset=True)
        tool = await tool_registry.update_tool(tool_name, updates)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")

        db_fields = {
            "display_name": tool.display_name,
            "description": tool.description,
            "category": tool.category,
            "api_endpoint": tool.api_endpoint,
            "http_method": tool.http_method,
            "input_schema": tool.input_schema,
            "output_schema": tool.output_schema,
            "headers": tool.headers,
            "auth_type": tool.auth_type,
            "is_active": tool.is_active,
            "version": tool.version,
            "updated_at": tool.updated_at
        }

        set_clauses = ", ".join([f"{key} = :{key}" for key in db_fields.keys()])
        try:
            async with get_db_session() as session:
                await session.execute(
                    text(f"UPDATE tools SET {set_clauses} WHERE name = :name"),
                    {**db_fields, "name": tool.name}
                )
        except Exception as db_error:
            logger.warning(f"Tool updated in memory but DB update failed: {db_error}")

        return {
            "success": True,
            "message": "Tool updated successfully",
            "tool": {
                "name": tool.name,
                "display_name": tool.display_name,
                "category": tool.category,
                "api_endpoint": tool.api_endpoint,
                "http_method": tool.http_method,
                "is_active": tool.is_active,
                "version": tool.version,
                "risk_level": tool.risk_level,
                "requires_elevation": tool.requires_elevation,
                "requires_confirmation": tool.requires_confirmation,
                "rate_limit_tier": tool.rate_limit_tier
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update tool error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tools/{tool_name}")
async def delete_tool(
    tool_name: str,
    current_user: UserInfo = Depends(require_admin)
):
    """Deactivate a tool (admin only)"""
    try:
        success = await tool_registry.delete_tool(tool_name)
        if not success:
            raise HTTPException(status_code=404, detail="Tool not found")

        try:
            async with get_db_session() as session:
                await session.execute(
                    text("UPDATE tools SET is_active = false, updated_at = NOW() WHERE name = :name"),
                    {"name": tool_name}
                )
        except Exception as db_error:
            logger.warning(f"Tool deactivated in memory but DB update failed: {db_error}")

        return {
            "success": True,
            "message": "Tool deactivated successfully",
            "tool_name": tool_name
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete tool error: {str(e)}")
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
# Policy Management Endpoints
# ============================================

@router.get("/policies/roles")
async def list_policy_roles(current_user: UserInfo = Depends(require_admin)):
    """List roles and permissions (admin only)"""
    try:
        roles = policy_engine.list_roles()
        return {
            "roles": [
                {
                    "name": role,
                    "permissions": policy_engine.get_role_permissions(role)
                }
                for role in roles
            ],
            "total": len(roles)
        }
    except Exception as e:
        logger.error(f"List policy roles error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/policies/roles")
async def create_policy_role(
    payload: RoleCreate,
    current_user: UserInfo = Depends(require_admin)
):
    """Create a new role (admin only)"""
    try:
        policy_engine.create_role(payload.name, payload.permissions)
        return {
            "success": True,
            "message": "Role created successfully",
            "role": {
                "name": payload.name,
                "permissions": payload.permissions
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Create policy role error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/policies/roles/{role}")
async def update_policy_role_permissions(
    role: str,
    payload: RolePermissionsUpdate,
    current_user: UserInfo = Depends(require_admin)
):
    """Replace permissions for a role (admin only)"""
    try:
        policy_engine.set_role_permissions(role, payload.permissions)
        return {
            "success": True,
            "message": "Role permissions updated",
            "role": {
                "name": role,
                "permissions": payload.permissions
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Update policy role error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/policies/roles/{role}/permissions")
async def add_policy_role_permission(
    role: str,
    payload: PermissionUpdate,
    current_user: UserInfo = Depends(require_admin)
):
    """Add a permission to a role (admin only)"""
    try:
        policy_engine.add_role_permission(role, payload.permission)
        return {
            "success": True,
            "message": "Permission added",
            "role": role,
            "permission": payload.permission
        }
    except Exception as e:
        logger.error(f"Add policy permission error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/policies/roles/{role}/permissions/remove")
async def remove_policy_role_permission(
    role: str,
    payload: PermissionUpdate,
    current_user: UserInfo = Depends(require_admin)
):
    """Remove a permission from a role (admin only)"""
    try:
        policy_engine.remove_role_permission(role, payload.permission)
        return {
            "success": True,
            "message": "Permission removed",
            "role": role,
            "permission": payload.permission
        }
    except Exception as e:
        logger.error(f"Remove policy permission error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/policies/roles/{role}")
async def delete_policy_role(
    role: str,
    current_user: UserInfo = Depends(require_admin)
):
    """Delete a role (admin only)"""
    try:
        policy_engine.delete_role(role)
        return {
            "success": True,
            "message": "Role deleted",
            "role": role
        }
    except Exception as e:
        logger.error(f"Delete policy role error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# User Management Endpoints
# ============================================

@router.get("/users")
async def list_users(current_user: UserInfo = Depends(require_admin)):
    """List all users and their roles (admin only)"""
    try:
        users = user_manager.list_users()
        return {
            "users": users,
            "total": len(users)
        }
    except Exception as e:
        logger.error(f"List users error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{username}")
async def get_user(
    username: str,
    current_user: UserInfo = Depends(require_admin)
):
    """Get user details (admin only)"""
    try:
        user = user_manager.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{username}/roles")
async def update_user_roles(
    username: str,
    payload: UserRolesUpdate,
    current_user: UserInfo = Depends(require_admin)
):
    """Update user roles (admin only)"""
    try:
        # Validate roles exist
        available_roles = policy_engine.list_roles()
        for role in payload.roles:
            if role not in available_roles:
                raise HTTPException(
                    status_code=400,
                    detail=f"Role '{role}' does not exist"
                )
        
        user_manager.set_user_roles(username, payload.roles)
        return {
            "success": True,
            "message": "User roles updated",
            "username": username,
            "roles": payload.roles
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user roles error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roles/{role}/users")
async def get_role_users(
    role: str,
    current_user: UserInfo = Depends(require_admin)
):
    """Get all users with a specific role (admin only)"""
    try:
        users = user_manager.get_users_by_role(role)
        return {
            "role": role,
            "users": users,
            "total": len(users)
        }
    except Exception as e:
        logger.error(f"Get role users error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# OPA Policy Management Endpoints
# ============================================

@router.get("/opa/policies/{policy_name}")
async def get_opa_policy(
    policy_name: str,
    current_user: UserInfo = Depends(require_admin)
):
    """Get OPA policy content (admin only)"""
    try:
        from pathlib import Path
        
        # Security: Only allow specific policy names
        allowed_policies = ["authz"]
        if policy_name not in allowed_policies:
            raise HTTPException(status_code=400, detail="Invalid policy name")
        
        policy_path = Path(__file__).parent.parent / "core" / "policy" / "rego" / f"{policy_name}.rego"
        
        if not policy_path.exists():
            raise HTTPException(status_code=404, detail="Policy file not found")
        
        with open(policy_path, 'r') as f:
            content = f.read()
        
        return {
            "policy_name": policy_name,
            "content": content,
            "path": str(policy_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get OPA policy error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/opa/policies/{policy_name}")
async def update_opa_policy(
    policy_name: str,
    payload: PolicyContent,
    current_user: UserInfo = Depends(require_admin)
):
    """Update OPA policy content (admin only)"""
    try:
        from pathlib import Path
        
        # Security: Only allow specific policy names
        allowed_policies = ["authz"]
        if policy_name not in allowed_policies:
            raise HTTPException(status_code=400, detail="Invalid policy name")
        
        policy_path = Path(__file__).parent.parent / "core" / "policy" / "rego" / f"{policy_name}.rego"
        
        # Backup existing policy
        if policy_path.exists():
            backup_path = policy_path.with_suffix('.rego.backup')
            import shutil
            shutil.copy(policy_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
        
        # Write new policy
        with open(policy_path, 'w') as f:
            f.write(payload.content)
        
        logger.info(f"Updated OPA policy: {policy_name}")
        
        return {
            "success": True,
            "message": "Policy updated successfully",
            "policy_name": policy_name
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update OPA policy error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/opa/policies/test")
async def test_opa_policy(
    payload: PolicyTestRequest,
    current_user: UserInfo = Depends(require_admin)
):
    """Test OPA policy decision (admin only)"""
    try:
        # Get user roles
        roles = user_manager.get_user_roles(payload.user)
        
        # Create policy decision input
        decision_input = {
            "user": payload.user,
            "roles": roles,
            "action": payload.action,
            "resource": payload.resource,
            "tool": payload.resource  # Alias for compatibility
        }
        
        # Test with policy engine
        result = await policy_engine.evaluate(
            user=payload.user,
            action=payload.action,
            resource=payload.resource,
            context={"roles": roles}
        )
        
        return {
            "allowed": result,
            "user": payload.user,
            "roles": roles,
            "action": payload.action,
            "resource": payload.resource,
            "engine": "OPA" if policy_engine.opa_enabled else "Simple RBAC"
        }
    except Exception as e:
        logger.error(f"Test OPA policy error: {str(e)}")
        return {
            "allowed": False,
            "error": str(e),
            "user": payload.user,
            "action": payload.action,
            "resource": payload.resource
        }


@router.post("/test-authz")
async def test_authorization(
    payload: PolicyTestRequest,
    current_user: UserInfo = Depends(require_admin)
):
    """Test authorization decision (admin only) - Used by Test Authorization page"""
    try:
        # Get user roles
        roles = user_manager.get_user_roles(payload.user)
        if not roles:
            # If user doesn't exist, use default "user" role for testing
            roles = ["user"]
        
        # Test with policy engine
        result = await policy_engine.evaluate(
            user=payload.user,
            action=payload.action,
            resource=payload.resource,
            context={"roles": roles}
        )
        
        # Get detailed reason if available
        reason = f"User has roles: {', '.join(roles)}. "
        if result:
            reason += f"Policy engine ({('OPA' if policy_engine.opa_enabled else 'Simple RBAC')}) allowed the action."
        else:
            reason += f"Policy engine ({('OPA' if policy_engine.opa_enabled else 'Simple RBAC')}) denied the action."
        
        return {
            "allowed": result,
            "user": payload.user,
            "roles": roles,
            "action": payload.action,
            "resource": payload.resource,
            "engine": "OPA" if policy_engine.opa_enabled else "Simple RBAC",
            "reason": reason
        }
    except Exception as e:
        logger.error(f"Test authorization error: {str(e)}")
        return {
            "allowed": False,
            "error": str(e),
            "user": payload.user,
            "action": payload.action,
            "resource": payload.resource
        }


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


@router.post("/tools/import/preview")
async def preview_openapi_import(
    request: OpenAPIImportRequest,
    current_user: UserInfo = Depends(require_admin)
):
    """
    Preview tools that will be created from OpenAPI/Swagger spec.
    Supports Swagger 2.0 and OpenAPI 3.x
    """
    try:
        spec = request.spec
        swagger_version = spec.get("swagger", spec.get("openapi", "unknown"))
        
        logger.info(f"Previewing OpenAPI import: version={swagger_version}")
        
        # Determine if Swagger 2.0 or OpenAPI 3.x
        is_swagger_2 = "swagger" in spec and spec["swagger"].startswith("2.")
        
        # Extract base URL
        if request.base_url_override:
            base_url = request.base_url_override
        elif is_swagger_2:
            # Swagger 2.0: host + basePath
            host = spec.get("host", "")
            base_path = spec.get("basePath", "")
            schemes = spec.get("schemes", ["https"])
            base_url = f"{schemes[0]}://{host}{base_path}" if host else ""
        else:
            # OpenAPI 3.x: servers[0].url
            servers = spec.get("servers", [])
            base_url = servers[0]["url"] if servers else ""
        
        # Parse paths
        paths = spec.get("paths", {})
        definitions = spec.get("definitions", spec.get("components", {}).get("schemas", {}))
        
        tools_preview = []
        
        for path, path_item in paths.items():
            for method in ["get", "post", "put", "delete", "patch"]:
                if method not in path_item:
                    continue
                
                operation = path_item[method]
                
                # Generate tool name from operationId or path
                operation_id = operation.get("operationId")
                if not operation_id:
                    # Generate from path: /v1/api/common/msil/dms/appointment-booking -> appointment_booking
                    tool_name = path.split("/")[-1].replace("-", "_")
                else:
                    tool_name = operation_id.replace("-", "_")
                
                # Filter by tool_names if specified
                if request.tool_names and tool_name not in request.tool_names and path not in request.tool_names:
                    continue
                
                # Extract parameters
                parameters = operation.get("parameters", [])
                input_params = []
                required_params = []
                
                for param in parameters:
                    param_info = {
                        "name": param.get("name"),
                        "location": param.get("in"),  # query, header, path, body
                        "type": param.get("type", "string"),
                        "description": param.get("description", ""),
                        "required": param.get("required", False)
                    }
                    
                    # Handle body parameter (Swagger 2.0)
                    if param.get("in") == "body" and "schema" in param:
                        schema = param["schema"]
                        if "$ref" in schema:
                            # Reference to definitions
                            ref_name = schema["$ref"].split("/")[-1]
                            if ref_name in definitions:
                                param_info["schema"] = definitions[ref_name]
                        else:
                            param_info["schema"] = schema
                    
                    input_params.append(param_info)
                    
                    if param.get("required"):
                        required_params.append(param.get("name"))
                
                # Extract security requirements
                security = operation.get("security", spec.get("security", []))
                security_requirements = []
                for sec_req in security:
                    security_requirements.extend(list(sec_req.keys()))
                
                # Create preview
                tool_preview = OpenAPIToolPreview(
                    name=tool_name,
                    display_name=operation.get("summary", tool_name.replace("_", " ").title()),
                    description=operation.get("description", operation.get("summary", "")),
                    http_method=method.upper(),
                    api_endpoint=path,
                    input_params=input_params,
                    required_params=required_params,
                    security_requirements=security_requirements
                )
                
                tools_preview.append(tool_preview.dict())
        
        logger.info(f"Preview generated: {len(tools_preview)} tools")
        
        return {
            "success": True,
            "spec_version": swagger_version,
            "base_url": base_url,
            "total_endpoints": len(paths),
            "tools_count": len(tools_preview),
            "tools": tools_preview
        }
    
    except Exception as e:
        logger.error(f"OpenAPI preview error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Failed to parse OpenAPI spec: {str(e)}")


@router.post("/tools/import/execute")
async def execute_openapi_import(
    request: OpenAPIImportRequest,
    current_user: UserInfo = Depends(require_admin)
):
    """
    Import and register tools from OpenAPI/Swagger spec.
    Creates tools in database and tool registry.
    """
    try:
        spec = request.spec
        is_swagger_2 = "swagger" in spec and spec["swagger"].startswith("2.")
        
        # Extract base URL
        if request.base_url_override:
            base_url = request.base_url_override
        elif is_swagger_2:
            host = spec.get("host", "")
            base_path = spec.get("basePath", "")
            schemes = spec.get("schemes", ["https"])
            base_url = f"{schemes[0]}://{host}{base_path}" if host else ""
        else:
            servers = spec.get("servers", [])
            base_url = servers[0]["url"] if servers else ""
        
        # Parse and create tools
        paths = spec.get("paths", {})
        definitions = spec.get("definitions", spec.get("components", {}).get("schemas", {}))
        
        created_tools = []
        errors = []
        
        async with get_db_session() as session:
            for path, path_item in paths.items():
                for method in ["get", "post", "put", "delete", "patch"]:
                    if method not in path_item:
                        continue
                    
                    operation = path_item[method]
                    
                    # Generate tool name
                    operation_id = operation.get("operationId")
                    if not operation_id:
                        tool_name = path.split("/")[-1].replace("-", "_")
                    else:
                        tool_name = operation_id.replace("-", "_")
                    
                    # Filter by tool_names if specified
                    if request.tool_names and tool_name not in request.tool_names and path not in request.tool_names:
                        continue
                    
                    try:
                        # Build input schema
                        properties = {}
                        required = []
                        
                        for param in operation.get("parameters", []):
                            param_name = param.get("name")
                            param_in = param.get("in")
                            
                            if param_in == "body" and "schema" in param:
                                # Handle body schema
                                schema = param["schema"]
                                if "$ref" in schema:
                                    ref_name = schema["$ref"].split("/")[-1]
                                    if ref_name in definitions:
                                        def_schema = definitions[ref_name]
                                        properties.update(def_schema.get("properties", {}))
                                        required.extend(def_schema.get("required", []))
                                else:
                                    properties.update(schema.get("properties", {}))
                                    required.extend(schema.get("required", []))
                            else:
                                # Handle other parameters
                                properties[param_name] = {
                                    "type": param.get("type", "string"),
                                    "description": param.get("description", ""),
                                    "in": param_in
                                }
                                
                                if param.get("required"):
                                    required.append(param_name)
                        
                        input_schema = {
                            "type": "object",
                            "properties": properties,
                            "required": required
                        }
                        
                        # Extract security
                        security = operation.get("security", spec.get("security", []))
                        auth_type = "api_key"
                        headers = {}
                        
                        if security:
                            for sec_req in security:
                                sec_schemes = spec.get("securityDefinitions", spec.get("components", {}).get("securitySchemes", {}))
                                for sec_name in sec_req.keys():
                                    if sec_name in sec_schemes:
                                        sec_def = sec_schemes[sec_name]
                                        if sec_def.get("type") == "apiKey":
                                            header_name = sec_def.get("name", "x-api-key")
                                            headers[header_name] = "${API_KEY}"
                                        if sec_def.get("type") == "oauth2" or "authorization" in sec_name.lower():
                                            headers["Authorization"] = "Bearer ${TOKEN}"
                        
                        # Create tool
                        tool_id = uuid.uuid4()
                        tool_data = {
                            "id": tool_id,
                            "name": tool_name,
                            "display_name": operation.get("summary", tool_name.replace("_", " ").title()),
                            "description": operation.get("description", operation.get("summary", ""))[:500],
                            "category": request.category,
                            "api_endpoint": path,
                            "http_method": method.upper(),
                            "input_schema": input_schema,
                            "output_schema": None,
                            "headers": headers,
                            "auth_type": auth_type,
                            "is_active": True,
                            "version": "1.0.0",
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                        
                        # Insert into database
                        result = await session.execute(
                            text("""
                                INSERT INTO tools 
                                (id, name, display_name, description, category, api_endpoint, 
                                http_method, input_schema, output_schema, headers, auth_type, 
                                is_active, version, created_at, updated_at)
                                VALUES 
                                (:id, :name, :display_name, :description, :category, :api_endpoint,
                                :http_method, :input_schema::jsonb, :output_schema::jsonb, :headers::jsonb, :auth_type,
                                :is_active, :version, :created_at, :updated_at)
                                ON CONFLICT (name) DO UPDATE SET
                                    display_name = EXCLUDED.display_name,
                                    description = EXCLUDED.description,
                                    api_endpoint = EXCLUDED.api_endpoint,
                                    http_method = EXCLUDED.http_method,
                                    input_schema = EXCLUDED.input_schema,
                                    headers = EXCLUDED.headers,
                                    updated_at = EXCLUDED.updated_at
                                RETURNING id
                            """),
                            {
                                **tool_data,
                                "input_schema": json.dumps(tool_data["input_schema"]),
                                "output_schema": json.dumps(tool_data["output_schema"]),
                                "headers": json.dumps(tool_data["headers"])
                            }
                        )
                        await session.commit()
                        
                        # Register in tool registry
                        tool_obj = Tool(**tool_data)
                        await tool_registry.register_tool(tool_obj)
                        
                        created_tools.append(tool_name)
                        logger.info(f"Imported tool: {tool_name}")
                    
                    except Exception as e:
                        error_msg = f"Failed to import {tool_name}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
        
        # Log audit
        await audit_service.log_admin_action(
            user_id=current_user.email,
            action="import_openapi_tools",
            resource=f"tools_import_{len(created_tools)}",
            details={"tools": created_tools, "errors": errors},
            correlation_id=f"import-{datetime.utcnow().timestamp()}"
        )
        
        return {
            "success": True,
            "message": f"Successfully imported {len(created_tools)} tools",
            "created_tools": created_tools,
            "errors": errors if errors else None,
            "base_url": base_url
        }
    
    except Exception as e:
        logger.error(f"OpenAPI import execution error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


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


# ============================================
# PHASE 1: Exposure Governance Admin APIs
# ============================================

@router.get("/exposure/roles")
async def get_role_exposure_permissions(
    role_name: str = Query(..., description="Role name to get exposure permissions for"),
    current_user: UserInfo = Depends(require_admin)
):
    """
    Get all exposure permissions for a specific role.
    
    Returns list of permissions like:
    - expose:bundle:Service Booking
    - expose:tool:resolve_customer
    - expose:all (for admin)
    """
    try:
        async with get_db_session() as session:
            result = await session.execute(
                text("""
                    SELECT DISTINCT prp.permission
                    FROM policy_roles pr
                    JOIN policy_role_permissions prp ON pr.id = prp.role_id
                    WHERE pr.name = :role_name
                    AND prp.permission LIKE 'expose:%'
                    ORDER BY prp.permission
                """),
                {"role_name": role_name}
            )
            rows = result.fetchall()
            permissions = [row[0] for row in rows]
            
            logger.info(f"Admin {current_user.user_id} queried exposure permissions for role '{role_name}'")
            
            return {
                "role": role_name,
                "permissions": permissions,
                "count": len(permissions)
            }
    except Exception as e:
        logger.error(f"Failed to get exposure permissions for role {role_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch exposure permissions")


@router.post("/exposure/roles/{role_name}/permissions")
async def add_exposure_permission(
    role_name: str,
    payload: PermissionUpdate,
    current_user: UserInfo = Depends(require_admin)
):
    """
    Add exposure permission to a role.
    
    Permission format:
    - expose:bundle:{bundle_name}  e.g., expose:bundle:Service Booking
    - expose:tool:{tool_name}      e.g., expose:tool:resolve_customer
    - expose:all                   (admin only)
    """
    try:
        permission = payload.permission
        
        # Validate permission format
        if not permission.startswith("expose:"):
            raise HTTPException(status_code=400, detail="Invalid permission format (must start with 'expose:')")
        
        async with get_db_session() as session:
            # Get role
            role_result = await session.execute(
                text("SELECT id FROM policy_roles WHERE name = :name"),
                {"name": role_name}
            )
            role_row = role_result.first()
            
            if not role_row:
                raise HTTPException(status_code=404, detail=f"Role '{role_name}' not found")
            
            role_id = role_row[0]
            
            # Check if permission already exists
            existing = await session.execute(
                text("SELECT id FROM policy_role_permissions WHERE role_id = :role_id AND permission = :permission"),
                {"role_id": role_id, "permission": permission}
            )
            
            if existing.first():
                logger.info(f"Permission '{permission}' already exists for role '{role_name}'")
                return {
                    "message": "Permission already exists",
                    "role": role_name,
                    "permission": permission
                }
            
            # Add permission
            await session.execute(
                text("""
                    INSERT INTO policy_role_permissions (role_id, permission, created_at)
                    VALUES (:role_id, :permission, NOW())
                """),
                {"role_id": role_id, "permission": permission}
            )
            await session.commit()
            
            # Invalidate exposure cache
            exposure_manager.invalidate_cache(role_name)
            
            # Audit log
            await audit_service.log_event(
                action="exposure_permission_added",
                user_id=current_user.user_id,
                details={
                    "role": role_name,
                    "permission": permission,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Admin {current_user.user_id} added exposure permission '{permission}' to role '{role_name}'")
            
            return {
                "message": "Permission added successfully",
                "role": role_name,
                "permission": permission
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add exposure permission: {e}")
        raise HTTPException(status_code=500, detail="Failed to add exposure permission")


@router.delete("/exposure/roles/{role_name}/permissions")
async def remove_exposure_permission(
    role_name: str,
    permission: str = Query(..., description="Permission to remove"),
    current_user: UserInfo = Depends(require_admin)
):
    """
    Remove exposure permission from a role.
    """
    try:
        async with get_db_session() as session:
            # Get role
            role_result = await session.execute(
                text("SELECT id FROM policy_roles WHERE name = :name"),
                {"name": role_name}
            )
            role_row = role_result.first()
            
            if not role_row:
                raise HTTPException(status_code=404, detail=f"Role '{role_name}' not found")
            
            role_id = role_row[0]
            
            # Delete permission
            result = await session.execute(
                text("DELETE FROM policy_role_permissions WHERE role_id = :role_id AND permission = :permission"),
                {"role_id": role_id, "permission": permission}
            )
            
            if result.rowcount == 0:
                logger.info(f"Permission '{permission}' not found for role '{role_name}'")
                raise HTTPException(status_code=404, detail="Permission not found")
            
            await session.commit()
            
            # Invalidate exposure cache
            exposure_manager.invalidate_cache(role_name)
            
            # Audit log
            await audit_service.log_event(
                action="exposure_permission_removed",
                user_id=current_user.user_id,
                details={
                    "role": role_name,
                    "permission": permission,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Admin {current_user.user_id} removed exposure permission '{permission}' from role '{role_name}'")
            
            return {
                "message": "Permission removed successfully",
                "role": role_name,
                "permission": permission
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove exposure permission: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove exposure permission")


@router.get("/exposure/bundles")
async def list_available_bundles(
    current_user: UserInfo = Depends(require_admin)
):
    """
    List all unique bundles from tools table.
    
    Returns available bundles that can be assigned to roles via exposure permissions.
    """
    try:
        async with get_db_session() as session:
            result = await session.execute(
                text("""
                    SELECT DISTINCT bundle_name
                    FROM tools
                    WHERE is_active = true
                    AND bundle_name IS NOT NULL
                    ORDER BY bundle_name
                """)
            )
            rows = result.fetchall()
            bundles = [row[0] for row in rows if row[0]]
            
            logger.debug(f"Listing {len(bundles)} available bundles")
            
            return {
                "bundles": bundles,
                "count": len(bundles)
            }
    except Exception as e:
        logger.error(f"Failed to list available bundles: {e}")
        raise HTTPException(status_code=500, detail="Failed to list bundles")


@router.get("/exposure/preview")
async def preview_role_exposure(
    role_name: str = Query(..., description="Role name to preview exposure for"),
    current_user: UserInfo = Depends(require_admin)
):
    """
    Preview what tools a role can see based on current exposure permissions.
    
    This shows the actual tools that would be returned by tools/list for users with this role.
    Useful for admin verification before deployment.
    """
    try:
        # Get all active tools
        all_tools = await tool_registry.list_tools()
        
        # Get exposure rules for role
        exposed_tools = await exposure_manager.filter_tools(
            all_tools,
            user_id=f"preview-{role_name}",
            roles=[role_name]
        )
        
        # Build response with correct structure
        tool_list = []
        bundles_set = set()
        
        for tool in exposed_tools:
            tool_list.append({
                "id": tool.id or "",
                "name": tool.name,
                "display_name": tool.display_name,
                "description": tool.description or "",
                "bundle_name": tool.bundle_name,
                "category": tool.category
            })
            bundles_set.add(tool.bundle_name)
        
        logger.info(f"Admin {current_user.user_id} previewed exposure for role '{role_name}': {len(tool_list)} tools in {len(bundles_set)} bundles")
        
        return {
            "role_name": role_name,
            "total_exposed_tools": len(tool_list),
            "exposed_bundles": sorted(list(bundles_set)),
            "exposed_tools": sorted(tool_list, key=lambda t: t["display_name"])
        }
    
    except Exception as e:
        logger.error(f"Failed to preview role exposure: {e}")
        raise HTTPException(status_code=500, detail="Failed to preview exposure")
