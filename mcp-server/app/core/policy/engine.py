"""Policy engine for RBAC and authorization with OPA integration."""

import logging
import httpx
from typing import Dict, Any, List, Optional

from .models import PolicyDecision, PolicyRule
from .risk_policy import risk_policy_manager, RiskPolicyManager
from app.config import settings

logger = logging.getLogger(__name__)


class PolicyEngine:
    """Policy engine for authorization with OPA integration."""
    
    def __init__(
        self,
        opa_url: str = None,
        fallback_to_simple: bool = True,
        risk_manager: Optional[RiskPolicyManager] = None
    ):
        """Initialize policy engine.
        
        Args:
            opa_url: OPA server URL
            fallback_to_simple: If True, use simple RBAC when OPA unavailable
            risk_manager: Risk policy manager for tool risk enforcement
        """
        self.opa_url = opa_url or settings.OPA_URL
        self.fallback_to_simple = fallback_to_simple
        self.opa_enabled = settings.OPA_ENABLED
        self.risk_manager = risk_manager or risk_policy_manager
        
        # Simple RBAC rules (fallback when OPA not available)
        self.simple_rules = self._initialize_simple_rules()
        
        logger.info(f"Policy engine initialized (OPA: {self.opa_enabled}, URL: {self.opa_url})")
    
    def _initialize_simple_rules(self) -> Dict[str, List[str]]:
        """Initialize simple role-based rules as fallback."""
        return {
            "admin": ["*"],  # Admin can do everything
            "developer": [
                "invoke:*",
                "read:*",
                "write:tool",
                "write:config"
            ],
            "operator": [
                "invoke:*",
                "read:*"
            ],
            "user": [
                "invoke:allowed_tools",
                "read:tool"
            ]
        }
    
    async def evaluate(
        self,
        action: str,
        resource: str,
        context: Dict[str, Any]
    ) -> PolicyDecision:
        """Evaluate policy for an action on a resource.
        
        Args:
            action: Action being performed (invoke, read, write, delete)
            resource: Resource being accessed (tool name, config, etc.)
            context: Context including user, roles, etc.
            
        Returns:
            PolicyDecision with allowed/denied and reason
        """
        roles = context.get("roles", [])
        user_id = context.get("user_id", "anonymous")
        
        logger.debug(f"Policy evaluation: {action}:{resource} for user {user_id} with roles {roles}")
        
        # Check tool risk policy if tool context provided
        tool = context.get("tool")
        if tool and hasattr(tool, 'risk_level'):
            risk_decision = self._evaluate_risk_policy(tool, context)
            if not risk_decision["allowed"]:
                return PolicyDecision(
                    allowed=False,
                    reason=risk_decision["reason"],
                    policies_evaluated=["risk_policy"],
                    metadata=risk_decision
                )
        
        # Try OPA first if enabled
        if self.opa_enabled:
            try:
                decision = await self._evaluate_opa(action, resource, context)
                logger.info(f"OPA decision: {decision.allowed} - {decision.reason}")
                return decision
            except Exception as e:
                logger.warning(f"OPA evaluation failed: {str(e)}, falling back to simple RBAC")
                if not self.fallback_to_simple:
                    return PolicyDecision(
                        allowed=False,
                        reason=f"Policy engine error: {str(e)}",
                        policies_evaluated=[]
                    )
        
        # Fallback to simple RBAC
        decision = self._evaluate_simple(action, resource, roles)
        logger.info(f"Simple RBAC decision: {decision.allowed} - {decision.reason}")
        return decision
    
    def _evaluate_risk_policy(
        self,
        tool: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate risk-based policy for tool.
        
        Args:
            tool: Tool object with risk attributes
            context: Request context
            
        Returns:
            Risk evaluation result
        """
        # Get user role (use first role if multiple)
        roles = context.get("roles", [])
        user_role = roles[0] if roles else "user"
        
        # Check if user is elevated (from PIM/PAM)
        is_elevated = context.get("is_elevated", False)
        
        # Evaluate access based on tool risk
        risk_result = self.risk_manager.evaluate_access(
            tool_risk_level=tool.risk_level,
            user_role=user_role,
            is_elevated=is_elevated
        )
        
        logger.info(
            f"Risk policy for {tool.name} (risk={tool.risk_level}): "
            f"allowed={risk_result['allowed']}, reason={risk_result['reason']}"
        )
        
        return risk_result
    
    async def _evaluate_opa(
        self,
        action: str,
        resource: str,
        context: Dict[str, Any]
    ) -> PolicyDecision:
        """Evaluate policy using OPA.
        
        Args:
            action: Action being performed
            resource: Resource being accessed
            context: Context for policy evaluation
            
        Returns:
            PolicyDecision from OPA
        """
        input_data = {
            "input": {
                "action": action,
                "resource": resource,
                "user": context.get("user_id"),
                "roles": context.get("roles", []),
                "timestamp": context.get("timestamp"),
                "metadata": context.get("metadata", {})
            }
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{self.opa_url}/v1/data/msil/authz/allow",
                json=input_data
            )
            response.raise_for_status()
            result = response.json()
        
        allowed = result.get("result", False)
        
        return PolicyDecision(
            allowed=allowed,
            reason=result.get("reason", "Policy decision from OPA"),
            policies_evaluated=result.get("policies", ["msil.authz.allow"]),
            metadata=result
        )
    
    def _evaluate_simple(
        self,
        action: str,
        resource: str,
        roles: List[str]
    ) -> PolicyDecision:
        """Evaluate using simple RBAC rules.
        
        Args:
            action: Action being performed
            resource: Resource being accessed
            roles: User roles
            
        Returns:
            PolicyDecision based on simple rules
        """
        if not roles:
            return PolicyDecision(
                allowed=False,
                reason="No roles assigned to user",
                policies_evaluated=["simple_rbac"]
            )
        
        # Check each role
        for role in roles:
            role_permissions = self.simple_rules.get(role, [])
            
            # Check for wildcard permission
            if "*" in role_permissions:
                return PolicyDecision(
                    allowed=True,
                    reason=f"Role '{role}' has wildcard permission",
                    policies_evaluated=["simple_rbac"]
                )
            
            # Check for exact permission match
            permission = f"{action}:{resource}"
            if permission in role_permissions:
                return PolicyDecision(
                    allowed=True,
                    reason=f"Role '{role}' has permission '{permission}'",
                    policies_evaluated=["simple_rbac"]
                )
            
            # Check for wildcard action
            wildcard_permission = f"{action}:*"
            if wildcard_permission in role_permissions:
                return PolicyDecision(
                    allowed=True,
                    reason=f"Role '{role}' has permission '{wildcard_permission}'",
                    policies_evaluated=["simple_rbac"]
                )
        
        return PolicyDecision(
            allowed=False,
            reason=f"No matching permission for action '{action}' on resource '{resource}'",
            policies_evaluated=["simple_rbac"]
        )
    
    async def check_tool_access(
        self,
        user_roles: List[str],
        tool_name: str,
        action: str = "invoke"
    ) -> bool:
        """Check if user roles have access to invoke a tool.
        
        Args:
            user_roles: List of user roles
            tool_name: Name of the tool
            action: Action to perform (default: invoke)
            
        Returns:
            True if access allowed, False otherwise
        """
        decision = await self.evaluate(
            action=action,
            resource=tool_name,
            context={"roles": user_roles}
        )
        return decision.allowed
    
    def get_role_permissions(self, role: str) -> List[str]:
        """Get permissions for a role.
        
        Args:
            role: Role name
            
        Returns:
            List of permissions
        """
        return self.simple_rules.get(role, [])
    
    def add_role_permission(self, role: str, permission: str):
        """Add permission to a role.
        
        Args:
            role: Role name
            permission: Permission to add (format: action:resource)
        """
        if role not in self.simple_rules:
            self.simple_rules[role] = []
        
        if permission not in self.simple_rules[role]:
            self.simple_rules[role].append(permission)
            logger.info(f"Added permission '{permission}' to role '{role}'")
    
    def remove_role_permission(self, role: str, permission: str):
        """Remove permission from a role.
        
        Args:
            role: Role name
            permission: Permission to remove
        """
        if role in self.simple_rules and permission in self.simple_rules[role]:
            self.simple_rules[role].remove(permission)
            logger.info(f"Removed permission '{permission}' from role '{role}'")
    
    def list_roles(self) -> List[str]:
        """List all available roles.
        
        Returns:
            List of role names
        """
        return list(self.simple_rules.keys())

    def create_role(self, role: str, permissions: Optional[List[str]] = None):
        """Create a new role.
        
        Args:
            role: Role name
            permissions: Optional initial permissions
        """
        if role in self.simple_rules:
            raise ValueError(f"Role '{role}' already exists")
        self.simple_rules[role] = permissions or []
        logger.info(f"Created role '{role}'")

    def set_role_permissions(self, role: str, permissions: List[str]):
        """Replace permissions for a role.
        
        Args:
            role: Role name
            permissions: Full list of permissions
        """
        if role not in self.simple_rules:
            raise ValueError(f"Role '{role}' does not exist")
        self.simple_rules[role] = permissions
        logger.info(f"Updated permissions for role '{role}'")

    def delete_role(self, role: str):
        """Delete a role.
        
        Args:
            role: Role name
        """
        if role in self.simple_rules:
            del self.simple_rules[role]
            logger.info(f"Deleted role '{role}'")


# Global policy engine instance
policy_engine = PolicyEngine()
