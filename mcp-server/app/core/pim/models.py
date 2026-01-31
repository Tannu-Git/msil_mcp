"""Data models for PIM/PAM."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ElevationStatus:
    """Status of user elevation."""
    
    elevated: bool
    elevated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    reason: Optional[str] = None
    approved_by: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        """Check if elevation is still valid."""
        if not self.elevated:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True


@dataclass
class ElevationRequest:
    """Request for elevation."""
    
    user_id: str
    tool_name: str
    reason: str
    requested_at: datetime
    requires_approval: bool = False
    approval_url: Optional[str] = None
