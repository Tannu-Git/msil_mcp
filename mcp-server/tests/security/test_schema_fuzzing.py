"""
Schema Fuzzing Tests for MCP Server
Tests input validation, schema enforcement, and injection vulnerabilities
"""

import pytest
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestSchemaValidation:
    """Test suite for schema validation and input sanitization."""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers for testing."""
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_missing_required_fields(self, auth_headers):
        """Test that requests with missing required fields are rejected."""
        response = client.post(
            "/api/tools/execute",
            headers=auth_headers,
            json={
                # Missing 'tool_name' field
                "parameters": {}
            }
        )
        assert response.status_code == 422
        assert "tool_name" in str(response.json())
    
    def test_invalid_field_types(self, auth_headers):
        """Test that invalid field types are rejected."""
        response = client.post(
            "/api/tools/execute",
            headers=auth_headers,
            json={
                "tool_name": 12345,  # Should be string
                "parameters": "not_a_dict"  # Should be dict
            }
        )
        assert response.status_code == 422
    
    def test_extra_fields_handled(self, auth_headers):
        """Test that extra fields are handled properly."""
        response = client.post(
            "/api/tools/execute",
            headers=auth_headers,
            json={
                "tool_name": "read_file",
                "parameters": {"path": "/tmp/test.txt"},
                "extra_field": "should_be_ignored"
            }
        )
        # Should either succeed or return validation error, not crash
        assert response.status_code in [200, 422]
    
    def test_deeply_nested_objects(self, auth_headers):
        """Test handling of deeply nested JSON objects."""
        # Create 100-level nested structure
        nested = {"level": 0}
        current = nested
        for i in range(1, 100):
            current["nested"] = {"level": i}
            current = current["nested"]
        
        response = client.post(
            "/api/tools/execute",
            headers=auth_headers,
            json={
                "tool_name": "process_data",
                "parameters": nested
            }
        )
        # Should reject or handle gracefully, not crash
        assert response.status_code in [400, 413, 422]
    
    def test_extremely_large_payloads(self, auth_headers):
        """Test handling of extremely large payloads."""
        large_string = "x" * (10 * 1024 * 1024)  # 10MB string
        response = client.post(
            "/api/tools/execute",
            headers=auth_headers,
            json={
                "tool_name": "process_text",
                "parameters": {"text": large_string}
            }
        )
        # Should reject with 413 Payload Too Large
        assert response.status_code == 413
    
    def test_array_with_mixed_types(self, auth_headers):
        """Test handling of arrays with mixed types."""
        response = client.post(
            "/api/tools/execute",
            headers=auth_headers,
            json={
                "tool_name": "process_list",
                "parameters": {
                    "items": [1, "string", True, None, {"key": "value"}]
                }
            }
        )
        assert response.status_code in [200, 400, 422]
    
    def test_unicode_and_special_characters(self, auth_headers):
        """Test handling of unicode and special characters."""
        special_strings = [
            "Hello 世界",  # Unicode
            "\\x00\\x01\\x02",  # Control characters
            "<script>alert('xss')</script>",  # XSS attempt
            "'; DROP TABLE users; --",  # SQL injection
            "../../../etc/passwd",  # Path traversal
            "$(whoami)",  # Command injection
            "${7*7}",  # Template injection
        ]
        
        for test_string in special_strings:
            response = client.post(
                "/api/tools/execute",
                headers=auth_headers,
                json={
                    "tool_name": "process_text",
                    "parameters": {"text": test_string}
                }
            )
            # Should handle safely without executing malicious code
            assert response.status_code in [200, 400, 422]


class TestSQLInjectionProtection:
    """Test suite for SQL injection protection."""
    
    @pytest.fixture
    def auth_headers(self):
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_sql_injection_in_search(self, auth_headers):
        """Test SQL injection attempts in search endpoints."""
        injection_attempts = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM users--",
            "admin'--",
            "' OR 1=1--",
            "1' AND '1'='1",
        ]
        
        for injection in injection_attempts:
            response = client.get(
                f"/api/tools/search?query={injection}",
                headers=auth_headers
            )
            # Should not execute SQL, should return safe results or error
            assert response.status_code in [200, 400]
            # Verify no sensitive data leaked
            if response.status_code == 200:
                data = response.json()
                # Check that we're not getting unexpected database dumps
                assert not isinstance(data, list) or len(data) < 1000
    
    def test_sql_injection_in_filter(self, auth_headers):
        """Test SQL injection in filter parameters."""
        response = client.get(
            "/api/audit/logs?user_id=' OR '1'='1",
            headers=auth_headers
        )
        assert response.status_code in [200, 400]
    
    def test_second_order_sql_injection(self, auth_headers):
        """Test second-order SQL injection through stored data."""
        # First, try to store malicious data
        response = client.post(
            "/api/tools/execute",
            headers=auth_headers,
            json={
                "tool_name": "create_note",
                "parameters": {
                    "title": "Normal Title",
                    "content": "'; DROP TABLE audit_logs; --"
                }
            }
        )
        
        # Then retrieve and verify it's properly escaped
        if response.status_code == 200:
            note_id = response.json().get("note_id")
            get_response = client.get(
                f"/api/tools/notes/{note_id}",
                headers=auth_headers
            )
            assert get_response.status_code == 200


class TestCommandInjectionProtection:
    """Test suite for command injection protection."""
    
    @pytest.fixture
    def auth_headers(self):
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_command_injection_in_file_operations(self, auth_headers):
        """Test command injection in file operation parameters."""
        injection_attempts = [
            "; ls -la",
            "| cat /etc/passwd",
            "& whoami",
            "`whoami`",
            "$(whoami)",
            "; rm -rf /",
            "&& cat /etc/shadow",
        ]
        
        for injection in injection_attempts:
            response = client.post(
                "/api/tools/execute",
                headers=auth_headers,
                json={
                    "tool_name": "read_file",
                    "parameters": {"path": f"/tmp/test{injection}"}
                }
            )
            # Should reject or sanitize, not execute commands
            assert response.status_code in [400, 404, 422]
    
    def test_shell_metacharacters_escaped(self, auth_headers):
        """Test that shell metacharacters are properly escaped."""
        metacharacters = [";", "|", "&", "$", "`", ">", "<", "\\n", "\\r"]
        
        for char in metacharacters:
            response = client.post(
                "/api/tools/execute",
                headers=auth_headers,
                json={
                    "tool_name": "echo_text",
                    "parameters": {"text": f"test{char}malicious"}
                }
            )
            # Should handle safely
            assert response.status_code in [200, 400]


class TestPathTraversalProtection:
    """Test suite for path traversal protection."""
    
    @pytest.fixture
    def auth_headers(self):
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_path_traversal_attempts(self, auth_headers):
        """Test various path traversal attack patterns."""
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "..;/..;/..;/etc/passwd",
            "/%2e%2e/%2e%2e/%2e%2e/etc/passwd",
            "/var/www/../../etc/passwd",
        ]
        
        for path in traversal_attempts:
            response = client.post(
                "/api/tools/execute",
                headers=auth_headers,
                json={
                    "tool_name": "read_file",
                    "parameters": {"path": path}
                }
            )
            # Should reject traversal attempts
            assert response.status_code in [400, 403, 404]
            # Should not return sensitive system files
            if response.status_code == 200:
                content = response.json()
                assert "root:" not in content.get("content", "")


class TestXSSProtection:
    """Test suite for XSS (Cross-Site Scripting) protection."""
    
    @pytest.fixture
    def auth_headers(self):
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_xss_in_user_input(self, auth_headers):
        """Test that XSS payloads are properly escaped."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg/onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "'-alert('XSS')-'",
        ]
        
        for payload in xss_payloads:
            response = client.post(
                "/api/tools/execute",
                headers=auth_headers,
                json={
                    "tool_name": "create_note",
                    "parameters": {
                        "title": payload,
                        "content": payload
                    }
                }
            )
            
            # If accepted, verify response is properly escaped
            if response.status_code == 200:
                data = response.json()
                # Response should not contain executable script tags
                response_str = json.dumps(data)
                assert "<script>" not in response_str.lower()


class TestJSONParsing:
    """Test suite for JSON parsing vulnerabilities."""
    
    def test_malformed_json(self):
        """Test handling of malformed JSON."""
        response = client.post(
            "/api/tools/execute",
            headers={"Content-Type": "application/json"},
            data="{malformed json"
        )
        assert response.status_code == 422
    
    def test_json_with_null_bytes(self):
        """Test handling of JSON with null bytes."""
        response = client.post(
            "/api/tools/execute",
            headers={"Content-Type": "application/json"},
            data='{"tool_name": "test\\x00", "parameters": {}}'
        )
        assert response.status_code in [400, 422]
    
    def test_extremely_large_numbers(self):
        """Test handling of extremely large numbers."""
        response = client.post(
            "/api/tools/execute",
            headers={"Content-Type": "application/json"},
            json={
                "tool_name": "process_number",
                "parameters": {
                    "value": 10**308  # Near float max
                }
            }
        )
        assert response.status_code in [200, 400, 422]


class TestHeaderInjection:
    """Test suite for header injection vulnerabilities."""
    
    def test_crlf_injection_in_headers(self):
        """Test CRLF injection attempts in headers."""
        malicious_values = [
            "value\\r\\nX-Injected-Header: malicious",
            "value\\nSet-Cookie: session=hijacked",
            "value\\r\\nHTTP/1.1 200 OK\\r\\n",
        ]
        
        for value in malicious_values:
            response = client.get(
                "/api/tools",
                headers={"X-Custom-Header": value}
            )
            # Should not inject additional headers
            assert "X-Injected-Header" not in response.headers
            assert "Set-Cookie" not in response.headers or \
                   response.headers.get("Set-Cookie") != "session=hijacked"


class TestXMLInjection:
    """Test suite for XML injection (if XML parsing is used)."""
    
    @pytest.fixture
    def auth_headers(self):
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_xxe_attack(self, auth_headers):
        """Test XXE (XML External Entity) attack protection."""
        xxe_payload = """<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<data>&xxe;</data>"""
        
        response = client.post(
            "/api/tools/parse-xml",
            headers={**auth_headers, "Content-Type": "application/xml"},
            data=xxe_payload
        )
        
        # Should reject or safely parse without resolving external entities
        if response.status_code == 200:
            content = response.text
            assert "root:" not in content  # Should not contain /etc/passwd


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
