"""Policy models for authorization."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class PolicyDecision:
    """Policy decision result."""
    
    allowed: bool
    reason: str
    policies_evaluated: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyRule:
    """Policy rule definition."""
    
    id: str
    name: str
    description: str
    resource_type: str  # tool, api, config
    resource_pattern: str  # * for all, or specific name/pattern
    actions: List[str]  # invoke, read, write, delete
    roles: List[str]  # admin, developer, operator, user
    effect: str = "allow"  # allow or deny
    conditions: Optional[Dict[str, Any]] = None
    priority: int = 0
    is_active: bool = True
