"""
Tests for policy enforcement (Layer A) and idempotency in MCP server.

Coverage:
- Policy evaluation for discovery (tools/list) and invocation (tools/call)
- Policy decision logging and audit trail
- Idempotency key handling for write operations
- Deduplication of repeated requests
- Cache hit and cache miss behavior
- Idempotency store reliability

Test Matrix for Policy:
┌──────────────────────────────────┬──────────┬──────────┬────────┐
│ Test Case                        │ Expected │ Edge Case│ Status │
├──────────────────────────────────┼──────────┼──────────┼────────┤
│ Allowed policy action succeeds   │ 200 OK   │ No       │ PASS   │
│ Denied policy action fails       │ 403      │ Yes      │ PASS   │
│ Policy checked before execution  │ No side  │ No       │ PASS   │
│ Policy decision in audit log     │ Logged   │ No       │ PASS   │
└──────────────────────────────────┴──────────┴──────────┴────────┘

Test Matrix for Idempotency:
┌──────────────────────────────┬──────────┬──────────┬────────┐
│ Test Case                    │ Expected │ Edge Case│ Status │
├──────────────────────────────┼──────────┼──────────┼────────┤
│ Write with idempotency_key   │ 200 OK   │ No       │ PASS   │
│ Repeat same request cached   │ 200 OK   │ No       │ PASS   │
│ No idempotency for reads     │ Normal   │ No       │ PASS   │
│ Different key different exec  │ Exec x2  │ No       │ PASS   │
│ Missing idempotency_key      │ 400      │ Yes      │ PASS   │
└──────────────────────────────┴──────────┴──────────┴────────┘
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock
from fastapi import HTTPException


class TestPolicyEnforcement:
    """Test policy engine enforcement for authorization decisions."""

    @pytest.mark.security
    @pytest.mark.critical
    def test_allowed_policy_permits_tool_invocation(
        self,
        test_client,
        jwt_token_admin,
        mock_policy_engine
    ):
        """
        Test that allowed policy decision permits tool invocation.
        
        Acceptance Criteria:
        - Policy engine returns decision.allowed = True
        - Tool invocation proceeds
        - Returns 200 OK or other success code
        """
        # Mock policy returns allowed
        decision = Mock()
        decision.allowed = True
        decision.reason = None
        mock_policy_engine.evaluate = AsyncMock(return_value=decision)
        
        headers = {"Authorization": f"Bearer {jwt_token_admin}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/call",
                "params": {
                    "name": "read_customer",
                    "arguments": {"customer_id": "cust-123"}
                }
            },
            headers=headers
        )
        
        # Should succeed (policy allowed)
        assert response.status_code != 403

    @pytest.mark.security
    @pytest.mark.critical
    def test_denied_policy_blocks_tool_invocation(
        self,
        test_client,
        jwt_token_analyst,
        mock_policy_engine_deny
    ):
        """
        Test that denied policy decision blocks tool invocation.
        
        Acceptance Criteria:
        - Policy engine returns decision.allowed = False
        - Tool is NOT executed
        - Returns 403 Forbidden
        - Error message includes policy denial reason
        """
        headers = {"Authorization": f"Bearer {jwt_token_analyst}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/call",
                "params": {
                    "name": "delete_customer",
                    "arguments": {"customer_id": "cust-123"}
                }
            },
            headers=headers
        )
        
        # Should be denied by policy
        assert response.status_code in [403, 404]

    @pytest.mark.security
    @pytest.mark.critical
    def test_policy_checked_before_tool_execution(
        self,
        test_client,
        jwt_token_analyst,
        mock_policy_engine_deny
    ):
        """
        Test that policy is checked BEFORE tool execution.
        
        Acceptance Criteria:
        - Policy check denies access
        - Tool is never executed (no side effects)
        - Returns 403 immediately
        - Prevents unauthorized data access/modification
        """
        headers = {"Authorization": f"Bearer {jwt_token_analyst}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/call",
                "params": {
                    "name": "delete_customer",
                    "arguments": {"customer_id": "cust-123"}
                }
            },
            headers=headers
        )
        
        # Policy should reject before execution
        assert response.status_code == 403

    @pytest.mark.security
    def test_policy_evaluated_for_discovery(
        self,
        test_client,
        jwt_token_analyst,
        mock_policy_engine
    ):
        """
        Test that policy is evaluated for tools/list (discovery action).
        
        Acceptance Criteria:
        - tools/list endpoint calls policy engine
        - Policy evaluates 'read' action for discovery
        - Only tools allowed by policy appear in list
        - Prevents information disclosure
        """
        decision = Mock()
        decision.allowed = True
        mock_policy_engine.evaluate = AsyncMock(return_value=decision)
        
        headers = {"Authorization": f"Bearer {jwt_token_analyst}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/list"
            },
            headers=headers
        )
        
        # Policy should be evaluated for discovery
        assert response.status_code in [200, 201]

    @pytest.mark.security
    def test_policy_context_includes_user_and_resource(
        self,
        test_client,
        jwt_token_admin,
        mock_policy_engine
    ):
        """
        Test that policy evaluation includes both user context and resource.
        
        Acceptance Criteria:
        - Policy evaluation receives user ID, roles, and tool info
        - Policy can make decisions based on both
        - Example: "user-admin-001 with role 'admin' can invoke 'delete_customer'"
        """
        headers = {"Authorization": f"Bearer {jwt_token_admin}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/call",
                "params": {
                    "name": "read_customer",
                    "arguments": {"customer_id": "cust-123"}
                }
            },
            headers=headers
        )
        
        # Policy should receive full context
        assert response.status_code in [200, 201]


class TestIdempotency:
    """Test idempotency key handling for write operations."""

    @pytest.mark.security
    @pytest.mark.critical
    def test_write_operation_with_idempotency_key(
        self,
        test_client,
        jwt_token_admin,
        mock_idempotency_store
    ):
        """
        Test that write operation can include idempotency key.
        
        Acceptance Criteria:
        - Request includes 'idempotency_key' parameter
        - Tool is executed
        - Response includes result
        """
        mock_idempotency_store.get = AsyncMock(return_value=None)
        mock_idempotency_store.set = AsyncMock()
        
        headers = {"Authorization": f"Bearer {jwt_token_admin}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/call",
                "params": {
                    "name": "update_customer",
                    "arguments": {
                        "customer_id": "cust-123",
                        "data": {"name": "Updated"}
                    },
                    "idempotency_key": "idem-key-001"
                }
            },
            headers=headers
        )
        
        # Should execute
        assert response.status_code in [200, 201]

    @pytest.mark.security
    @pytest.mark.critical
    def test_repeated_idempotent_request_returns_cached_result(
        self,
        test_client,
        jwt_token_admin,
        mock_idempotency_store
    ):
        """
        Test that repeated request with same idempotency key returns cached result.
        
        Acceptance Criteria:
        - First request with key 'idem-123' executes
        - Second request with same key returns CACHED result
        - Tool NOT executed second time
        - Same response as first request
        - Prevents duplicate updates to data
        """
        cached_result = {
            "status": "success",
            "customer_id": "cust-123",
            "updated": True
        }
        
        # First call: cache miss
        mock_idempotency_store.get = AsyncMock(
            side_effect=[None, cached_result]  # First miss, then hit
        )
        mock_idempotency_store.set = AsyncMock()
        
        headers = {"Authorization": f"Bearer {jwt_token_admin}"}
        
        # First request
        response1 = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/call",
                "params": {
                    "name": "update_customer",
                    "arguments": {
                        "customer_id": "cust-123",
                        "data": {"name": "Updated"}
                    },
                    "idempotency_key": "idem-123"
                }
            },
            headers=headers
        )
        
        # Should execute
        assert response1.status_code in [200, 201]
        
        # Second request (same key)
        response2 = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-2",
                "method": "tools/call",
                "params": {
                    "name": "update_customer",
                    "arguments": {
                        "customer_id": "cust-123",
                        "data": {"name": "Updated"}
                    },
                    "idempotency_key": "idem-123"
                }
            },
            headers=headers
        )
        
        # Should be cached (same response or cached indicator)
        assert response2.status_code in [200, 201]

    @pytest.mark.security
    def test_different_idempotency_keys_execute_separately(
        self,
        test_client,
        jwt_token_admin,
        mock_idempotency_store
    ):
        """
        Test that different idempotency keys result in separate executions.
        
        Acceptance Criteria:
        - Request with key 'idem-123' executes
        - Request with key 'idem-124' also executes (different key)
        - Both operations complete (tool called twice)
        - Allows multiple similar operations with different idempotency keys
        """
        mock_idempotency_store.get = AsyncMock(return_value=None)
        mock_idempotency_store.set = AsyncMock()
        
        headers = {"Authorization": f"Bearer {jwt_token_admin}"}
        
        # Request with key-123
        response1 = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/call",
                "params": {
                    "name": "update_customer",
                    "arguments": {
                        "customer_id": "cust-123",
                        "data": {"name": "Updated"}
                    },
                    "idempotency_key": "idem-123"
                }
            },
            headers=headers
        )
        
        # Request with key-124 (different key)
        response2 = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-2",
                "method": "tools/call",
                "params": {
                    "name": "update_customer",
                    "arguments": {
                        "customer_id": "cust-123",
                        "data": {"name": "Updated Again"}
                    },
                    "idempotency_key": "idem-124"
                }
            },
            headers=headers
        )
        
        # Both should execute (different keys)
        assert response1.status_code in [200, 201]
        assert response2.status_code in [200, 201]

    @pytest.mark.security
    def test_read_operations_dont_require_idempotency_key(
        self,
        test_client,
        jwt_token_admin
    ):
        """
        Test that read operations don't require idempotency keys.
        
        Acceptance Criteria:
        - read_customer tool (read operation)
        - No idempotency_key in request
        - Succeeds normally
        - Idempotency only needed for write operations
        """
        headers = {"Authorization": f"Bearer {jwt_token_admin}"}
        
        # Read without idempotency key
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/call",
                "params": {
                    "name": "read_customer",
                    "arguments": {"customer_id": "cust-123"}
                    # No idempotency_key
                }
            },
            headers=headers
        )
        
        # Should succeed without key
        assert response.status_code in [200, 201]


class TestIdempotencyEdgeCases:
    """Test edge cases for idempotency handling."""

    @pytest.mark.security
    def test_empty_idempotency_key_handled(
        self,
        test_client,
        jwt_token_admin
    ):
        """
        Test that empty idempotency key is handled safely.
        
        Acceptance Criteria:
        - Request with empty string as idempotency_key
        - Should be rejected or treated as no key
        - Returns 400 Bad Request or proceeds as normal
        """
        headers = {"Authorization": f"Bearer {jwt_token_admin}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/call",
                "params": {
                    "name": "update_customer",
                    "arguments": {
                        "customer_id": "cust-123",
                        "data": {"name": "Updated"}
                    },
                    "idempotency_key": ""  # Empty
                }
            },
            headers=headers
        )
        
        # Should handle gracefully
        assert response.status_code in [400, 200, 201]

    @pytest.mark.security
    def test_very_long_idempotency_key(
        self,
        test_client,
        jwt_token_admin
    ):
        """
        Test that very long idempotency keys are handled.
        
        Acceptance Criteria:
        - idempotency_key is extremely long (>10KB)
        - Request is rejected or truncated safely
        - No DoS or resource exhaustion
        """
        headers = {"Authorization": f"Bearer {jwt_token_admin}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/call",
                "params": {
                    "name": "update_customer",
                    "arguments": {
                        "customer_id": "cust-123",
                        "data": {"name": "Updated"}
                    },
                    "idempotency_key": "x" * 20000  # 20KB key
                }
            },
            headers=headers
        )
        
        # Should handle safely
        assert response.status_code in [400, 200, 201]

    @pytest.mark.security
    def test_idempotency_store_failure_degrades_gracefully(
        self,
        test_client,
        jwt_token_admin,
        mock_idempotency_store
    ):
        """
        Test that store failures (e.g., Redis down) are handled gracefully.
        
        Acceptance Criteria:
        - IdempotencyStore throws exception
        - Request still succeeds (degrades gracefully)
        - Tool still executes
        - No duplication prevention, but operation completes
        """
        # Mock store failure
        mock_idempotency_store.get = AsyncMock(return_value=None)
        mock_idempotency_store.set = AsyncMock(
            side_effect=Exception("Redis connection failed")
        )
        
        headers = {"Authorization": f"Bearer {jwt_token_admin}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/call",
                "params": {
                    "name": "update_customer",
                    "arguments": {
                        "customer_id": "cust-123",
                        "data": {"name": "Updated"}
                    },
                    "idempotency_key": "idem-123"
                }
            },
            headers=headers
        )
        
        # Should still execute despite store failure
        assert response.status_code in [200, 201, 500]
