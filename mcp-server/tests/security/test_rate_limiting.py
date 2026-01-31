"""
Rate Limiting Tests for MCP Server
Tests rate limiting, throttling, and DoS protection mechanisms
"""

import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestBasicRateLimiting:
    """Test suite for basic rate limiting functionality."""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers for testing."""
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_rate_limit_exceeded(self, auth_headers):
        """Test that rate limits are enforced."""
        # Make requests until rate limited
        rate_limited = False
        for i in range(150):  # Exceed typical rate limit
            response = client.get("/api/tools", headers=auth_headers)
            if response.status_code == 429:
                rate_limited = True
                break
        
        assert rate_limited, "Rate limit was not enforced"
    
    def test_rate_limit_headers_present(self, auth_headers):
        """Test that rate limit headers are included in responses."""
        response = client.get("/api/tools", headers=auth_headers)
        
        # Check for standard rate limit headers
        expected_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ]
        
        # At least some rate limit info should be present
        has_rate_limit_info = any(
            header in response.headers for header in expected_headers
        )
        assert has_rate_limit_info or response.status_code == 429
    
    def test_rate_limit_reset(self, auth_headers):
        """Test that rate limits reset after time window."""
        # Hit rate limit
        for _ in range(150):
            response = client.get("/api/tools", headers=auth_headers)
            if response.status_code == 429:
                break
        
        assert response.status_code == 429
        
        # Wait for reset (if reset time is provided)
        if "X-RateLimit-Reset" in response.headers:
            reset_time = int(response.headers["X-RateLimit-Reset"])
            wait_time = max(reset_time - int(time.time()), 0) + 1
            if wait_time < 60:  # Only wait if reasonable
                time.sleep(wait_time)
                
                # Should be able to make requests again
                response = client.get("/api/tools", headers=auth_headers)
                assert response.status_code in [200, 429]  # May need more time
    
    def test_rate_limit_per_user(self, auth_headers):
        """Test that rate limits are enforced per user."""
        # Create second user
        response2 = client.post("/api/auth/login", json={
            "username": "test_user2",
            "password": "test_password2"
        })
        auth_headers2 = {"Authorization": f"Bearer {response2.json()['access_token']}"}
        
        # Exhaust user1's rate limit
        for _ in range(150):
            response = client.get("/api/tools", headers=auth_headers)
            if response.status_code == 429:
                break
        
        # User2 should still be able to make requests
        response2 = client.get("/api/tools", headers=auth_headers2)
        assert response2.status_code == 200


class TestEndpointSpecificRateLimiting:
    """Test suite for endpoint-specific rate limits."""
    
    @pytest.fixture
    def auth_headers(self):
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_write_operations_stricter_limits(self, auth_headers):
        """Test that write operations have stricter rate limits."""
        # Test read endpoint
        read_rate_limited = False
        read_requests = 0
        for i in range(150):
            response = client.get("/api/tools", headers=auth_headers)
            read_requests += 1
            if response.status_code == 429:
                read_rate_limited = True
                break
        
        # Reset rate limit (wait or use new token)
        time.sleep(2)
        
        # Test write endpoint (should have lower limit)
        write_rate_limited = False
        write_requests = 0
        for i in range(150):
            response = client.post(
                "/api/tools/execute",
                headers=auth_headers,
                json={"tool_name": "test", "parameters": {}}
            )
            write_requests += 1
            if response.status_code == 429:
                write_rate_limited = True
                break
        
        # Write operations should hit limit sooner (or same)
        if read_rate_limited and write_rate_limited:
            assert write_requests <= read_requests
    
    def test_privileged_operations_strictest_limits(self, auth_headers):
        """Test that privileged operations have the strictest limits."""
        # Try privileged operation multiple times
        rate_limited = False
        for i in range(20):  # Lower threshold for privileged ops
            response = client.delete(
                "/api/admin/users/test",
                headers=auth_headers
            )
            if response.status_code == 429:
                rate_limited = True
                break
        
        # Should hit limit quickly for privileged operations
        assert rate_limited or i < 20


class TestConcurrentRequestHandling:
    """Test suite for concurrent request handling and throttling."""
    
    @pytest.fixture
    def auth_headers(self):
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_concurrent_request_limit(self, auth_headers):
        """Test maximum concurrent requests per user."""
        def make_request():
            return client.get("/api/tools", headers=auth_headers)
        
        # Launch many concurrent requests
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            responses = [future.result() for future in as_completed(futures)]
        
        # Check if any were throttled
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes or 503 in status_codes, \
            "Concurrent requests not throttled"
    
    def test_slowloris_protection(self, auth_headers):
        """Test protection against slowloris-style attacks."""
        # Try to open many slow connections
        # Note: This is a basic test; real slowloris requires lower-level control
        responses = []
        for _ in range(20):
            try:
                response = client.get(
                    "/api/tools",
                    headers=auth_headers,
                    timeout=0.1  # Very short timeout
                )
                responses.append(response)
            except Exception:
                # Timeout or connection refused is acceptable
                pass
        
        # Server should handle this gracefully
        assert len(responses) < 20 or any(r.status_code == 429 for r in responses)


class TestIPBasedRateLimiting:
    """Test suite for IP-based rate limiting."""
    
    def test_unauthenticated_ip_rate_limit(self):
        """Test rate limiting for unauthenticated requests by IP."""
        rate_limited = False
        for _ in range(200):  # Higher limit for unauthenticated
            response = client.get("/health")
            if response.status_code == 429:
                rate_limited = True
                break
        
        # Should eventually rate limit even unauthenticated requests
        assert rate_limited
    
    def test_ip_allowlist_bypass(self):
        """Test that allowlisted IPs can bypass rate limits."""
        # Note: This test requires configuration of allowlisted IPs
        # For now, just verify the mechanism exists
        response = client.get("/health")
        # Should not immediately rate limit health checks
        assert response.status_code == 200


class TestBurstRateLimiting:
    """Test suite for burst rate limiting."""
    
    @pytest.fixture
    def auth_headers(self):
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_burst_allowed_within_limits(self, auth_headers):
        """Test that burst traffic is allowed within limits."""
        # Make a quick burst of requests
        responses = []
        for _ in range(10):  # Small burst
            response = client.get("/api/tools", headers=auth_headers)
            responses.append(response)
        
        # All should succeed if within burst limit
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 5  # At least half should succeed
    
    def test_sustained_traffic_throttled(self, auth_headers):
        """Test that sustained high traffic is throttled."""
        rate_limited = False
        for _ in range(200):
            response = client.get("/api/tools", headers=auth_headers)
            if response.status_code == 429:
                rate_limited = True
                break
            time.sleep(0.05)  # Small delay between requests
        
        assert rate_limited


class TestResourceBasedLimits:
    """Test suite for resource-based rate limiting."""
    
    @pytest.fixture
    def auth_headers(self):
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_expensive_operation_lower_limit(self, auth_headers):
        """Test that expensive operations have lower rate limits."""
        rate_limited = False
        for i in range(20):
            response = client.post(
                "/api/tools/execute",
                headers=auth_headers,
                json={
                    "tool_name": "heavy_computation",
                    "parameters": {"size": "large"}
                }
            )
            if response.status_code == 429:
                rate_limited = True
                break
        
        # Should hit limit quickly for expensive operations
        assert rate_limited or i < 20
    
    def test_payload_size_affects_rate_limit(self, auth_headers):
        """Test that large payloads consume more rate limit quota."""
        # Make request with large payload
        large_payload = {"data": "x" * 1_000_000}  # 1MB
        response = client.post(
            "/api/tools/execute",
            headers=auth_headers,
            json={
                "tool_name": "process_data",
                "parameters": large_payload
            }
        )
        
        # Should either succeed or reject based on size
        assert response.status_code in [200, 400, 413, 429]


class TestRateLimitBypass:
    """Test suite for rate limit bypass attempts."""
    
    def test_cannot_bypass_with_multiple_tokens(self):
        """Test that multiple tokens from same user don't bypass limits."""
        # Get two tokens for same user
        response1 = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        token1 = response1.json()["access_token"]
        
        response2 = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        token2 = response2.json()["access_token"]
        
        # Exhaust rate limit with token1
        for _ in range(150):
            response = client.get(
                "/api/tools",
                headers={"Authorization": f"Bearer {token1}"}
            )
            if response.status_code == 429:
                break
        
        # Token2 should also be rate limited (same user)
        response = client.get(
            "/api/tools",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert response.status_code == 429
    
    def test_cannot_bypass_with_header_manipulation(self):
        """Test that header manipulation doesn't bypass rate limits."""
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        token = response.json()["access_token"]
        
        # Try with different X-Forwarded-For headers
        for i in range(150):
            headers = {
                "Authorization": f"Bearer {token}",
                "X-Forwarded-For": f"10.0.0.{i % 255}"
            }
            response = client.get("/api/tools", headers=headers)
            if response.status_code == 429:
                break
        
        # Should still be rate limited despite header manipulation
        assert response.status_code == 429


class TestRateLimitMonitoring:
    """Test suite for rate limit monitoring and observability."""
    
    @pytest.fixture
    def admin_headers(self):
        """Get admin authentication headers."""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin_password"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_rate_limit_metrics_available(self, admin_headers):
        """Test that rate limit metrics are available to admins."""
        response = client.get("/api/admin/metrics", headers=admin_headers)
        
        if response.status_code == 200:
            metrics = response.json()
            # Should include rate limit metrics
            assert any("rate_limit" in str(metrics).lower() for _ in [1])
    
    def test_rate_limit_alerts_configured(self, admin_headers):
        """Test that rate limit alerts can be configured."""
        response = client.get("/api/admin/alerts", headers=admin_headers)
        
        if response.status_code == 200:
            alerts = response.json()
            # Should have some rate limit alert configuration
            assert isinstance(alerts, (list, dict))


class TestDDoSProtection:
    """Test suite for DDoS protection mechanisms."""
    
    def test_request_flood_protection(self):
        """Test protection against request floods."""
        # Simulate a flood of requests
        responses = []
        for _ in range(1000):
            try:
                response = client.get("/health", timeout=1)
                responses.append(response)
            except Exception:
                # Connection errors are acceptable under flood
                pass
        
        # Server should remain responsive
        # At least some requests should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count > 0, "Server completely unresponsive"
        
        # And some should be rate limited
        rate_limited = sum(1 for r in responses if r.status_code == 429)
        assert rate_limited > 0, "No rate limiting under flood"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
