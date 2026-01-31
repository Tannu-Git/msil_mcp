"""
Structured JSON Logger - Production-ready logging with structured output
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        """Add custom fields to log record"""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Add level name
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname
        
        # Add service name
        log_record['service'] = 'msil-mcp-server'
        
        # Add correlation ID if present
        if hasattr(record, 'correlation_id'):
            log_record['correlation_id'] = record.correlation_id
        
        # Add user ID if present
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        
        # Add request ID if present
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id


def setup_json_logging(level: str = "INFO", output_file: Optional[str] = None):
    """
    Setup structured JSON logging
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        output_file: Optional file path for log output
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        rename_fields={
            'levelname': 'level',
            'name': 'logger',
            'msg': 'message'
        }
    )
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if output_file:
        file_handler = logging.FileHandler(output_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class StructuredLogger:
    """Helper class for structured logging with context"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context: Dict[str, Any] = {}
    
    def add_context(self, **kwargs):
        """Add context fields to all log messages"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear all context fields"""
        self.context = {}
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal log method with context"""
        extra = {**self.context, **kwargs}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def tool_execution(
        self,
        tool_name: str,
        correlation_id: str,
        status: str,
        duration_ms: float,
        **kwargs
    ):
        """Log tool execution"""
        self.info(
            f"Tool execution: {tool_name}",
            tool_name=tool_name,
            correlation_id=correlation_id,
            status=status,
            duration_ms=duration_ms,
            event_type="tool_execution",
            **kwargs
        )
    
    def api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        **kwargs
    ):
        """Log API request"""
        self.info(
            f"{method} {path} - {status_code}",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            event_type="api_request",
            **kwargs
        )
    
    def policy_decision(
        self,
        action: str,
        resource: str,
        allowed: bool,
        user_id: Optional[str] = None,
        **kwargs
    ):
        """Log policy decision"""
        self.info(
            f"Policy decision: {action} on {resource} - {'allowed' if allowed else 'denied'}",
            action=action,
            resource=resource,
            allowed=allowed,
            user_id=user_id,
            event_type="policy_decision",
            **kwargs
        )
    
    def security_event(
        self,
        event: str,
        severity: str,
        user_id: Optional[str] = None,
        **kwargs
    ):
        """Log security event"""
        level = logging.WARNING if severity == "medium" else logging.ERROR
        self._log(
            level,
            f"Security event: {event}",
            security_event=event,
            severity=severity,
            user_id=user_id,
            event_type="security",
            **kwargs
        )


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name)
