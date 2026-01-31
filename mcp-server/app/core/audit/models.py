"""Audit event models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
import uuid


@dataclass
class AuditEvent:
    """Audit event for compliance logging."""
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_type: str = ""  # tool_call, policy_decision, auth_event, config_change
    correlation_id: str = ""
    user_id: Optional[str] = None
    tool_name: Optional[str] = None
    action: str = ""
    status: str = ""  # success, failure, denied
    latency_ms: Optional[float] = None
    request_size: Optional[int] = None
    response_size: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "event_type": self.event_type,
            "correlation_id": self.correlation_id,
            "user_id": self.user_id,
            "tool_name": self.tool_name,
            "action": self.action,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "request_size": self.request_size,
            "response_size": self.response_size,
            "error_message": self.error_message,
            "metadata": self.metadata
        }
