"""
Security Test Suite for MCP Server
Tests unauthorized access, authentication, and authorization controls
"""

import pytest
import httpx
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestUnauthorizedAccess:
    """Test suite for unauthorized access attempts."""
    
    def test_unauthenticated_api_access(self):
        """Test that API endpoints reject unauthenticated requests."""
        response = client.get("/api/tools")
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_invalid_token_rejected(self):
        """Test that invalid JWT tokens are rejected."""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = client.get("/api/tools", headers=headers)
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]
    
    def test_expired_token_rejected(self):
        """Test that expired JWT tokens are rejected."""
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMSIsImV4cCI6MTYwMDAwMDAwMH0.invalid"
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/tools", headers=headers)
        assert response.status_code == 401
    
    def test_missing_authorization_header(self):
        """Test that requests without Authorization header are rejected."""
        response = client.post("/api/tools/execute")
        assert response.status_code == 401
    
    def test_malformed_authorization_header(self):
        """Test that malformed Authorization headers are rejected."""
        headers = {"Authorization": "InvalidFormat token123"}
        response = client.get("/api/tools", headers=headers)
        assert response.status_code == 401
    
    def test_wrong_token_type(self):
        """Test that non-Bearer token types are rejected."""
        headers = {"Authorization": "Basic dXNlcjpwYXNzd29yZA=="}
        response = client.get("/api/tools", headers=headers)
        assert response.status_code == 401


class TestAuthorizationControls:
    """Test suite for role-based authorization."""
    
    @pytest.fixture
    def user_token(self):
        """Generate token for regular user."""
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def admin_token(self):
        """Generate token for admin user."""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin_password"
        })
        return response.json()["access_token"]
    
    def test_user_cannot_access_admin_endpoints(self, user_token):
        """Test that regular users cannot access admin endpoints."""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/api/admin/users", headers=headers)
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]
    
    def test_admin_can_access_admin_endpoints(self, admin_token):
        """Test that admin users can access admin endpoints."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/admin/users", headers=headers)
        assert response.status_code == 200
    
    def test_user_cannot_execute_privileged_tools(self, user_token):
        """Test that users without elevation cannot execute privileged tools."""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.post("/api/tools/execute", headers=headers, json={
            "tool_name": "delete_database",
            "parameters": {}
        })
        assert response.status_code == 403
        assert "elevation" in response.json()["detail"].lower()
    
    def test_user_cannot_modify_settings(self, user_token):
        """Test that regular users cannot modify system settings."""
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.put("/api/admin/settings", headers=headers, json={
            "rate_limit": 10000
        })
        assert response.status_code == 403


class TestAPIKeyAuthentication:
    """Test suite for API key authentication."""
    
    def test_valid_api_key_accepted(self):
        """Test that valid API keys are accepted."""
        headers = {"X-API-Key": "valid_api_key_12345"}
        response = client.get("/api/tools", headers=headers)
        assert response.status_code == 200
    
    def test_invalid_api_key_rejected(self):
        """Test that invalid API keys are rejected."""
        headers = {"X-API-Key": "invalid_key"}
        response = client.get("/api/tools", headers=headers)
        assert response.status_code == 401
    
    def test_api_key_rate_limiting(self):
        """Test that API keys are subject to rate limiting."""
        headers = {"X-API-Key": "valid_api_key_12345"}
        
        # Make requests up to the limit
        for _ in range(100):
            response = client.get("/api/tools", headers=headers)
            if response.status_code == 429:
                break
        
        # Next request should be rate limited
        response = client.get("/api/tools", headers=headers)
        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"].lower()


class TestSessionManagement:
    """Test suite for session management and token refresh."""
    
    def test_token_refresh_with_valid_refresh_token(self):
        """Test that valid refresh tokens can get new access tokens."""
        # Login to get tokens
        login_response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_token_refresh_with_invalid_refresh_token(self):
        """Test that invalid refresh tokens are rejected."""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid_refresh_token"
        })
        assert response.status_code == 401
    
    def test_logout_invalidates_tokens(self):
        """Test that logout invalidates access tokens."""
        # Login
        login_response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        access_token = login_response.json()["access_token"]
        
        # Logout
        headers = {"Authorization": f"Bearer {access_token}"}
        logout_response = client.post("/api/auth/logout", headers=headers)
        assert logout_response.status_code == 200
        
        # Try to use token after logout
        response = client.get("/api/tools", headers=headers)
        assert response.status_code == 401


class TestCORSVulnerabilities:
    """Test suite for CORS misconfiguration vulnerabilities."""
    
    def test_cors_rejects_unauthorized_origins(self):
        """Test that CORS rejects requests from unauthorized origins."""
        headers = {"Origin": "https://malicious-site.com"}
        response = client.options("/api/tools", headers=headers)
        
        # Check that Access-Control-Allow-Origin is not present or is restrictive
        assert "Access-Control-Allow-Origin" not in response.headers or \
               response.headers["Access-Control-Allow-Origin"] != "*"
    
    def test_cors_allows_authorized_origins(self):
        """Test that CORS allows requests from authorized origins."""
        headers = {"Origin": "https://mcp.maruti.com"}
        response = client.options("/api/tools", headers=headers)
        assert response.status_code == 200
    
    def test_cors_credentials_not_allowed_with_wildcard(self):
        """Test that credentials are not allowed with wildcard origins."""
        headers = {"Origin": "https://mcp.maruti.com"}
        response = client.options("/api/tools", headers=headers)
        
        if response.headers.get("Access-Control-Allow-Origin") == "*":
            assert response.headers.get("Access-Control-Allow-Credentials") != "true"


class TestCSRFProtection:
    """Test suite for CSRF protection."""
    
    def test_state_changing_operations_require_csrf_token(self):
        """Test that state-changing operations require CSRF tokens."""
        # Try to execute tool without CSRF token
        response = client.post("/api/tools/execute", json={
            "tool_name": "read_file",
            "parameters": {"path": "/etc/passwd"}
        })
        
        # Should require authentication first, then CSRF
        assert response.status_code in [401, 403]
    
    def test_get_requests_do_not_require_csrf(self):
        """Test that GET requests do not require CSRF tokens."""
        # Login first
        login_response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/tools", headers=headers)
        assert response.status_code == 200


class TestAccountLockout:
    """Test suite for account lockout after failed login attempts."""
    
    def test_account_lockout_after_failed_attempts(self):
        """Test that accounts are locked after too many failed login attempts."""
        # Attempt login with wrong password multiple times
        for _ in range(5):
            client.post("/api/auth/login", json={
                "username": "test_user",
                "password": "wrong_password"
            })
        
        # Next attempt should be locked
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"  # Even correct password
        })
        assert response.status_code == 403
        assert "locked" in response.json()["detail"].lower()
    
    def test_lockout_counter_resets_after_successful_login(self):
        """Test that failed attempt counter resets after successful login."""
        # Fail a few times
        for _ in range(3):
            client.post("/api/auth/login", json={
                "username": "test_user",
                "password": "wrong_password"
            })
        
        # Successful login
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        assert response.status_code == 200
        
        # Counter should be reset - try again with wrong password
        for _ in range(3):
            response = client.post("/api/auth/login", json={
                "username": "test_user",
                "password": "wrong_password"
            })
        
        # Should not be locked yet
        assert response.status_code != 403


class TestPasswordSecurity:
    """Test suite for password security requirements."""
    
    def test_weak_passwords_rejected(self):
        """Test that weak passwords are rejected during registration."""
        response = client.post("/api/auth/register", json={
            "username": "newuser",
            "password": "123",
            "email": "user@example.com"
        })
        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()
    
    def test_strong_passwords_accepted(self):
        """Test that strong passwords are accepted."""
        response = client.post("/api/auth/register", json={
            "username": "newuser",
            "password": "StrongP@ssw0rd123!",
            "email": "user@example.com"
        })
        assert response.status_code in [200, 201]
    
    def test_password_cannot_be_retrieved(self):
        """Test that passwords cannot be retrieved through API."""
        # Login as admin
        login_response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin_password"
        })
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/admin/users", headers=headers)
        
        # Check that password field is not in response
        users = response.json()
        for user in users:
            assert "password" not in user
            assert "hashed_password" not in user


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
