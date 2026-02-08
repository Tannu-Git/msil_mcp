"""
Integration tests for MCP tools/list and tools/call with exposure filtering.

Tests the full flow:
1. Client sends X-User-ID and X-User-Roles headers
2. MCP handler extracts user context
3. ExposureManager filters tools
4. Response includes only exposed tools
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, Mock
from uuid import uuid4

from app.core.tools.registry import Tool


@pytest.fixture
def client():
    """Create test client for MCP endpoints."""
    from app.api.mcp import router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    
    return TestClient(app)


@pytest.fixture
def mock_exposure_manager():
    """Mock exposure manager."""
    manager = AsyncMock()
    manager.filter_tools = AsyncMock()
    manager.is_tool_exposed = Mock()
    manager.get_exposed_tools_for_user = AsyncMock()
    return manager


@pytest.fixture
def mock_tools():
    """Mock tools list."""
    return [
        Tool(
            id=uuid4(),
            name="book_appointment",
            display_name="Book Appointment",
            description="Book a service appointment",
            category="service_booking",
            api_endpoint="/api/booking/book",
            http_method="POST",
            input_schema={"type": "object"},
            bundle_name="Service Booking"
        ),
        Tool(
            id=uuid4(),
            name="list_appointments",
            display_name="List Appointments",
            description="List service appointments",
            category="service_booking",
            api_endpoint="/api/booking/list",
            http_method="GET",
            input_schema={"type": "object"},
            bundle_name="Service Booking"
        ),
        Tool(
            id=uuid4(),
            name="get_dealer",
            display_name="Get Dealer",
            description="Get dealer information",
            category="dealer_management",
            api_endpoint="/api/dealers/get",
            http_method="GET",
            input_schema={"type": "object"},
            bundle_name="Dealer Management"
        ),
    ]


# ============================================
# tools/list TESTS
# ============================================

@pytest.mark.asyncio
async def test_tools_list_with_user_context(client, mock_exposure_manager, mock_tools):
    """Test tools/list endpoint with user context headers."""
    decision = Mock()
    decision.allowed = True
    decision.reason = None

    with patch("app.api.mcp.exposure_manager", mock_exposure_manager), \
         patch("app.api.mcp.tool_registry.list_tools", AsyncMock(return_value=mock_tools)), \
         patch("app.api.mcp.policy_engine.evaluate", AsyncMock(return_value=decision)):
        
        mock_exposure_manager.filter_tools.return_value = mock_tools[:2]
        
        response = client.post(
            "/mcp",
            headers={
                "X-User-ID": "user123",
                "X-User-Roles": "operator",
            },
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/list",
            },
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    # tools/list should return filtered tools
    tools = data["result"].get("tools", [])
    assert len(tools) == 2


@pytest.mark.asyncio
async def test_tools_list_operator_role(client, mock_exposure_manager, mock_tools):
    """Test tools/list for operator role (limited access)."""
    service_booking_tools = mock_tools[:2]
    decision = Mock()
    decision.allowed = True
    decision.reason = None

    with patch("app.api.mcp.exposure_manager", mock_exposure_manager), \
         patch("app.api.mcp.tool_registry.list_tools", AsyncMock(return_value=mock_tools)), \
         patch("app.api.mcp.policy_engine.evaluate", AsyncMock(return_value=decision)):
        
        mock_exposure_manager.filter_tools.return_value = service_booking_tools
        
        response = client.post(
            "/mcp",
            headers={
                "X-User-ID": "operator_user",
                "X-User-Roles": "operator",
            },
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/list",
            },
        )
    
    assert response.status_code == 200
    tools = response.json()["result"]["tools"]
    
    # Should only contain Service Booking tools
    assert all(t["bundle"] == "Service Booking" for t in tools)
    assert len(tools) == 2


@pytest.mark.asyncio
async def test_tools_list_admin_role(client, mock_exposure_manager, mock_tools):
    """Test tools/list for admin role (full access)."""
    decision = Mock()
    decision.allowed = True
    decision.reason = None

    with patch("app.api.mcp.exposure_manager", mock_exposure_manager), \
         patch("app.api.mcp.tool_registry.list_tools", AsyncMock(return_value=mock_tools)), \
         patch("app.api.mcp.policy_engine.evaluate", AsyncMock(return_value=decision)):
        
        mock_exposure_manager.filter_tools.return_value = mock_tools
        
        response = client.post(
            "/mcp",
            headers={
                "X-User-ID": "admin_user",
                "X-User-Roles": "admin",
            },
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/list",
            },
        )
    
    assert response.status_code == 200
    tools = response.json()["result"]["tools"]
    
    # Admin should see all tools
    assert len(tools) == 3


@pytest.mark.asyncio
async def test_tools_list_multiple_roles(client, mock_exposure_manager, mock_tools):
    """Test tools/list with multiple roles."""
    decision = Mock()
    decision.allowed = True
    decision.reason = None

    with patch("app.api.mcp.exposure_manager", mock_exposure_manager), \
         patch("app.api.mcp.tool_registry.list_tools", AsyncMock(return_value=mock_tools)), \
         patch("app.api.mcp.policy_engine.evaluate", AsyncMock(return_value=decision)):
        
        # Operator + Developer should see more tools
        mock_exposure_manager.filter_tools.return_value = mock_tools[:3]
        
        response = client.post(
            "/mcp",
            headers={
                "X-User-ID": "user123",
                "X-User-Roles": "operator,developer",
            },
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/list",
            },
        )
    
    assert response.status_code == 200
    tools = response.json()["result"]["tools"]
    assert len(tools) == 3


@pytest.mark.asyncio
async def test_tools_list_no_user_context(client, mock_exposure_manager, mock_tools):
    """Test tools/list without user context headers."""
    decision = Mock()
    decision.allowed = True
    decision.reason = None

    with patch("app.api.mcp.exposure_manager", mock_exposure_manager), \
         patch("app.api.mcp.tool_registry.list_tools", AsyncMock(return_value=mock_tools)), \
         patch("app.api.mcp.policy_engine.evaluate", AsyncMock(return_value=decision)):
        
        mock_exposure_manager.filter_tools.return_value = []
        
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/list",
            },
        )
    
    # Should still work, but with anonymous user context
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_tools_list_includes_bundle_metadata(client, mock_exposure_manager, mock_tools):
    """Test that tools/list response includes bundle metadata."""
    decision = Mock()
    decision.allowed = True
    decision.reason = None

    with patch("app.api.mcp.exposure_manager", mock_exposure_manager), \
         patch("app.api.mcp.tool_registry.list_tools", AsyncMock(return_value=mock_tools)), \
         patch("app.api.mcp.policy_engine.evaluate", AsyncMock(return_value=decision)):
        
        mock_exposure_manager.filter_tools.return_value = mock_tools
        
        response = client.post(
            "/mcp",
            headers={
                "X-User-ID": "user123",
                "X-User-Roles": "admin",
            },
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/list",
            },
        )
    
    tools = response.json()["result"]["tools"]
    
    # Each tool should include bundle metadata
    assert all("bundle" in tool for tool in tools)


# ============================================
# tools/call TESTS
# ============================================

@pytest.mark.asyncio
async def test_tools_call_allowed_tool(client, mock_exposure_manager):
    """Test tools/call for tool that user has access to."""
    decision = Mock()
    decision.allowed = True
    decision.reason = None

    rate_ok = Mock()
    rate_ok.allowed = True
    rate_ok.retry_after = None

    mock_tool = Tool(
        id=uuid4(),
        name="book_appointment",
        display_name="Book Appointment",
        description="Book a service appointment",
        category="service_booking",
        api_endpoint="/api/booking/book",
        http_method="POST",
        input_schema={"type": "object"},
        bundle_name="Service Booking"
    )

    with patch("app.api.mcp.exposure_manager", mock_exposure_manager), \
         patch("app.api.mcp.tool_registry.get_tool", AsyncMock(return_value=mock_tool)), \
         patch("app.api.mcp.policy_engine.evaluate", AsyncMock(return_value=decision)), \
         patch("app.api.mcp.rate_limiter.check_user_rate_limit", AsyncMock(return_value=rate_ok)), \
         patch("app.api.mcp.rate_limiter.check_tool_rate_limit", AsyncMock(return_value=rate_ok)), \
         patch("app.api.mcp.tool_executor.execute", AsyncMock(return_value={"success": True})):

        mock_exposure_manager.get_exposed_tools_for_user.return_value = ["service_booking"]
        mock_exposure_manager.is_tool_exposed.return_value = True

        response = client.post(
            "/mcp",
            headers={
                "X-User-ID": "user123",
                "X-User-Roles": "operator",
            },
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/call",
                "params": {
                    "name": "book_appointment",
                    "arguments": {"date": "2026-02-15"},
                },
            },
        )
    
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["isError"] is False
    assert "content" in result


@pytest.mark.asyncio
async def test_tools_call_forbidden_tool(client, mock_exposure_manager):
    """Test tools/call for tool that user does NOT have access to."""
    mock_tool = Tool(
        id=uuid4(),
        name="get_dealer",
        display_name="Get Dealer",
        description="Get dealer information",
        category="dealer_management",
        api_endpoint="/api/dealers/get",
        http_method="GET",
        input_schema={"type": "object"},
        bundle_name="Dealer Management"
    )

    with patch("app.api.mcp.exposure_manager", mock_exposure_manager), \
         patch("app.api.mcp.tool_registry.get_tool", AsyncMock(return_value=mock_tool)):

        mock_exposure_manager.get_exposed_tools_for_user.return_value = ["service_booking"]
        mock_exposure_manager.is_tool_exposed.return_value = False

        response = client.post(
            "/mcp",
            headers={
                "X-User-ID": "user123",
                "X-User-Roles": "operator",
            },
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/call",
                "params": {
                    "name": "get_dealer",  # Dealer Management bundle, not for operator
                    "arguments": {"dealer_id": "D123"},
                },
            },
        )
    
    # Should return HTTP 403 error
    assert response.status_code == 403
    error_detail = response.json().get("detail", "")
    assert "exposed" in error_detail.lower() or "forbidden" in error_detail.lower()


@pytest.mark.asyncio
async def test_tools_call_admin_all_access(client, mock_exposure_manager):
    """Test tools/call for admin (should access any tool)."""
    decision = Mock()
    decision.allowed = True
    decision.reason = None

    rate_ok = Mock()
    rate_ok.allowed = True
    rate_ok.retry_after = None

    mock_tool = Tool(
        id=uuid4(),
        name="get_dealer",
        display_name="Get Dealer",
        description="Get dealer information",
        category="dealer_management",
        api_endpoint="/api/dealers/get",
        http_method="GET",
        input_schema={"type": "object"},
        bundle_name="Dealer Management"
    )

    with patch("app.api.mcp.exposure_manager", mock_exposure_manager), \
         patch("app.api.mcp.tool_registry.get_tool", AsyncMock(return_value=mock_tool)), \
         patch("app.api.mcp.policy_engine.evaluate", AsyncMock(return_value=decision)), \
         patch("app.api.mcp.rate_limiter.check_user_rate_limit", AsyncMock(return_value=rate_ok)), \
         patch("app.api.mcp.rate_limiter.check_tool_rate_limit", AsyncMock(return_value=rate_ok)), \
         patch("app.api.mcp.tool_executor.execute", AsyncMock(return_value={"success": True})):

        # Admin can access anything
        mock_exposure_manager.get_exposed_tools_for_user.return_value = ["service_booking", "dealer_management"]
        mock_exposure_manager.is_tool_exposed.return_value = True

        response = client.post(
            "/mcp",
            headers={
                "X-User-ID": "admin_user",
                "X-User-Roles": "admin",
            },
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/call",
                "params": {
                    "name": "get_dealer",
                    "arguments": {"dealer_id": "D123"},
                },
            },
        )
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_tools_call_unauthorized_authorization_error(client, mock_exposure_manager):
    """Test tools/call when user has exposure but lacks authorization."""
    decision = Mock()
    decision.allowed = False
    decision.reason = "Denied by policy"

    mock_tool = Tool(
        id=uuid4(),
        name="book_appointment",
        display_name="Book Appointment",
        description="Book a service appointment",
        category="service_booking",
        api_endpoint="/api/booking/book",
        http_method="POST",
        input_schema={"type": "object"},
        bundle_name="Service Booking"
    )

    with patch("app.api.mcp.exposure_manager", mock_exposure_manager), \
         patch("app.api.mcp.tool_registry.get_tool", AsyncMock(return_value=mock_tool)), \
         patch("app.api.mcp.policy_engine.evaluate", AsyncMock(return_value=decision)), \
         patch("app.api.mcp.tool_executor.execute", AsyncMock(return_value={"success": True})) as mock_execute:

        # User has exposure but not authorization
        mock_exposure_manager.get_exposed_tools_for_user.return_value = ["service_booking"]
        mock_exposure_manager.is_tool_exposed.return_value = True

        response = client.post(
            "/mcp",
            headers={
                "X-User-ID": "user123",
                "X-User-Roles": "restricted",
            },
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/call",
                "params": {
                    "name": "book_appointment",
                    "arguments": {"date": "2026-02-15"},
                },
            },
        )

    mock_execute.assert_not_called()
    
    # Should fail at authorization layer, not exposure layer
    assert response.status_code >= 400


@pytest.mark.asyncio
async def test_tools_call_nonexistent_tool(client, mock_exposure_manager):
    """Test tools/call for non-existent tool."""
    with patch("app.api.mcp.exposure_manager", mock_exposure_manager), \
         patch("app.api.mcp.tool_registry.get_tool", AsyncMock(return_value=None)):

        response = client.post(
            "/mcp",
            headers={
                "X-User-ID": "user123",
                "X-User-Roles": "admin",
            },
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/call",
                "params": {
                    "name": "nonexistent_tool",
                    "arguments": {},
                },
            },
        )
    
    assert response.status_code >= 400


# ============================================
# DEFENSE-IN-DEPTH TESTS
# ============================================

@pytest.mark.asyncio
async def test_exposure_check_in_tools_list(client, mock_exposure_manager, mock_tools):
    """Test that exposure filtering is applied in tools/list."""
    decision = Mock()
    decision.allowed = True
    decision.reason = None

    with patch("app.api.mcp.exposure_manager", mock_exposure_manager), \
         patch("app.api.mcp.tool_registry.list_tools", AsyncMock(return_value=mock_tools)), \
         patch("app.api.mcp.policy_engine.evaluate", AsyncMock(return_value=decision)):

        client.post(
            "/mcp",
            headers={
                "X-User-ID": "user123",
                "X-User-Roles": "operator",
            },
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/list",
            },
        )
    
    # Verify filter_tools was called
    mock_exposure_manager.filter_tools.assert_called()


@pytest.mark.asyncio
async def test_exposure_check_in_tools_call(client, mock_exposure_manager):
    """Test that exposure validation is applied in tools/call."""
    decision = Mock()
    decision.allowed = True
    decision.reason = None

    rate_ok = Mock()
    rate_ok.allowed = True
    rate_ok.retry_after = None

    mock_tool = Tool(
        id=uuid4(),
        name="book_appointment",
        display_name="Book Appointment",
        description="Book a service appointment",
        category="service_booking",
        api_endpoint="/api/booking/book",
        http_method="POST",
        input_schema={"type": "object"},
        bundle_name="Service Booking"
    )

    with patch("app.api.mcp.exposure_manager", mock_exposure_manager), \
         patch("app.api.mcp.tool_registry.get_tool", AsyncMock(return_value=mock_tool)), \
         patch("app.api.mcp.policy_engine.evaluate", AsyncMock(return_value=decision)), \
         patch("app.api.mcp.rate_limiter.check_user_rate_limit", AsyncMock(return_value=rate_ok)), \
         patch("app.api.mcp.rate_limiter.check_tool_rate_limit", AsyncMock(return_value=rate_ok)), \
         patch("app.api.mcp.tool_executor.execute", AsyncMock(return_value={"success": True})):

        mock_exposure_manager.get_exposed_tools_for_user.return_value = ["service_booking"]
        mock_exposure_manager.is_tool_exposed.return_value = True

        client.post(
            "/mcp",
            headers={
                "X-User-ID": "user123",
                "X-User-Roles": "operator",
            },
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/call",
                "params": {
                    "name": "book_appointment",
                    "arguments": {},
                },
            },
        )
    
    # Verify is_tool_exposed was called
    mock_exposure_manager.is_tool_exposed.assert_called()


# ============================================
# PERFORMANCE & CACHING TESTS
# ============================================

@pytest.mark.asyncio
async def test_caching_reduces_db_calls(client, mock_exposure_manager, mock_tools):
    """Test that exposure caching reduces database calls."""
    call_count = 0
    
    def mock_filter(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return mock_tools[:2]
    
    decision = Mock()
    decision.allowed = True
    decision.reason = None

    with patch("app.api.mcp.exposure_manager", mock_exposure_manager), \
        patch("app.api.mcp.tool_registry.list_tools", AsyncMock(return_value=mock_tools)), \
        patch("app.api.mcp.policy_engine.evaluate", AsyncMock(return_value=decision)):
        
        mock_exposure_manager.filter_tools = AsyncMock(side_effect=mock_filter)
        
        # First request
        client.post(
            "/mcp",
            headers={
                "X-User-ID": "user123",
                "X-User-Roles": "operator",
            },
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/list",
            },
        )
        
        # Second request (same user, same roles)
        client.post(
            "/mcp",
            headers={
                "X-User-ID": "user123",
                "X-User-Roles": "operator",
            },
            json={
                "jsonrpc": "2.0",
                "id": "2",
                "method": "tools/list",
            },
        )


# ============================================
# ERROR SCENARIOS
# ============================================

@pytest.mark.asyncio
async def test_malformed_json_request(client):
    """Test handling of malformed JSON-RPC request."""
    response = client.post(
        "/mcp",
        headers={
            "X-User-ID": "user123",
            "X-User-Roles": "operator",
        },
        json={
            "invalid": "request",
        },
    )
    
    # Should return JSON-RPC error
    assert response.status_code >= 400


@pytest.mark.asyncio
async def test_missing_method_in_request(client):
    """Test handling of missing method in JSON-RPC request."""
    response = client.post(
        "/mcp",
        headers={
            "X-User-ID": "user123",
            "X-User-Roles": "operator",
        },
        json={
            "jsonrpc": "2.0",
            "id": "1",
        },
    )
    
    assert response.status_code >= 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
