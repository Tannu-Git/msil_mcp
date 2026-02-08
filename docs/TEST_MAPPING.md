# Test Mapping and Execution Guide for MSIL MCP Server

## Overview

This document provides a comprehensive mapping of features/functionality to test cases, enabling QA engineers to:
- Understand what each test covers
- Map features to specific test files and test names
- Execute specific functionality tests
- Add new test cases for future features
- Understand positive/negative/edge case coverage

---

## Test File Structure

```
mcp-server/tests/
├── conftest.py                    # Shared fixtures and mocks
├── test_authentication.py         # Auth enforcement (401, JWT validation, DEMO_MODE)
├── test_exposure_governance.py   # Layer B: Role-based tool filtering
├── test_rate_limiting.py         # Rate limiting enforcement (429, retry-after)
├── test_policy_idempotency.py    # Layer A policy + idempotency key handling
├── test_audit_chat.py            # Audit logging and Chat API security
└── test_analytics.py             # Analytics endpoints and metrics
```

Each file contains multiple test classes and functions organized by feature.

---

## Quick Test Execution Guide

### Run All Tests
```bash
cd mcp-server
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_authentication.py -v
pytest tests/test_exposure_governance.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_authentication.py::TestAuthenticationBasics -v
pytest tests/test_rate_limiting.py::TestPerUserRateLimiting -v
```

### Run Specific Test
```bash
pytest tests/test_authentication.py::TestAuthenticationBasics::test_valid_jwt_token_accepted -v
```

### Run Critical Security Tests Only
```bash
pytest tests/ -m critical -v
```

### Run All Security Tests
```bash
pytest tests/ -m security -v
```

### Run with Coverage Report
```bash
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html to view coverage
```

### Run Tests in Parallel (faster)
```bash
pytest tests/ -v -n auto
```

---

## Functional Area 1: Authentication & Authorization

### Feature: JWT Token Validation

**Acceptance Criteria:**
- Valid JWT tokens are accepted
- Expired tokens are rejected (401)
- Malformed tokens are rejected (401)
- Missing Authorization header returns 401 (when AUTH_REQUIRED=true)
- Token signature is verified

**Test Files and Cases:**

| Test File | Test Class | Test Function | Coverage |
|-----------|-----------|---------------|----------|
| test_authentication.py | TestAuthenticationBasics | test_valid_jwt_token_accepted | ✓ Valid token accepted |
| test_authentication.py | TestAuthenticationBasics | test_missing_token_returns_401 | ✓ Missing token → 401 |
| test_authentication.py | TestAuthenticationBasics | test_invalid_token_format_returns_401 | ✓ Malformed token → 401 |
| test_authentication.py | TestAuthenticationBasics | test_expired_token_returns_401 | ✓ Expired token → 401 |
| test_authentication.py | TestAuthenticationBasics | test_token_without_bearer_prefix_rejected | ✓ Missing "Bearer " prefix |
| test_authentication.py | TestAuthenticationBasics | test_bearer_prefix_case_insensitive | ✓ Case handling |
| test_authentication.py | TestAuthenticationEdgeCases | test_empty_authorization_header | ✓ Empty header handling |
| test_authentication.py | TestAuthenticationEdgeCases | test_bearer_without_token | ✓ "Bearer " without token |
| test_authentication.py | TestAuthenticationEdgeCases | test_token_with_tampered_payload | ✓ Signature verification |

**Positive Cases (should pass):**
- Valid, non-expired JWT with correct signature
- Bearer prefix (case-insensitive)
- Token with standard claims (sub, roles, scope, azp)

**Negative Cases (should fail):**
- Missing Authorization header (AUTH_REQUIRED=true)
- Expired token
- Malformed token (invalid base64, missing parts)
- Wrong signature (key mismatch)
- Empty token

**Edge Cases:**
- Unicode characters in Authorization header
- Very long token (>10KB)
- Token with null bytes

**How to Execute:**
```bash
# Run all authentication tests
pytest tests/test_authentication.py -v

# Run just the basics
pytest tests/test_authentication.py::TestAuthenticationBasics -v

# Run one specific test
pytest tests/test_authentication.py::TestAuthenticationBasics::test_valid_jwt_token_accepted -v
```

---

### Feature: DEMO_MODE Bypass

**Acceptance Criteria:**
- When DEMO_MODE=true and DEMO_MODE_AUTH_BYPASS=true, unauthenticated requests are allowed
- Default role assigned to demo users
- Production deployments should have DEMO_MODE=false

**Test Files and Cases:**

| Test File | Test Class | Test Function | Coverage |
|-----------|-----------|---------------|----------|
| test_authentication.py | TestAuthenticationBasics | test_demo_mode_bypass_without_token | ✓ Bypass enabled |

**How to Execute:**
```bash
pytest tests/test_authentication.py::TestAuthenticationBasics::test_demo_mode_bypass_without_token -v
```

---

### Feature: User Context & Claims Extraction

**Acceptance Criteria:**
- User ID extracted from 'sub' claim
- Roles parsed from 'roles' claim (space-separated)
- Scopes parsed from 'scope' claim (space-separated)
- Client ID extracted from 'azp' claim
- Configurable claim names supported

**Test Files and Cases:**

| Test File | Test Class | Test Function | Coverage |
|-----------|-----------|---------------|----------|
| test_authentication.py | TestTokenClaimExtraction | test_user_id_extracted_from_sub_claim | ✓ sub → user_id |
| test_authentication.py | TestTokenClaimExtraction | test_roles_parsed_from_space_separated_claim | ✓ roles parsing |
| test_authentication.py | TestTokenClaimExtraction | test_scopes_parsed_from_space_separated_claim | ✓ scope parsing |
| test_authentication.py | TestTokenClaimExtraction | test_client_id_extracted_from_azp_claim | ✓ azp → client_id |

**How to Execute:**
```bash
pytest tests/test_authentication.py::TestTokenClaimExtraction -v
```

---

## Functional Area 2: Exposure Governance (Layer B)

### Feature: Role-Based Tool Filtering

**Acceptance Criteria:**
- Admin users see all tools
- Data scientists see subset of tools
- Analysts see minimal (read-only) tools
- Users with no roles see no tools
- Exposure patterns: expose:bundle:X, expose:tool:X, expose:*

**Test Files and Cases:**

| Test File | Test Class | Test Function | Coverage |
|-----------|-----------|---------------|----------|
| test_exposure_governance.py | TestExposureGovernanceDiscovery | test_admin_sees_all_tools | ✓ Admin access |
| test_exposure_governance.py | TestExposureGovernanceDiscovery | test_data_scientist_sees_subset_of_tools | ✓ Role filtering |
| test_exposure_governance.py | TestExposureGovernanceDiscovery | test_analyst_sees_minimal_tools | ✓ Minimal access |
| test_exposure_governance.py | TestExposureGovernanceDiscovery | test_user_with_no_roles_sees_no_tools | ✓ No access |
| test_exposure_governance.py | TestExposureBundleLevel | test_expose_bundle_pattern_allows_all_bundle_tools | ✓ Bundle pattern |
| test_exposure_governance.py | TestExposureBundleLevel | test_expose_all_bundles_pattern | ✓ Wildcard pattern |
| test_exposure_governance.py | TestExposureToolLevel | test_expose_tool_pattern_allows_specific_tool | ✓ Tool pattern |
| test_exposure_governance.py | TestExposureToolLevel | test_expose_all_tools_pattern | ✓ Tool wildcard |

**Positive Cases (should see tools):**
- Admin role → all tools visible
- Data scientist role → customer-service bundle tools visible
- Analyst role → read-only tools visible

**Negative Cases (should NOT see tools):**
- Non-exposed bundle (analytics for analyst)
- Non-exposed tool (delete_customer for analyst)
- No roles → no tools visible

**Edge Cases:**
- Empty tool list
- Very long tool names
- Special characters in names (XSS, SQL injection attempts)

**How to Execute:**
```bash
pytest tests/test_exposure_governance.py::TestExposureGovernanceDiscovery -v
pytest tests/test_exposure_governance.py -v -k "exposure"
```

---

### Feature: Exposure Enforcement on Invocation

**Acceptance Criteria:**
- Exposed tools can be invoked
- Non-exposed tools return 403 Forbidden
- Exposure check occurs BEFORE execution (no side effects)

**Test Files and Cases:**

| Test File | Test Class | Test Function | Coverage |
|-----------|-----------|---------------|----------|
| test_exposure_governance.py | TestExposureGovernanceInvocation | test_exposed_tool_can_be_invoked | ✓ Can invoke |
| test_exposure_governance.py | TestExposureGovernanceInvocation | test_non_exposed_tool_cannot_be_invoked | ✓ Returns 403 |
| test_exposure_governance.py | TestExposureGovernanceInvocation | test_tool_exposure_checked_before_execution | ✓ Pre-execution check |

**How to Execute:**
```bash
pytest tests/test_exposure_governance.py::TestExposureGovernanceInvocation -v
```

---

## Functional Area 3: Rate Limiting

### Feature: Per-User and Per-Tool Rate Limiting

**Acceptance Criteria:**
- Requests within quota succeed
- Requests exceeding quota return 429
- Rate-After header provided with reset time
- Per-tool limits can be stricter than per-user limits
- Risk tiers: read (1x), write (3x), privileged (10x)

**Test Files and Cases:**

| Test File | Test Class | Test Function | Coverage |
|-----------|-----------|---------------|----------|
| test_rate_limiting.py | TestPerUserRateLimiting | test_request_within_user_limit | ✓ Within limit |
| test_rate_limiting.py | TestPerUserRateLimiting | test_request_exceeding_user_limit_returns_429 | ✓ Exceeds limit → 429 |
| test_rate_limiting.py | TestPerToolRateLimiting | test_tool_can_have_independent_limit | ✓ Tool-level limits |
| test_rate_limiting.py | TestRiskTierMultipliers | test_read_tool_has_standard_limit | ✓ Read tier (1x) |
| test_rate_limiting.py | TestRiskTierMultipliers | test_write_tool_has_3x_stricter_limit | ✓ Write tier (3x) |
| test_rate_limiting.py | TestRiskTierMultipliers | test_privileged_tool_has_10x_stricter_limit | ✓ Privileged tier (10x) |
| test_rate_limiting.py | TestRateLimitHeaders | test_429_response_includes_retry_after_header | ✓ Retry-After header |
| test_rate_limiting.py | TestRateLimitHeaders | test_rate_limit_info_in_response_body | ✓ Error body |
| test_rate_limiting.py | TestRateLimitReset | test_limit_resets_after_time_window | ✓ Time-based reset |

**Positive Cases (should succeed):**
- Request within quota
- First few requests of quota period
- Different users (separate quotas)

**Negative Cases (should get 429):**
- Requests after quota exhausted
- Privileged tools hit limit faster than read tools
- User exceeds both user-wide and tool-specific limits

**Edge Cases:**
- Zero remaining quota
- Negative remaining (system error condition)
- Very close to limit boundary

**How to Execute:**
```bash
pytest tests/test_rate_limiting.py -v

# Just the multiplier tests
pytest tests/test_rate_limiting.py::TestRiskTierMultipliers -v

# Critical rate limiting
pytest tests/test_rate_limiting.py -m critical -v
```

---

## Functional Area 4: Policy Enforcement (Layer A)

### Feature: Policy Decision Making

**Acceptance Criteria:**
- Allowed policies permit tool invocation
- Denied policies block invocation (403)
- Policy checked BEFORE execution
- Policy context includes user and resource
- Policy evaluated for both discovery and invocation

**Test Files and Cases:**

| Test File | Test Class | Test Function | Coverage |
|-----------|-----------|---------------|----------|
| test_policy_idempotency.py | TestPolicyEnforcement | test_allowed_policy_permits_tool_invocation | ✓ Allow decision |
| test_policy_idempotency.py | TestPolicyEnforcement | test_denied_policy_blocks_tool_invocation | ✓ Deny → 403 |
| test_policy_idempotency.py | TestPolicyEnforcement | test_policy_checked_before_tool_execution | ✓ Pre-execution |
| test_policy_idempotency.py | TestPolicyEnforcement | test_policy_evaluated_for_discovery | ✓ tools/list |
| test_policy_idempotency.py | TestPolicyEnforcement | test_policy_context_includes_user_and_resource | ✓ Full context |

**How to Execute:**
```bash
pytest tests/test_policy_idempotency.py::TestPolicyEnforcement -v
```

---

## Functional Area 5: Idempotency

### Feature: Idempotency Key Handling

**Acceptance Criteria:**
- Write operations support idempotency_key parameter
- Repeated requests with same key return cached result
- Different keys result in separate executions
- Read operations don't require keys
- Missing keys handled gracefully
- Very long keys rejected safely

**Test Files and Cases:**

| Test File | Test Class | Test Function | Coverage |
|-----------|-----------|---------------|----------|
| test_policy_idempotency.py | TestIdempotency | test_write_operation_with_idempotency_key | ✓ Key support |
| test_policy_idempotency.py | TestIdempotency | test_repeated_idempotent_request_returns_cached_result | ✓ Caching |
| test_policy_idempotency.py | TestIdempotency | test_different_idempotency_keys_execute_separately | ✓ Different keys |
| test_policy_idempotency.py | TestIdempotency | test_read_operations_dont_require_idempotency_key | ✓ Reads optional |
| test_policy_idempotency.py | TestIdempotencyEdgeCases | test_empty_idempotency_key_handled | ✓ Empty key |
| test_policy_idempotency.py | TestIdempotencyEdgeCases | test_very_long_idempotency_key | ✓ Long key |
| test_policy_idempotency.py | TestIdempotencyEdgeCases | test_idempotency_store_failure_degrades_gracefully | ✓ Graceful failure |

**Positive Cases (should succeed):**
- Write with valid idempotency_key
- Repeated with same key (cached)
- Different keys (separate executions)

**Negative Cases (edge cases):**
- Empty key
- Missing key (should still work)
- Very long key (>10KB)
- Store unavailable (Redis down)

**How to Execute:**
```bash
pytest tests/test_policy_idempotency.py::TestIdempotency -v
pytest tests/test_policy_idempotency.py::TestIdempotencyEdgeCases -v
```

---

## Functional Area 6: Audit Logging

### Feature: Comprehensive Audit Trail

**Acceptance Criteria:**
- Tool invocations logged with full context
- Policy decisions logged
- Auth events logged
- PII masked in logs
- Timestamps and correlation IDs captured
- Audit traceable for compliance

**Test Files and Cases:**

| Test File | Test Class | Test Function | Coverage |
|-----------|-----------|---------------|----------|
| test_audit_chat.py | TestAuditLogging | test_tool_invocation_logged_to_audit | ✓ Tool log |
| test_audit_chat.py | TestAuditLogging | test_policy_decision_logged_to_audit | ✓ Policy log |
| test_audit_chat.py | TestAuditLogging | test_successful_tool_invocation_status_in_audit | ✓ Success status |
| test_audit_chat.py | TestAuditLogging | test_failed_tool_invocation_logged | ✓ Failure status |
| test_audit_chat.py | TestAuditLogging | test_authentication_events_logged | ✓ Auth log |
| test_audit_chat.py | TestAuditLogging | test_rate_limit_events_logged | ✓ Rate limit log |
| test_audit_chat.py | TestAuditPIIMasking | test_customer_id_masked_in_audit | ✓ Data masking |
| test_audit_chat.py | TestAuditPIIMasking | test_email_addresses_masked_in_audit | ✓ Email mask |
| test_audit_chat.py | TestAuditPIIMasking | test_api_keys_masked_in_audit | ✓ Key mask |

**Positive Cases (should log):**
- Successful tool execution
- Failed invocation
- Policy allow/deny
- Auth success/failure

**Verification Points:**
- Audit record contains user_id
- Timestamp is accurate
- Correlation ID present
- PII is masked (not plaintext)
- Tool name and arguments logged

**How to Execute:**
```bash
pytest tests/test_audit_chat.py -v
pytest tests/test_audit_chat.py::TestAuditLogging -v
pytest tests/test_audit_chat.py::TestAuditPIIMasking -v
```

---

## Functional Area 7: Chat API Security

### Feature: Chat API Authentication & Authorization

**Acceptance Criteria:**
- Chat API requires authentication (401 without token)
- Accepts valid JWT tokens
- Rejects invalid tokens (401)
- Filters tools by user exposure
- Enforces policy for tool execution
- Applies rate limiting
- Logs all activity

**Test Files and Cases:**

| Test File | Test Class | Test Function | Coverage |
|-----------|-----------|---------------|----------|
| test_audit_chat.py | TestChatAPIAuthentication | test_chat_requires_auth_token | ✓ Auth required |
| test_audit_chat.py | TestChatAPIAuthentication | test_chat_accepts_valid_jwt_token | ✓ Valid token |
| test_audit_chat.py | TestChatAPIAuthentication | test_chat_rejects_invalid_token | ✓ Invalid → 401 |
| test_audit_chat.py | TestChatAPIAuthorization | test_chat_filters_tools_by_exposure | ✓ Exposure filter |
| test_audit_chat.py | TestChatAPIAuthorization | test_chat_enforces_policy_for_tool_execution | ✓ Policy check |
| test_audit_chat.py | TestChatAPIAuthorization | test_chat_applies_rate_limiting | ✓ Rate limit |
| test_audit_chat.py | TestChatAuditLogging | test_chat_tool_execution_logged | ✓ Tool log |
| test_audit_chat.py | TestChatAuditLogging | test_chat_policy_decisions_logged | ✓ Policy log |

**How to Execute:**
```bash
pytest tests/test_audit_chat.py -v
pytest tests/test_audit_chat.py::TestChatAPIAuthentication -v
pytest tests/test_audit_chat.py::TestChatAPIAuthorization -v
```

---

## Functional Area 8: Analytics & Monitoring

### Feature: Real-Time Metrics Collection & Reporting

**Acceptance Criteria:**
- Metrics endpoints available and responsive
- Real data aggregation (not mock data)
- Performance percentiles calculated accurately
- Error rates tracked
- Timeline data properly aggregated
- Recent activity ordered by timestamp

**Test Files and Cases:**

| Test File | Test Class | Test Function | Coverage |
|-----------|-----------|---------------|----------|
| test_analytics.py | TestAnalyticsEndpoints | test_requests_timeline_endpoint_available | ✓ Endpoint works |
| test_analytics.py | TestAnalyticsEndpoints | test_performance_metrics_endpoint_available | ✓ Endpoint works |
| test_analytics.py | TestAnalyticsEndpoints | test_recent_activity_endpoint_available | ✓ Endpoint works |
| test_analytics.py | TestAnalyticsDataAccuracy | test_requests_timeline_aggregates_correctly | ✓ Aggregation |
| test_analytics.py | TestAnalyticsDataAccuracy | test_performance_percentiles_calculated | ✓ Percentiles |
| test_analytics.py | TestAnalyticsDataAccuracy | test_error_rate_calculated_correctly | ✓ Error rate |
| test_analytics.py | TestAnalyticsEdgeCases | test_empty_metrics_returns_zero_data | ✓ Empty data |
| test_analytics.py | TestAnalyticsEdgeCases | test_single_execution_metrics | ✓ Single item |
| test_analytics.py | TestAnalyticsEdgeCases | test_recent_activity_orders_by_timestamp | ✓ Ordering |
| test_analytics.py | TestAnalyticsAuthorization | test_analytics_requires_auth_token | ✓ Auth required |
| test_analytics.py | TestAnalyticsAuthorization | test_analyst_can_view_analytics | ✓ RBAC |

**Verification Points:**
- /metrics/requests-timeline returns daily/weekly aggregation
- /metrics/performance includes p50, p95, p99 latencies
- /metrics/recent-activity shows latest executions first
- All endpoints require authentication

**How to Execute:**
```bash
pytest tests/test_analytics.py -v
pytest tests/test_analytics.py::TestAnalyticsDataAccuracy -v
```

---

## Test Execution Workflow for QA

### 1. **Initial Validation (Pre-Commit)**
Run before committing changes:
```bash
pytest tests/ -m critical -v
```
This runs all critical security tests. Should all pass.

### 2. **Full Suite (Pre-Release)**
Run before release builds:
```bash
pytest tests/ -v --cov=app --cov-report=html
```
Generates HTML coverage report showing lines covered/missed.

### 3. **Feature-Specific Testing**
To test a specific feature (e.g., rate limiting):
```bash
pytest tests/test_rate_limiting.py -v
```

### 4. **Regression Testing**
After bug fix, re-run related tests:
```bash
# Fixed authentication? Run:
pytest tests/test_authentication.py -v

# Fixed rate limiting? Run:
pytest tests/test_rate_limiting.py -v
```

### 5. **Continuous Integration**
In CI/CD pipeline:
```bash
pytest tests/ -v --junit-xml=test-results.xml
```
Generates JUnit XML for metrics/dashboards.

---

## Mapping: ChatGPT Identified Gaps → Tests

The following 9 gaps were identified in code review. Each has corresponding test coverage:

| Gap | Layer | Test File | Test Classes |
|-----|-------|-----------|--------------|
| Auth not enforced | RequestContext | test_authentication.py | TestAuthenticationBasics, TestTokenClaimExtraction |
| Exposure bypassed | Layer B | test_exposure_governance.py | TestExposureGovernanceDiscovery, TestExposureGovernanceInvocation |
| Policy not invoked | Layer A | test_policy_idempotency.py | TestPolicyEnforcement |
| Rate limiting unused | Cross-cutting | test_rate_limiting.py | TestPerUserRateLimiting, TestPerToolRateLimiting, TestRiskTierMultipliers |
| Idempotency not wired | Cross-cutting | test_policy_idempotency.py | TestIdempotency, TestIdempotencyEdgeCases |
| Audit logging missing | Cross-cutting | test_audit_chat.py | TestAuditLogging, TestAuditPIIMasking |
| Analytics use mock data | Observability | test_analytics.py | TestAnalyticsDataAccuracy |
| Exposure UI API broken | Admin UI | test_audit_chat.py | (API call validation) |
| Chat API unauthenticated | Chat UI | test_audit_chat.py | TestChatAPIAuthentication, TestChatAPIAuthorization |

---

## Coverage Metrics Target

**Aim for the following coverage levels:**

```
app/api/mcp.py              → 95%+ (critical security)
app/api/chat.py             → 95%+ (critical security)
app/core/                   → 90%+ (all security layers)
```

Check coverage:
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

---

## Adding New Tests

### Template for New Test Class
```python
"""
Tests for [Feature Name] in MCP server.

Coverage:
- [Aspect 1]
- [Aspect 2]

Test Matrix:
┌──────────────┬──────────┬──────────┬────────┐
│ Test Case    │ Expected │ Edge Case│ Status │
├──────────────┼──────────┼──────────┼────────┤
│ ...          │ ...      │ ...      │ PASS   │
└──────────────┴──────────┴──────────┴────────┘
"""

import pytest

class TestMyFeature:
    """Test [feature name]."""
    
    @pytest.mark.security
    @pytest.mark.critical
    def test_positive_case(self, test_client, jwt_token_admin):
        """
        Test that [positive behavior occurs].
        
        Acceptance Criteria:
        - [Criterion 1]
        - [Criterion 2]
        """
        headers = {"Authorization": f"Bearer {jwt_token_admin}"}
        response = test_client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": "test", "method": "tools/list"},
            headers=headers
        )
        
        assert response.status_code in [200, 201]
```

### Steps to Add Test
1. Choose appropriate test file (or create new one)
2. Create test class (group related tests)
3. Add test methods (one per behavior)
4. Add @pytest.mark.security and @pytest.mark.critical as appropriate
5. Include docstring with Acceptance Criteria
6. Use existing fixtures from conftest.py
7. Run test: `pytest tests/test_yourfile.py::TestYourClass::test_yourtest -v`

---

## Contact & Support

For questions about test execution or adding new tests, refer to:
- conftest.py for available fixtures
- Test class docstrings for detailed coverage info
- Terminal output for test failures and error details

---

**Last Updated:** February 7, 2026  
**Status:** Ready for 309 API Onboarding Validation
