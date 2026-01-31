"""Audit service for compliance and security logging."""

import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime

from .models import AuditEvent
from .pii_masker import pii_masker
from .s3_store import S3WORMStore

logger = logging.getLogger(__name__)


class AuditService:
    """Audit logging service for compliance with 12-month retention."""
    
    def __init__(
        self,
        db=None,
        s3_client: Optional[S3WORMStore] = None,
        dual_write: bool = True
    ):
        """Initialize audit service.
        
        Args:
            db: Database connection (for PostgreSQL storage)
            s3_client: S3 WORM store client
            dual_write: Write to both DB and S3
        """
        self.db = db
        self.s3 = s3_client
        self.dual_write = dual_write
        self._in_memory_logs = []  # Fallback if DB not available
    
    async def log_event(self, event: AuditEvent):
        """Log audit event to storage.
        
        Args:
            event: Audit event to log
        """
        try:
            # Mask PII in metadata
            if event.metadata:
                event.metadata = pii_masker.mask_dict(event.metadata)
            
            # Mask PII in user_id (partial masking)
            if event.user_id:
                event.user_id = self._mask_user_id(event.user_id)
            
            # Write to S3 WORM storage
            if self.s3:
                try:
                    await self.s3.write_audit_event(event.to_dict())
                    logger.info(f"Audit event written to S3 WORM: {event.event_type}")
                except Exception as e:
                    logger.error(f"Failed to write audit event to S3: {e}")
                    # Continue to DB write if dual_write enabled
            
            # Log to database if available
            if self.db and (self.dual_write or not self.s3):
                await self._log_to_database(event)
            elif not self.db and not self.s3:
                # Fallback: store in memory (for demo)
                self._in_memory_logs.append(event.to_dict())
                logger.info(f"Audit event logged to memory: {event.event_type}")
            
            # Log to S3 for immutable storage (future implementation)
            if self.s3:
                await self._write_to_s3(event)
            
            # Also log to application logger for immediate visibility
            logger.info(
                f"AUDIT: {event.event_type} | {event.action} | {event.status} | "
                f"user={event.user_id} | tool={event.tool_name} | "
                f"correlation={event.correlation_id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            # Don't raise - audit logging should never break the main flow
    
    async def log_tool_call(
        self,
        tool_name: str,
        params: Dict,
        result: Any,
        latency: float,
        correlation_id: str,
        user_id: str,
        status: str = "success",
        error: str = None
    ):
        """Log tool execution.
        
        Args:
            tool_name: Name of the tool
            params: Tool parameters
            result: Tool result
            latency: Execution time in seconds
            correlation_id: Request correlation ID
            user_id: User who executed the tool
            status: Execution status
            error: Error message if failed
        """
        event = AuditEvent(
            event_type="tool_call",
            correlation_id=correlation_id,
            user_id=user_id,
            tool_name=tool_name,
            action="invoke",
            status=status,
            latency_ms=latency * 1000,
            request_size=len(json.dumps(params)) if params else 0,
            response_size=len(json.dumps(result)) if result else 0,
            error_message=error,
            metadata={
                "params": params,
                "result": result if status == "success" else None
            }
        )
        await self.log_event(event)
    
    async def log_policy_decision(
        self,
        decision: Dict,
        context: Dict,
        correlation_id: str
    ):
        """Log policy decision.
        
        Args:
            decision: Policy decision details
            context: Decision context
            correlation_id: Request correlation ID
        """
        event = AuditEvent(
            event_type="policy_decision",
            correlation_id=correlation_id,
            user_id=context.get("user_id"),
            tool_name=context.get("tool_name"),
            action=context.get("action"),
            status="allowed" if decision.get("allowed") else "denied",
            error_message=decision.get("reason") if not decision.get("allowed") else None,
            metadata={
                "decision": decision,
                "context": context
            }
        )
        await self.log_event(event)
    
    async def log_auth_event(
        self,
        action: str,
        user_id: Optional[str],
        status: str,
        correlation_id: str,
        metadata: Optional[Dict] = None
    ):
        """Log authentication event.
        
        Args:
            action: Auth action (login, logout, refresh, etc.)
            user_id: User ID
            status: Event status
            correlation_id: Request correlation ID
            metadata: Additional metadata
        """
        event = AuditEvent(
            event_type="auth_event",
            correlation_id=correlation_id,
            user_id=user_id,
            action=action,
            status=status,
            metadata=metadata or {}
        )
        await self.log_event(event)
    
    async def log_config_change(
        self,
        action: str,
        resource: str,
        user_id: str,
        correlation_id: str,
        changes: Dict
    ):
        """Log configuration change.
        
        Args:
            action: Change action (create, update, delete, toggle)
            resource: Resource being changed
            user_id: User making the change
            correlation_id: Request correlation ID
            changes: Details of changes made
        """
        event = AuditEvent(
            event_type="config_change",
            correlation_id=correlation_id,
            user_id=user_id,
            action=action,
            status="success",
            metadata={
                "resource": resource,
                "changes": changes
            }
        )
        await self.log_event(event)
    
    async def get_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tool_name: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict:
        """Get audit logs with filters.
        
        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            tool_name: Filter by tool name
            user_id: Filter by user ID
            status: Filter by status
            event_type: Filter by event type
            limit: Maximum number of logs
            offset: Pagination offset
            
        Returns:
            Dictionary with logs and total count
        """
        if self.db:
            # Query from database (future implementation)
            pass
        else:
            # Return from in-memory logs
            logs = self._in_memory_logs
            
            # Apply filters
            if start_date:
                logs = [log for log in logs if datetime.fromisoformat(log["timestamp"]) >= start_date]
            if end_date:
                logs = [log for log in logs if datetime.fromisoformat(log["timestamp"]) <= end_date]
            if tool_name:
                logs = [log for log in logs if log.get("tool_name") == tool_name]
            if user_id:
                logs = [log for log in logs if log.get("user_id") == user_id]
            if status:
                logs = [log for log in logs if log.get("status") == status]
            if event_type:
                logs = [log for log in logs if log.get("event_type") == event_type]
            
            # Sort by timestamp descending
            logs = sorted(logs, key=lambda x: x["timestamp"], reverse=True)
            
            # Apply pagination
            total = len(logs)
            logs = logs[offset:offset + limit]
            
            return {
                "logs": logs,
                "total": total,
                "limit": limit,
                "offset": offset
            }
    
    def _mask_user_id(self, user_id: str) -> str:
        """Partially mask user ID for logging."""
        if not user_id or len(user_id) <= 4:
            return "***"
        return f"{user_id[:2]}***{user_id[-2:]}"
    
    async def _log_to_database(self, event: AuditEvent):
        """Log event to PostgreSQL database.
        
        Args:
            event: Audit event to log
        """
        query = """
            INSERT INTO audit_logs (
                event_id, timestamp, event_type, correlation_id,
                user_id, tool_name, action, status, latency_ms,
                request_size, response_size, error_message, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """
        try:
            await self.db.execute(
                query,
                event.event_id,
                event.timestamp,
                event.event_type,
                event.correlation_id,
                event.user_id,
                event.tool_name,
                event.action,
                event.status,
                event.latency_ms,
                event.request_size,
                event.response_size,
                event.error_message,
                json.dumps(event.metadata)
            )
            logger.debug(f"Audit event logged to database: {event.event_id}")
        except Exception as e:
            logger.error(f"Failed to log to database: {str(e)}")
            # Fallback to in-memory
            self._in_memory_logs.append(event.to_dict())
    
    async def _write_to_s3(self, event: AuditEvent):
        """Write audit event to S3 for WORM storage.
        
        This will be implemented when S3 integration is added.
        S3 Object Lock should be enabled for immutable storage.
        
        Args:
            event: Audit event to store
        """
        # Future: Implement S3 Object Lock for WORM compliance
        # Key format: audit-logs/{year}/{month}/{day}/{event_id}.json
        pass


# Global audit service instance
audit_service = AuditService()
