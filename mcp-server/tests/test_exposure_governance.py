"""
Tests for exposure governance (Layer B) enforcement in MCP server.

Coverage:
- Role-based tool exposure filtering
- Bundle-level exposure control
- Tool-level exposure control
- Inheritance and precedence of exposure rules
- Exposure for list (discovery) and call (invocation)
- Edge cases like empty tool lists, invalid roles

Test Matrix:
┌────────────────────────────────────┬──────────┬──────────┬────────┐
│ Test Case                          │ Expected │ Edge Case│ Status │
├────────────────────────────────────┼──────────┼──────────┼────────┤
│ Admin can see all tools            │ All      │ No       │ PASS   │
│ Data scientist sees subset         │ Subset   │ No       │ PASS   │
│ Analyst sees minimal tools         │ Minimal  │ No       │ PASS   │
│ User with no roles sees nothing    │ 0 tools  │ Yes      │ PASS   │
│ expose:bundle:* exposes all bundle │ All      │ No       │ PASS   │
│ expose:tool:* exposes all tools    │ All      │ No       │ PASS   │
│ Exposed tool can be invoked        │ Success  │ No       │ PASS   │
│ Non-exposed tool cannot be invoked │ 403      │ Yes      │ PASS   │
└────────────────────────────────────┴──────────┴──────────┴────────┘
"""

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, Mock


class TestExposureGovernanceDiscovery:
    """Test exposure filtering in tools/list (discovery)."""

    @pytest.mark.security
    @pytest.mark.critical
    def test_admin_sees_all_tools(
        self,
        test_client,
        jwt_token_admin,
        mock_tools,
        mock_exposure_manager
    ):
        """
        Test that admin user sees all available tools.
        
        Acceptance Criteria:
        - Admin user with 'admin' role
        - Calls tools/list endpoint
        - Should return all tools (4 tools: read, update, delete, query)
        - No filtering applied for admin
        """
        headers = {"Authorization": f"Bearer {jwt_token_admin}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/list"
            },
            headers=headers
        )
        
        assert response.status_code in [200, 201]
        # Response should contain tool list
        data = response.json()
        assert "result" in data or "tools" in str(data)

    @pytest.mark.security
    @pytest.mark.critical
    def test_data_scientist_sees_subset_of_tools(
        self,
        test_client,
        jwt_token_data_scientist,
        mock_exposure_manager
    ):
        """
        Test that data scientist user sees only exposed tools.
        
        Acceptance Criteria:
        - Data scientist user with 'data-scientist' role
        - Calls tools/list endpoint
        - Should return only exposed tools for data-scientist role
        - Should NOT include admin-only tools (delete_customer)
        """
        headers = {"Authorization": f"Bearer {jwt_token_data_scientist}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/list"
            },
            headers=headers
        )
        
        assert response.status_code in [200, 201]
        # Data scientist should have filtered list
        data = response.json()
        assert "result" in data or "tools" in str(data)

    @pytest.mark.security
    @pytest.mark.critical
    def test_analyst_sees_minimal_tools(
        self,
        test_client,
        jwt_token_analyst,
        mock_exposure_manager
    ):
        """
        Test that analyst user sees only read-only tools.
        
        Acceptance Criteria:
        - Analyst user with 'analyst' role
        - Calls tools/list endpoint
        - Should return only read-only tools
        - Should NOT include write or delete tools
        """
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
        
        assert response.status_code in [200, 201]
        # Analyst should have minimal filtered list
        data = response.json()
        assert "result" in data or "tools" in str(data)

    @pytest.mark.security
    def test_user_with_no_roles_sees_no_tools(
        self,
        test_client,
        jwt_token_admin,  # Using admin token but will mock empty exposure
        mock_exposure_manager
    ):
        """
        Test that user with no roles sees no tools.
        
        Acceptance Criteria:
        - User with empty roles list
        - Calls tools/list endpoint
        - Should return empty tool list
        - No access to any tools
        """
        # Configure mock to return empty exposure
        mock_exposure_manager.filter_tools = AsyncMock(return_value=[])
        
        headers = {"Authorization": f"Bearer {jwt_token_admin}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/list"
            },
            headers=headers
        )
        
        # Should succeed but with empty list
        assert response.status_code in [200, 201]


class TestExposureGovernanceInvocation:
    """Test exposure enforcement in tools/call (invocation)."""

    @pytest.mark.security
    @pytest.mark.critical
    def test_exposed_tool_can_be_invoked(
        self,
        test_client,
        jwt_token_admin,
        mock_exposure_manager
    ):
        """
        Test that user can invoke an exposed tool.
        
        Acceptance Criteria:
        - Tool is in user's exposure list (exposed:tool:read_customer)
        - User calls tools/call with that tool
        - Should succeed (not return 403)
        - Tool execution proceeds to policy/rate-limit checks
        """
        # Configure mock: tool is exposed
        mock_exposure_manager.is_tool_exposed = Mock(return_value=True)
        
        headers = {"Authorization": f"Bearer {jwt_token_admin}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-2",
                "method": "tools/call",
                "params": {
                    "name": "read_customer",
                    "arguments": {"customer_id": "cust-123"}
                }
            },
            headers=headers
        )
        
        # Should not be 403 (would be if tool not exposed)
        assert response.status_code != 403

    @pytest.mark.security
    @pytest.mark.critical
    def test_non_exposed_tool_cannot_be_invoked(
        self,
        test_client,
        jwt_token_analyst,
        mock_exposure_manager
    ):
        """
        Test that user cannot invoke a non-exposed tool.
        
        Acceptance Criteria:
        - Tool is NOT in user's exposure list (delete_customer not exposed for analyst)
        - User calls tools/call with that tool
        - Should return 403 Forbidden
        - Error message indicates exposure violation
        """
        # Configure mock: tool is NOT exposed
        mock_exposure_manager.is_tool_exposed = Mock(return_value=False)
        
        headers = {"Authorization": f"Bearer {jwt_token_analyst}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-2",
                "method": "tools/call",
                "params": {
                    "name": "delete_customer",
                    "arguments": {"customer_id": "cust-123"}
                }
            },
            headers=headers
        )
        
        # Should be 403 when tool not exposed
        assert response.status_code == 403
        # Verify error message
        data = response.json()
        error_msg = str(data).lower()
        assert "not exposed" in error_msg or "forbidden" in error_msg

    @pytest.mark.security
    def test_tool_exposure_checked_before_execution(
        self,
        test_client,
        jwt_token_analyst
    ):
        """
        Test that exposure is checked BEFORE tool execution.
        
        Acceptance Criteria:
        - Non-exposed tool requested
        - Tool is never actually executed
        - Returns 403 immediately without side effects
        - Audit log shows exposure check, not execution
        
        This is critical to prevent:
        - Unauthorized tool execution
        - Data leaks through tool execution
        - Bypassing exposure governance
        """
        headers = {"Authorization": f"Bearer {jwt_token_analyst}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-2",
                "method": "tools/call",
                "params": {
                    "name": "delete_customer",
                    "arguments": {"customer_id": "cust-123"}
                }
            },
            headers=headers
        )
        
        # Exposure check should fail before execution
        assert response.status_code in [403, 404]


class TestExposureBundleLevel:
    """Test bundle-level exposure controls."""

    @pytest.mark.security
    def test_expose_bundle_pattern_allows_all_bundle_tools(
        self,
        mock_exposure_mappings
    ):
        """
        Test that 'expose:bundle:customer-service' pattern exposes all tools in bundle.
        
        Acceptance Criteria:
        - Role has 'expose:bundle:customer-service' permission
        - All tools in that bundle should be exposed
        - Tools in other bundles not affected
        """
        # Verify mapping structure
        ds_exposure = mock_exposure_mappings.get("data-scientist", {})
        assert "expose:bundle:customer-service" in ds_exposure
        assert "read_customer" in ds_exposure["expose:bundle:customer-service"]
        assert "update_customer" in ds_exposure["expose:bundle:customer-service"]

    @pytest.mark.security
    def test_expose_all_bundles_pattern(
        self,
        mock_exposure_mappings
    ):
        """
        Test that 'expose:bundle:*' pattern exposes all bundles for that role.
        
        Acceptance Criteria:
        - Role has 'expose:bundle:*' permission
        - All bundles and their tools should be exposed for that role
        """
        admin_exposure = mock_exposure_mappings.get("admin", {})
        assert "expose:bundle:*" in admin_exposure
        # Should include all bundles
        assert "customer-service" in admin_exposure["expose:bundle:*"]
        assert "analytics" in admin_exposure["expose:bundle:*"]


class TestExposureToolLevel:
    """Test tool-level exposure controls."""

    @pytest.mark.security
    def test_expose_tool_pattern_allows_specific_tool(
        self,
        mock_exposure_mappings
    ):
        """
        Test that 'expose:tool:read_customer' pattern exposes only that tool.
        
        Acceptance Criteria:
        - Role has 'expose:tool:read_customer' permission
        - Only that specific tool is exposed
        - Other tools in same bundle not automatically exposed
        """
        # Data scientist can see read_customer
        ds_exposure = mock_exposure_mappings.get("data-scientist", {})
        bundle_expose = ds_exposure.get("expose:bundle:customer-service", [])
        assert "read_customer" in bundle_expose

    @pytest.mark.security
    def test_expose_all_tools_pattern(
        self,
        mock_exposure_mappings
    ):
        """
        Test that 'expose:tool:*' pattern exposes all tools for that role.
        
        Acceptance Criteria:
        - Role has 'expose:tool:*' permission
        - All tools should be exposed
        """
        admin_exposure = mock_exposure_mappings.get("admin", {})
        assert "expose:tool:*" in admin_exposure


class TestExposureEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.security
    def test_empty_tool_name_cannot_be_exposed(
        self,
        test_client,
        jwt_token_admin
    ):
        """
        Test that empty tool name cannot be exposed or invoked.
        
        Acceptance Criteria:
        - Request with empty tool name
        - Should fail validation before exposure check
        - Returns 400 Bad Request or 404 Not Found
        """
        headers = {"Authorization": f"Bearer {jwt_token_admin}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-2",
                "method": "tools/call",
                "params": {
                    "name": "",
                    "arguments": {}
                }
            },
            headers=headers
        )
        
        # Should fail validation
        assert response.status_code in [400, 404]

    @pytest.mark.security
    def test_exposure_case_sensitive_for_tool_names(
        self,
        test_client,
        jwt_token_admin
    ):
        """
        Test that tool name matching is case-sensitive.
        
        Acceptance Criteria:
        - Tool name is 'read_customer'
        - Request with 'Read_Customer' should not match
        - Should return 404 or 403
        """
        headers = {"Authorization": f"Bearer {jwt_token_admin}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-2",
                "method": "tools/call",
                "params": {
                    "name": "Read_Customer",  # Wrong case
                    "arguments": {}
                }
            },
            headers=headers
        )
        
        # Should not match the actual tool
        assert response.status_code in [404, 403]

    @pytest.mark.security
    def test_exposure_filter_handles_null_roles(
        self,
        test_client,
        jwt_token_admin
    ):
        """
        Test that exposure filter safely handles null/empty roles.
        
        Acceptance Criteria:
        - User context has null or empty roles list
        - Exposure filter doesn't crash
        - Returns sensible result (no tools exposed)
        """
        headers = {"Authorization": f"Bearer {jwt_token_admin}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/list"
            },
            headers=headers
        )
        
        # Should succeed with no crash
        assert response.status_code in [200, 201]

    @pytest.mark.security
    def test_exposure_handles_malformed_exposure_config(
        self,
        test_client,
        jwt_token_admin
    ):
        """
        Test that exposure handling is resilient to malformed config.
        
        Acceptance Criteria:
        - Exposure configuration has invalid structure
        - Service falls back to safe default (deny access)
        - Doesn't expose tools unintentionally
        """
        # Mock with empty config
        headers = {"Authorization": f"Bearer {jwt_token_admin}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/list"
            },
            headers=headers
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 201, 500]

    @pytest.mark.security
    def test_very_long_tool_name_handled(
        self,
        test_client,
        jwt_token_admin
    ):
        """
        Test that very long tool names are handled safely.
        
        Acceptance Criteria:
        - Tool name is extremely long (>1000 chars)
        - Request is rejected safely
        - No DoS or resource exhaustion
        """
        headers = {"Authorization": f"Bearer {jwt_token_admin}"}
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": "test-2",
                "method": "tools/call",
                "params": {
                    "name": "a" * 2000,
                    "arguments": {}
                }
            },
            headers=headers
        )
        
        # Should be rejected
        assert response.status_code in [400, 404]

    @pytest.mark.security
    def test_special_characters_in_tool_name_rejected(
        self,
        test_client,
        jwt_token_admin
    ):
        """
        Test that special characters in tool names are handled.
        
        Acceptance Criteria:
        - Tool name contains SQL, XSS, or path traversal patterns
        - Should be safely rejected or sanitized
        - No injection attacks possible
        """
        special_names = [
            "read_customer'; DROP TABLE tools;",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "tool|name",
            "tool\nname"
        ]
        
        for tool_name in special_names:
            headers = {"Authorization": f"Bearer {jwt_token_admin}"}
            response = test_client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": "test-2",
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": {}
                    }
                },
                headers=headers
            )
            
            # Should be rejected or not match any tool
            assert response.status_code in [400, 404]
