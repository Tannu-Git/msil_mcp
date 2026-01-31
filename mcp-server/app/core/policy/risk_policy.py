"""Risk-based policy enforcement for tool execution."""
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RiskPolicy:
    """Risk-based access policy."""
    
    risk_level: str  # read, write, privileged
    min_role: str  # Minimum role required
    requires_elevation: bool  # Requires PIM/PAM elevation
    requires_approval: bool  # Requires manager approval
    rate_limit_tier: str  # Rate limit tier
    max_concurrency: int  # Max concurrent executions
    pii_policy: str  # PII handling policy
    
    def allows_role(self, user_role: str) -> bool:
        """Check if user role meets minimum requirement."""
        role_hierarchy = {
            "user": 0,
            "operator": 1,
            "developer": 2,
            "admin": 3
        }
        
        user_level = role_hierarchy.get(user_role, -1)
        required_level = role_hierarchy.get(self.min_role, 999)
        
        return user_level >= required_level


class RiskPolicyManager:
    """Manager for risk-based policies."""
    
    def __init__(self):
        """Initialize risk policy manager."""
        self.policies = self._initialize_policies()
    
    def _initialize_policies(self) -> Dict[str, RiskPolicy]:
        """Initialize default risk policies."""
        return {
            "read": RiskPolicy(
                risk_level="read",
                min_role="user",
                requires_elevation=False,
                requires_approval=False,
                rate_limit_tier="permissive",
                max_concurrency=50,
                pii_policy="mask"
            ),
            "write": RiskPolicy(
                risk_level="write",
                min_role="operator",
                requires_elevation=False,
                requires_approval=False,
                rate_limit_tier="standard",
                max_concurrency=20,
                pii_policy="mask"
            ),
            "privileged": RiskPolicy(
                risk_level="privileged",
                min_role="developer",
                requires_elevation=True,
                requires_approval=True,
                rate_limit_tier="strict",
                max_concurrency=5,
                pii_policy="redact"
            )
        }
    
    def get_policy(self, risk_level: str) -> RiskPolicy:
        """
        Get policy for risk level.
        
        Args:
            risk_level: Risk level (read, write, privileged)
            
        Returns:
            Risk policy
        """
        return self.policies.get(risk_level, self.policies["read"])
    
    def evaluate_access(
        self,
        tool_risk_level: str,
        user_role: str,
        is_elevated: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate access based on tool risk and user role.
        
        Args:
            tool_risk_level: Tool risk level
            user_role: User role
            is_elevated: Whether user is currently elevated
            
        Returns:
            Dictionary with access decision and enforcement details
        """
        policy = self.get_policy(tool_risk_level)
        
        # Check role requirement
        has_role = policy.allows_role(user_role)
        
        # Check elevation requirement
        needs_elevation = policy.requires_elevation and not is_elevated
        
        # Determine if access is allowed
        allowed = has_role and not needs_elevation
        
        result = {
            "allowed": allowed,
            "has_required_role": has_role,
            "requires_elevation": policy.requires_elevation,
            "is_elevated": is_elevated,
            "needs_elevation": needs_elevation,
            "requires_approval": policy.requires_approval,
            "rate_limit_tier": policy.rate_limit_tier,
            "max_concurrency": policy.max_concurrency,
            "pii_policy": policy.pii_policy,
            "reason": self._build_reason(allowed, has_role, needs_elevation, policy)
        }
        
        logger.debug(f"Risk evaluation: {tool_risk_level} for {user_role} -> {allowed}")
        
        return result
    
    def _build_reason(
        self,
        allowed: bool,
        has_role: bool,
        needs_elevation: bool,
        policy: RiskPolicy
    ) -> str:
        """Build reason message for access decision."""
        if allowed:
            return "Access granted"
        
        if not has_role:
            return f"Insufficient role. Requires at least '{policy.min_role}' role"
        
        if needs_elevation:
            return "Elevation required for privileged operation"
        
        return "Access denied"
    
    def get_rate_limit_multiplier(self, tier: str) -> float:
        """
        Get rate limit multiplier for tier.
        
        Args:
            tier: Rate limit tier (permissive, standard, strict)
            
        Returns:
            Multiplier for rate limit (1.0 = standard)
        """
        multipliers = {
            "permissive": 2.0,  # 2x normal rate limit
            "standard": 1.0,    # Normal rate limit
            "strict": 0.5       # Half normal rate limit
        }
        return multipliers.get(tier, 1.0)
    
    def update_policy(
        self,
        risk_level: str,
        **kwargs
    ):
        """
        Update policy for a risk level.
        
        Args:
            risk_level: Risk level to update
            **kwargs: Policy attributes to update
        """
        if risk_level not in self.policies:
            logger.warning(f"Unknown risk level: {risk_level}")
            return
        
        policy = self.policies[risk_level]
        
        for key, value in kwargs.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
                logger.info(f"Updated {risk_level} policy: {key}={value}")
            else:
                logger.warning(f"Unknown policy attribute: {key}")


# Global instance
risk_policy_manager = RiskPolicyManager()
