# Test Execution Playbook for QA Engineers

## Quick Start for QA

This playbook enables you to run, understand, and maintain the test suite for MSIL MCP Server.

---

## Installation & Setup

### 1. Install Test Dependencies
```bash
cd mcp-server
pip install -r requirements.txt

# Install pytest if not included
pip install pytest pytest-asyncio pytest-cov pytest-xdist
```

### 2. Verify Setup
```bash
# Run a simple test
pytest tests/test_authentication.py::TestAuthenticationBasics::test_valid_jwt_token_accepted -v
```

If successful, you'll see:
```
tests/test_authentication.py::TestAuthenticationBasics::test_valid_jwt_token_accepted PASSED [100%]
```

---

## Understanding Test Organization

### Tests are Organized by Functionality

```
tests/
├── test_authentication.py      → JWT validation, DEMO_MODE bypass
├── test_exposure_governance.py → Role-based tool filtering (Layer B)
├── test_rate_limiting.py       → Per-user/tool limits, risk tiers
├── test_policy_idempotency.py  → Policy decisions (Layer A) + idempotency keys
├── test_audit_chat.py          → Audit logging + Chat API security
└── test_analytics.py           → Metrics and reporting endpoints
```

### Within Each File: Test Classes & Methods

```
test_authentication.py
├── TestAuthenticationBasics
│   ├── test_valid_jwt_token_accepted()
│   ├── test_missing_token_returns_401()
│   └── test_expired_token_returns_401()
├── TestTokenClaimExtraction
│   ├── test_user_id_extracted_from_sub_claim()
│   └── test_roles_parsed_from_space_separated_claim()
└── TestAuthenticationEdgeCases
    ├── test_empty_authorization_header()
    └── test_token_with_tampered_payload()
```

Each test is independent and can be run individually.

---

## Common Test Execution Scenarios

### Scenario 1: I Found a Bug in Authentication
**Action:** Run authentication tests after fix
```bash
pytest tests/test_authentication.py -v
```

Expected output: All tests pass (✓)

---

### Scenario 2: Rate Limiting Not Working
**Action:** Debug rate limiting tests
```bash
# Run just rate limiting tests
pytest tests/test_rate_limiting.py -v

# Run one specific test with more details
pytest tests/test_rate_limiting.py::TestPerUserRateLimiting::test_request_exceeding_user_limit_returns_429 -v -s
```

The `-s` flag shows print statements (helps with debugging).

---

### Scenario 3: Pre-Release Testing
**Action:** Run full suite with coverage
```bash
pytest tests/ -v --cov=app --cov-report=html

# Then open coverage report
start htmlcov/index.html  # Windows
open htmlcov/index.html   # Mac
```

This shows which lines of code are tested (green) vs. not tested (red).

---

### Scenario 4: Policy Engine Not Evaluating
**Action:** Run policy-specific tests
```bash
pytest tests/test_policy_idempotency.py::TestPolicyEnforcement -v
```

---

### Scenario 5: Regression After Deployment
**Action:** Run critical tests that catch 90% of issues
```bash
pytest tests/ -m critical -v
```

This runs only tests marked with `@pytest.mark.critical`. Should take <5 minutes.

---

## Understanding Test Markers

Tests are tagged with markers for quick filtering:

### @pytest.mark.critical
Tests that MUST pass before deployment. These cover:
- Authentication enforcement (401 without token)
- Exposure governance (403 for non-exposed tools)
- Policy decisions (allow/deny)
- Rate limiting (429 when exceeded)
- Idempotency (no duplicates)

Run critical tests:
```bash
pytest tests/ -m critical -v
```

### @pytest.mark.security
All security-related tests (includes critical):

```bash
pytest tests/ -m security -v
```

### @pytest.mark.performance
Performance and load tests (usually skipped in CI):

```bash
pytest tests/ -m performance -v
```

---

## Reading Test Output

### Successful Test Run
```
tests/test_authentication.py::TestAuthenticationBasics::test_valid_jwt_token_accepted PASSED [100%]
```
- `PASSED` = test passed
- `[100%]` = progress indicator

### Failed Test Run
```
tests/test_authentication.py::TestAuthenticationBasics::test_missing_token_returns_401 FAILED [50%]

AssertionError: assert 200 == 401
  Expected: 401 (Unauthorized)
  Got: 200 (OK)
```

**Action:** The missing token should return 401, but it returned 200. This indicates auth enforcement is not working.

### Test Error (unexpected exception)
```
tests/test_rate_limiting.py::TestPerUserRateLimiting::test_request_exceeding_user_limit_returns_429 ERROR

TypeError: 'NoneType' object is not subscriptable
```

This indicates a code error in the test itself or in the component being tested.

---

## Coverage Report

After running tests with coverage, open the HTML report:

```bash
pytest tests/ --cov=app --cov-report=html
```

**Important Coverage Targets:**

```
app/api/mcp.py              → 95%+ (critical)
app/api/chat.py             → 95%+ (critical)
app/core/                   → 90%+ (auth, exposure, policy)
app/core/metrics/           → 85%+ (analytics)
```

If coverage is below target:
1. Identify uncovered lines (shown in red)
2. Check TEST_MAPPING.md for what tests should cover that line
3. Consider adding negative/edge case tests

---

## Debugging Failed Tests

### Step 1: Run the failed test in isolation
```bash
pytest tests/test_policy_idempotency.py::TestIdempotency::test_repeated_idempotent_request_returns_cached_result -v -s
```

### Step 2: Add print statements
Edit the test to add debugging output:

```python
def test_repeated_idempotent_request_returns_cached_result(self, test_client, jwt_token_admin):
    headers = {"Authorization": f"Bearer {jwt_token_admin}"}
    print(f"Token: {jwt_token_admin[:20]}...")  # First 20 chars only
    
    response1 = test_client.post(...)
    print(f"First response status: {response1.status_code}")
    print(f"Response body: {response1.json()}")
    
    assert response1.status_code in [200, 201]
```

Then run:
```bash
pytest tests/test_policy_idempotency.py::TestIdempotency::test_repeated_idempotent_request_returns_cached_result -v -s
```

The `-s` flag shows the print statements.

### Step 3: Check the actual service
For rate limiting failures:
1. Check that `RATE_LIMIT_ENABLED=True` in config
2. Check that Redis is running
3. Check rate limiter initialization in app/main.py

---

## New Feature Testing Workflow

When a new feature is added:

### 1. Write the Test First (TDD)
```bash
# Create test_new_feature.py with test cases
# Run test to confirm it fails (good! It means test is active)
pytest tests/test_new_feature.py -v
```

Expected: All tests fail ✗ (feature not implemented yet)

### 2. Implement the Feature
Update the code to make the test feature work.

### 3. Verify Tests Pass
```bash
pytest tests/test_new_feature.py -v
```

Expected: All tests pass ✓

### 4. Check Coverage
```bash
pytest tests/test_new_feature.py --cov=app/new_module --cov-report=term-missing
```

Expected: 90%+ coverage

### 5. Run Regression
```bash
pytest tests/ -v  # All tests still pass
```

---

## Test Case Template for New Tests

When adding new tests, use this template:

```python
@pytest.mark.security  # Add appropriate marker
@pytest.mark.critical  # Mark critical tests
def test_feature_behavior(self, test_client, jwt_token_admin):
    """
    Test that [specific behavior] occurs.
    
    Acceptance Criteria:
    - [Criterion 1]
    - [Criterion 2]
    - [Criterion 3]
    
    Edge Cases:
    - [Edge case 1]
    """ 
    
    # Setup
    headers = {"Authorization": f"Bearer {jwt_token_admin}"}
    
    # Action
    response = test_client.post(
        "/api/endpoint",
        json={"param": "value"},
        headers=headers
    )
    
    # Verify
    assert response.status_code in [200, 201]
    data = response.json()
    assert "expected_field" in data
```

---

## Parallel Execution (Faster Tests)

For large test suites, run in parallel:

```bash
pip install pytest-xdist
pytest tests/ -n auto
```

This automatically uses all CPU cores. Example output:
```
Running 24 tests in parallel using 8 workers...
PASSED tests/test_authentication.py::TestAuthenticationBasics::test_valid_jwt_token_accepted
PASSED tests/test_rate_limiting.py::TestPerUserRateLimiting::test_request_within_user_limit
...
24 passed in 2.45s
```

---

## Mock Objects & Fixtures

Tests use mocks to avoid needing real services. Key mocks in conftest.py:

### Mock Exposure Manager
```python
mock_exposure_manager:
  - filter_tools() → Returns list of tools user can see
  - is_tool_exposed() → True/False if tool exposed to user
```

### Mock Policy Engine
```python
mock_policy_engine:
  - evaluate() → Returns decision with allowed=True/False
```

### Mock Rate Limiter
```python
mock_rate_limiter:
  - check_user_rate_limit() → allowed=True/False, remaining=N
```

If you need a different mock behavior, modify it in your test:

```python
def test_rate_limit_exceeded(self, test_client, jwt_token_admin, mock_rate_limiter):
    # Change mock to deny access
    mock_rate_limiter.check_user_rate_limit.return_value = Mock(
        allowed=False,
        remaining=0,
        retry_after=60
    )
    
    response = test_client.post(...)
    assert response.status_code == 429
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --junit-xml=results.xml
      - uses: actions/upload-artifact@v2
        if: always()
        with:
          name: test-results
          path: results.xml
```

---

## Troubleshooting Common Issues

### Issue: "ModuleNotFoundError: No module named 'app'"
**Solution:** Run pytest from mcp-server directory
```bash
cd mcp-server
pytest tests/...
```

### Issue: "FAILED - KeyError: 'Authorization'"
**Solution:** Ensure mock headers are provided
```python
headers = {"Authorization": f"Bearer {jwt_token_admin}"}
response = test_client.post(..., headers=headers)  # Don't forget headers!
```

### Issue: "AssertionError: assert 200 == 401"
**Solution:** Check that AUTH_REQUIRED is True in test config
Look at test_settings fixture in conftest.py.

### Issue: Tests timeout
**Solution:** Some tests may be async. Ensure pytest-asyncio is installed:
```bash
pip install pytest-asyncio
```

---

## Maintenance

### Monthly: Update Dependencies
```bash
pip install --upgrade pip pytest pytest-asyncio
```

### Quarterly: Review Coverage
```bash
pytest tests/ --cov=app
# Check for uncovered lines in critical modules
```

### After Each Release: Regression Test
```bash
pytest tests/ -m critical -v
# All should pass before shipping
```

---

## Support References

- **TEST_MAPPING.md**: Detailed mapping of features to test cases
- **conftest.py**: Available fixtures and mocks
- **Individual test files**: Docstrings explain each test's purpose
- **pytest documentation**: https://docs.pytest.org/

---

**Last Updated:** February 7, 2026  
**Status:** Ready for 309 API Onboarding
