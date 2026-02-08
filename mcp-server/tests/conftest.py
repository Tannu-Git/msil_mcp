"""
Shared pytest fixtures and configuration for MSIL MCP Server tests.

This module provides:
- Mock users with different roles and permissions
- Mock tools and bundles for testing
- FastAPI TestClient setup
- JWT token generation for auth tests
- Mock request contexts
- Database and Redis mocks
- Policy engine mocks
"""

import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
import jwt
from datetime import datetime

# Core fixtures


@pytest.fixture
def mock_user_admin():
    """Admin user with all roles and permissions."""
    return {
        "user_id": "user-admin-001",
        "email": "admin@msil.dev",
        "roles": ["admin", "data-scientist", "analyst"],
        "scopes": ["read", "write", "delete", "admin"],
        "client_id": "admin-client",
        "is_admin": True
    }


@pytest.fixture
def mock_user_data_scientist():
    """Data scientist user with standard permissions."""
    return {
        "user_id": "user-ds-001",
        "email": "data-scientist@msil.dev",
        "roles": ["data-scientist", "analyst"],
        "scopes": ["read", "write"],
        "client_id": "ds-client",
        "is_admin": False
    }


@pytest.fixture
def mock_user_analyst():
    """Analyst user with read-only permissions."""
    return {
        "user_id": "user-analyst-001",
        "email": "analyst@msil.dev",
        "roles": ["analyst"],
        "scopes": ["read"],
        "client_id": "analyst-client",
        "is_admin": False
    }


@pytest.fixture
def mock_user_no_roles():
    """User with no roles (should have minimal access)."""
    return {
        "user_id": "user-limited-001",
        "email": "limited@msil.dev",
        "roles": [],
        "scopes": [],
        "client_id": "limited-client",
        "is_admin": False
    }


@pytest.fixture
def mock_tools():
    """Mock MCP tools for exposure governance testing."""
    return {
        "read_customer": {
            "name": "read_customer",
            "bundle_name": "customer-service",
            "description": "Read customer information",
            "rate_limit_tier": "read",
            "requires_auth": True,
            "parameters": {
                "customer_id": {"type": "string", "required": True}
            }
        },
        "update_customer": {
            "name": "update_customer",
            "bundle_name": "customer-service",
            "description": "Update customer information",
            "rate_limit_tier": "write",
            "requires_auth": True,
            "parameters": {
                "customer_id": {"type": "string", "required": True},
                "data": {"type": "object", "required": True}
            }
        },
        "delete_customer": {
            "name": "delete_customer",
            "bundle_name": "customer-service",
            "description": "Delete customer",
            "rate_limit_tier": "privileged",
            "requires_auth": True,
            "parameters": {
                "customer_id": {"type": "string", "required": True}
            }
        },
        "query_analytics": {
            "name": "query_analytics",
            "bundle_name": "analytics",
            "description": "Query analytics data",
            "rate_limit_tier": "read",
            "requires_auth": True,
            "parameters": {
                "query": {"type": "string", "required": True}
            }
        }
    }


@pytest.fixture
def mock_exposure_mappings():
    """Mock exposure governance mappings (role -> exposed tools)."""
    return {
        "admin": {
            "expose:bundle:*": ["customer-service", "analytics"],
            "expose:tool:*": ["read_customer", "update_customer", "delete_customer", "query_analytics"]
        },
        "data-scientist": {
            "expose:bundle:customer-service": ["read_customer", "update_customer"],
            "expose:bundle:analytics": ["query_analytics"]
        },
        "analyst": {
            "expose:bundle:customer-service": ["read_customer"],
            "expose:bundle:analytics": ["query_analytics"]
        }
    }


@pytest.fixture
def request_context_admin(mock_user_admin):
    """RequestContext for admin user."""
    from app.core.request_context import RequestContext
    return RequestContext(
        user_id=mock_user_admin["user_id"],
        roles=mock_user_admin["roles"],
        scopes=mock_user_admin["scopes"],
        client_id=mock_user_admin["client_id"],
        correlation_id="corr-admin-001",
        ip="127.0.0.1",
        env="test"
    )


@pytest.fixture
def request_context_data_scientist(mock_user_data_scientist):
    """RequestContext for data scientist user."""
    from app.core.request_context import RequestContext
    return RequestContext(
        user_id=mock_user_data_scientist["user_id"],
        roles=mock_user_data_scientist["roles"],
        scopes=mock_user_data_scientist["scopes"],
        client_id=mock_user_data_scientist["client_id"],
        correlation_id="corr-ds-001",
        ip="192.168.1.1",
        env="test"
    )


@pytest.fixture
def request_context_analyst(mock_user_analyst):
    """RequestContext for analyst user."""
    from app.core.request_context import RequestContext
    return RequestContext(
        user_id=mock_user_analyst["user_id"],
        roles=mock_user_analyst["roles"],
        scopes=mock_user_analyst["scopes"],
        client_id=mock_user_analyst["client_id"],
        correlation_id="corr-analyst-001",
        ip="10.0.0.1",
        env="test"
    )


# JWT Token fixtures


@pytest.fixture
def jwt_secret():
    """Secret key for JWT token generation."""
    return "test-secret-key-for-jwt-tokens"


@pytest.fixture
def jwt_token_admin(mock_user_admin, jwt_secret):
    """Generate valid JWT token for admin user."""
    payload = {
        "sub": mock_user_admin["user_id"],
        "email": mock_user_admin["email"],
        "roles": " ".join(mock_user_admin["roles"]),  # Space-separated roles
        "scope": " ".join(mock_user_admin["scopes"]),  # Space-separated scopes
        "azp": mock_user_admin["client_id"],
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


@pytest.fixture
def jwt_token_data_scientist(mock_user_data_scientist, jwt_secret):
    """Generate valid JWT token for data scientist user."""
    payload = {
        "sub": mock_user_data_scientist["user_id"],
        "email": mock_user_data_scientist["email"],
        "roles": " ".join(mock_user_data_scientist["roles"]),
        "scope": " ".join(mock_user_data_scientist["scopes"]),
        "azp": mock_user_data_scientist["client_id"],
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


@pytest.fixture
def jwt_token_analyst(mock_user_analyst, jwt_secret):
    """Generate valid JWT token for analyst user."""
    payload = {
        "sub": mock_user_analyst["user_id"],
        "email": mock_user_analyst["email"],
        "roles": " ".join(mock_user_analyst["roles"]),
        "scope": " ".join(mock_user_analyst["scopes"]),
        "azp": mock_user_analyst["client_id"],
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


@pytest.fixture
def jwt_token_expired(jwt_secret):
    """Generate expired JWT token."""
    payload = {
        "sub": "user-expired",
        "email": "expired@msil.dev",
        "roles": "analyst",
        "iat": datetime.utcnow() - timedelta(hours=2),
        "exp": datetime.utcnow() - timedelta(hours=1)
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


@pytest.fixture
def jwt_token_invalid():
    """Return invalid JWT token."""
    return "invalid.token.format"


# Mock service fixtures


@pytest.fixture
def mock_exposure_manager():
    """Mock ExposureManager service."""
    manager = AsyncMock()
    manager.filter_tools = AsyncMock(return_value=[])
    manager.is_tool_exposed = Mock(return_value=True)
    manager.get_exposed_tools_for_user = AsyncMock(return_value=[])
    return manager


@pytest.fixture
def mock_policy_engine():
    """Mock PolicyEngine service."""
    engine = AsyncMock()
    
    # Default: allow access for read actions
    decision = Mock()
    decision.allowed = True
    decision.reason = None
    decision.policies_evaluated = ["default-allow"]
    
    engine.evaluate = AsyncMock(return_value=decision)
    return engine


@pytest.fixture
def mock_policy_engine_deny():
    """Mock PolicyEngine that denies access."""
    engine = AsyncMock()
    
    decision = Mock()
    decision.allowed = False
    decision.reason = "User does not have required permissions"
    decision.policies_evaluated = ["deny-policy"]
    
    engine.evaluate = AsyncMock(return_value=decision)
    return engine


@pytest.fixture
def mock_rate_limiter():
    """Mock RateLimiter service."""
    limiter = AsyncMock()
    
    # Default: allow requests
    result = Mock()
    result.allowed = True
    result.remaining = 99
    result.reset_at = datetime.utcnow() + timedelta(hours=1)
    
    limiter.check_user_rate_limit = AsyncMock(return_value=result)
    limiter.check_tool_rate_limit = AsyncMock(return_value=result)
    return limiter


@pytest.fixture
def mock_rate_limiter_exceeded():
    """Mock RateLimiter that indicates exceeded limit."""
    limiter = AsyncMock()
    
    result = Mock()
    result.allowed = False
    result.remaining = 0
    result.reset_at = datetime.utcnow() + timedelta(seconds=60)
    result.retry_after = 60
    
    limiter.check_user_rate_limit = AsyncMock(return_value=result)
    limiter.check_tool_rate_limit = AsyncMock(return_value=result)
    return limiter


@pytest.fixture
def mock_audit_service():
    """Mock AuditService."""
    service = AsyncMock()
    service.log_tool_call = AsyncMock()
    service.log_policy_decision = AsyncMock()
    service.log_authentication_event = AsyncMock()
    service.log_rate_limit_event = AsyncMock()
    return service


@pytest.fixture
def mock_idempotency_store():
    """Mock IdempotencyStore."""
    store = AsyncMock()
    store.get = AsyncMock(return_value=None)
    store.set = AsyncMock()
    return store


@pytest.fixture
def mock_metrics_collector():
    """Mock MetricsCollector."""
    collector = Mock()
    collector.record_tool_execution = Mock()
    collector.record_policy_decision = Mock()
    collector.get_all_executions = Mock(return_value=[])
    return collector


# Settings/Config fixtures


@pytest.fixture
def test_settings():
    """Test configuration settings."""
    from app.config import settings
    
    # Override for testing
    settings.AUTH_REQUIRED = True
    settings.DEMO_MODE = True
    settings.DEMO_MODE_AUTH_BYPASS = True
    settings.DEMO_MODE_DEFAULT_ROLE = "analyst"
    settings.RATE_LIMIT_ENABLED = True
    settings.IDEMPOTENCY_ENABLED = True
    settings.AUDIT_ENABLED = True
    settings.ENVIRONMENT = "test"
    
    return settings


# FastAPI TestClient fixtures


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture
def test_client(app):
    """Create TestClient for API testing."""
    return TestClient(app)


# Helper fixtures


@pytest.fixture
def mcp_request_body_tools_list():
    """Sample MCP request for tools/list."""
    return {
        "jsonrpc": "2.0",
        "id": "test-1",
        "method": "tools/list",
        "params": {}
    }


@pytest.fixture
def mcp_request_body_tools_call(mock_tools):
    """Sample MCP request for tools/call."""
    return {
        "jsonrpc": "2.0",
        "id": "test-2",
        "method": "tools/call",
        "params": {
            "name": "read_customer",
            "arguments": {
                "customer_id": "cust-123"
            },
            "idempotency_key": "idem-key-001"
        }
    }


@pytest.fixture
def chat_request_body():
    """Sample Chat API request."""
    return {
        "message": "What is the customer info for ID 123?",
        "role": "user",
        "conversation_id": "conv-001"
    }


# Parametrization helpers for edge cases


@pytest.fixture
def edge_case_tool_names():
    """Edge case tool names for robustness testing."""
    return [
        "",  # Empty string
        "a" * 1000,  # Very long name
        "<script>alert('xss')</script>",  # XSS injection attempt
        "../../etc/passwd",  # Path traversal attempt
        "tool\nname",  # Newline injection
        "tool\x00name",  # Null byte injection
    ]


@pytest.fixture
def edge_case_user_ids():
    """Edge case user IDs."""
    return [
        "",  # Empty
        "a" * 2000,  # Very long
        "'\" OR 1=1 --",  # SQL injection attempt
        "user\x00admin",  # Null byte
    ]


# Marker fixtures for test organization


@pytest.fixture
def mark_critical():
    """Marker for critical security tests that must pass."""
    return pytest.mark.critical


@pytest.fixture
def mark_security():
    """Marker for all security-related tests."""
    return pytest.mark.security


@pytest.fixture
def mark_performance():
    """Marker for performance tests."""
    return pytest.mark.performance


@pytest.fixture
def mark_integration():
    """Marker for integration tests."""
    return pytest.mark.integration
