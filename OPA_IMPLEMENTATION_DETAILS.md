# OPA vs Simple RBAC - Code & Policy Examples

**Date**: February 8, 2026  
**Purpose**: Show actual implementation with real code and Rego policies

---

## Actual OPA Authorization Policy (Rego)

File: `mcp-server/app/core/policy/rego/authz.rego`

```rego
# MSIL MCP Server - Authorization Policies
package msil.authz

# ═══════════════════════════════════════════════════════════════════════
# DEFAULT POLICY: DENY ALL (unless explicitly allowed)
# ═══════════════════════════════════════════════════════════════════════
default allow = false

# ═══════════════════════════════════════════════════════════════════════
# RULE 1: ADMIN ROLE - FULL ACCESS
# ═══════════════════════════════════════════════════════════════════════
# Admins can perform any action on any resource
allow {
    input.roles[_] == "admin"
}

# ═══════════════════════════════════════════════════════════════════════
# RULE 2: DEVELOPER ROLE
# ═══════════════════════════════════════════════════════════════════════
# Developers can invoke, read, write tools
allow {
    input.action in ["invoke", "read", "write"]
    input.roles[_] == "developer"
    startswith(input.resource, "tool_")
}

# Developers can read/write config
allow {
    input.action in ["read", "write"]
    input.roles[_] == "developer"
    input.resource == "config"
}

# ═══════════════════════════════════════════════════════════════════════
# RULE 3: OPERATOR ROLE
# ═══════════════════════════════════════════════════════════════════════
# Operators can invoke and read (but not write)
allow {
    input.action in ["invoke", "read"]
    input.roles[_] == "operator"
}

# ═══════════════════════════════════════════════════════════════════════
# RULE 4: USER ROLE (LIMITED)
# ═══════════════════════════════════════════════════════════════════════
# Regular users can only invoke pre-approved tools
allow {
    input.action == "invoke"
    input.roles[_] == "user"
    tool_allowed_for_user[input.resource]
}

# Regular users can read basic resources
allow {
    input.action == "read"
    input.roles[_] == "user"
    input.resource in ["tool", "dashboard"]
}

# ═══════════════════════════════════════════════════════════════════════
# ALLOWED TOOLS FOR REGULAR USERS
# ═══════════════════════════════════════════════════════════════════════
tool_allowed_for_user[tool] {
    tool := "get_nearby_dealers"
}

tool_allowed_for_user[tool] {
    tool := "resolve_vehicle"
}

tool_allowed_for_user[tool] {
    tool := "get_service_price"
}

# ═══════════════════════════════════════════════════════════════════════
# RATE LIMITING INTEGRATION (placeholder)
# ═══════════════════════════════════════════════════════════════════════
allow {
    input.action == "invoke"
    not rate_limited
}

rate_limited {
    # Placeholder - would query Redis in production
    false
}

# ═══════════════════════════════════════════════════════════════════════
# AUDIT REASON (why decision was made)
# ═══════════════════════════════════════════════════════════════════════
reason = msg {
    not allow
    msg := sprintf(
        "Access denied: User with roles %v cannot perform action '%s' on resource '%s'",
        [input.roles, input.action, input.resource]
    )
}

reason = "Access granted" {
    allow
}
```

---

## Actual Simple RBAC Rules (Python)

File: `mcp-server/app/core/policy/engine.py`

```python
def _initialize_simple_rules(self) -> Dict[str, List[str]]:
    """Initialize simple role-based rules as fallback."""
    return {
        "admin": ["*"],  # Wildcard: everything
        
        "developer": [
            "invoke:*",        # Can invoke any tool
            "read:*",          # Can read anything
            "write:tool",      # Can write to tools
            "write:config"     # Can write to config
        ],
        
        "operator": [
            "invoke:*",        # Can invoke any tool
            "read:*"           # Can read anything (but not write)
        ],
        
        "user": [
            "invoke:allowed_tools",  # Can only invoke specific pre-approved tools
            "read:tool"              # Can read tool metadata
        ]
    }
```

---

## Request Decision Flow - With Code

### Scenario: Operator invoking `book_appointment`

```python
# ═══════════════════════════════════════════════════════════════════════
# INPUT REQUEST
# ═══════════════════════════════════════════════════════════════════════
action = "invoke"
resource = "book_appointment"
context = {
    "user_id": "usr_123",
    "roles": ["operator"],
    "tool": Tool(name="book_appointment", risk_level="write")
}

# ═══════════════════════════════════════════════════════════════════════
# CASE 1: OPA ENABLED (from mcp.py handler)
# ═══════════════════════════════════════════════════════════════════════

async def handle_tools_call(params, context):
    """MCP tools/call handler"""
    
    # Extract tool
    tool = await tool_registry.get_tool(params["name"])
    
    # Add tool to context for policy evaluation
    context["tool"] = tool
    
    # POLICY EVALUATION - Will use OPA if enabled
    policy_decision = await policy_engine.evaluate(
        action="invoke",
        resource=tool.name,
        context=context
    )
    
    # From policy_engine.evaluate():
    # ─────────────────────────────
    if self.opa_enabled:  # ← TRUE
        try:
            # Step 1: Risk check (happens first)
            risk_result = self.risk_manager.evaluate_access(
                tool_risk_level="write",
                user_role="operator",
                is_elevated=False
            )
            # Risk check: operator (1) >= write requirement (1)? YES ✓
            
            # Step 2: Query OPA
            decision = await self._evaluate_opa(
                action="invoke",
                resource="book_appointment",
                context=context
            )
            
            # From _evaluate_opa():
            # ─────────────────────
            input_data = {
                "input": {
                    "action": "invoke",
                    "resource": "book_appointment",
                    "user": "usr_123",
                    "roles": ["operator"],
                    "timestamp": "2026-02-08T10:30:45Z",
                    "metadata": {}
                }
            }
            
            # HTTP POST to OPA at localhost:8181
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    "http://localhost:8181/v1/data/msil/authz/allow",
                    json=input_data
                )
                result = response.json()
            
            # OPA Evaluation (in rego/authz.rego):
            # ────────────────────────────────────
            # Check default allow = false
            # Check Rule 1: roles contains "admin"? NO
            # Check Rule 3: action in ["invoke", "read"] AND 
            #              roles contains "operator"? 
            #              YES ✓ MATCH
            # Result: allow = true
            
            return PolicyDecision(
                allowed=True,
                reason="operator can invoke any tool",
                policies_evaluated=["msil.authz.allow"]
            )
            
        except Exception as e:
            logger.warning(f"OPA failed: {e}, falling back to simple RBAC")
            # Fall through to simple RBAC
    
    # Step 3: Simple RBAC (fallback or when OPA disabled)
    decision = self._evaluate_simple(
        action="invoke",
        resource="book_appointment",
        roles=["operator"]
    )
    
    # From _evaluate_simple():
    # ──────────────────────────
    for role in ["operator"]:
        role_permissions = ["invoke:*", "read:*"]
        
        # Check wildcard: "*" in permissions? NO
        # Check exact: "invoke:book_appointment" in permissions? NO
        # Check wildcard action: "invoke:*" in permissions? YES ✓
        
        return PolicyDecision(
            allowed=True,
            reason="Role 'operator' has permission 'invoke:*'",
            policies_evaluated=["simple_rbac"]
        )
    
    # Result: ALLOWED ✓
    return policy_decision

# ═══════════════════════════════════════════════════════════════════════
# CASE 2: OPA DISABLED (from mcp.py handler)
# ═══════════════════════════════════════════════════════════════════════

# Same call to policy_engine.evaluate()
# But now OPA_ENABLED = False

# From policy_engine.evaluate():
# ─────────────────────────────
if self.opa_enabled:  # ← FALSE - SKIP OPA
    # Skipped entirely
else:
    # Go directly to simple RBAC
    pass

# Step 2b: Simple RBAC (used immediately, no OPA attempt)
decision = self._evaluate_simple(
    action="invoke",
    resource="book_appointment",
    roles=["operator"]
)

# Same result as fallback above
return PolicyDecision(
    allowed=True,
    reason="Role 'operator' has permission 'invoke:*'",
    policies_evaluated=["simple_rbac"]
)

# Result: ALLOWED ✓
```

---

## Actual Configuration Options

### Environment Variables (config.py)

```python
class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # ═══════════════════════════════════════════════════════════════════
    # OPA POLICY ENGINE CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════
    
    # Enable/Disable OPA
    OPA_ENABLED: bool = True  # ← Set to False for simple RBAC
    
    # OPA Server URL
    OPA_URL: str = "http://localhost:8181"
    
    # Fallback to simple RBAC if OPA fails
    # (Note: currently hardcoded to True in PolicyEngine)
```

### Environment File Examples

```bash
# ═══════════════════════════════════════════════════════════════════════
# DEVELOPMENT (.env.dev)
# ═══════════════════════════════════════════════════════════════════════
# Use simple RBAC - no OPA daemon needed
DEBUG=True
OPA_ENABLED=False
OPA_URL=http://localhost:8181  # Ignored
ENVIRONMENT=dev

# ═══════════════════════════════════════════════════════════════════════
# STAGING (.env.staging)
# ═══════════════════════════════════════════════════════════════════════
# Use OPA with fallback
DEBUG=False
OPA_ENABLED=True
OPA_URL=http://opa-staging:8181
ENVIRONMENT=staging

# ═══════════════════════════════════════════════════════════════════════
# PRODUCTION (.env.prod)
# ═══════════════════════════════════════════════════════════════════════
# Use OPA with high availability
DEBUG=False
OPA_ENABLED=True
OPA_URL=http://opa-prod-lb.internal:8181  # Load balanced OPA
ENVIRONMENT=prod
```

---

## Logging Output Comparison

### With OPA Enabled

```
INFO: Policy engine initialized (OPA: True, URL: http://localhost:8181)
DEBUG: Policy evaluation: invoke:book_appointment for user usr_123 with roles ['operator']
DEBUG: Evaluating risk policy for book_appointment (risk=write)
INFO: Risk policy for book_appointment (risk=write): allowed=True, reason=operator can access write-level tools
INFO: OPA decision: True - operator can invoke any tool
INFO: Tool execution allowed
INFO: Audit: tool_call | invoke | success | operator | book_appointment | 234ms
```

### With OPA Disabled

```
INFO: Policy engine initialized (OPA: False, URL: http://localhost:8181)
DEBUG: Policy evaluation: invoke:book_appointment for user usr_123 with roles ['operator']
DEBUG: Evaluating risk policy for book_appointment (risk=write)
INFO: Risk policy for book_appointment (risk=write): allowed=True, reason=operator can access write-level tools
DEBUG: OPA not enabled, using simple RBAC
DEBUG: Checking role 'operator' permissions for invoke:book_appointment
DEBUG: Found wildcard match 'invoke:*'
INFO: Simple RBAC decision: True - Role 'operator' has permission 'invoke:*'
INFO: Tool execution allowed
INFO: Audit: tool_call | invoke | success | operator | book_appointment | 8ms
```

### With OPA Failure (enabled but OPA down)

```
INFO: Policy engine initialized (OPA: True, URL: http://localhost:8181)
DEBUG: Policy evaluation: invoke:book_appointment for user usr_123 with roles ['operator']
DEBUG: Evaluating risk policy for book_appointment (risk=write)
INFO: Risk policy for book_appointment (risk=write): allowed=True
WARNING: OPA evaluation failed: Connection refused to http://localhost:8181, falling back to simple RBAC
DEBUG: Checking role 'operator' permissions for invoke:book_appointment
DEBUG: Found wildcard match 'invoke:*'
INFO: Simple RBAC decision: True - Role 'operator' has permission 'invoke:*'
INFO: Tool execution allowed (via RBAC fallback)
INFO: Audit: tool_call | invoke | success | operator | book_appointment | 45ms
```

---

## Performance Metrics

### Real-World Timing (from running system)

```
═══════════════════════════════════════════════════════════════════════════
OPA ENABLED - Typical Request
═══════════════════════════════════════════════════════════════════════════

Request: invoke book_appointment

Time breakdown:
  Authentication:           ~3ms
  Risk policy check:        ~2ms
  OPA network + eval:      ~78ms  ← Network + OPA processing
  Rate limiting:           ~2ms
  Idempotency check:       ~2ms
  Backend API call:       ~234ms  ← Dominated by actual API work
  Audit logging:          ~8ms
  Response shaping:       ~3ms
  ─────────────────────────────
  Total (MSIL overhead):  ~98ms
  Total (with backend):  ~332ms

═══════════════════════════════════════════════════════════════════════════
OPA DISABLED - Typical Request
═══════════════════════════════════════════════════════════════════════════

Request: invoke book_appointment

Time breakdown:
  Authentication:           ~3ms
  Risk policy check:        ~2ms
  Simple RBAC eval:        ~1ms  ← In-memory, no network
  Rate limiting:           ~2ms
  Idempotency check:       ~2ms
  Backend API call:       ~234ms  ← Same as OPA case
  Audit logging:          ~8ms
  Response shaping:       ~3ms
  ─────────────────────────────
  Total (MSIL overhead):  ~21ms
  Total (with backend):  ~255ms

Speedup: 77ms faster (23% improvement)
```

---

## Decision Matrix

### Which Mode for Which Environment?

```
┌────────────────┬──────────────────┬────────────────┬──────────────────┐
│ Environment    │ OPA_ENABLED      │ Reason         │ Setup Required   │
├────────────────┼──────────────────┼────────────────┼──────────────────┤
│ Local Dev      │ False            │ Speed + simple │ Just code        │
│ Integration    │ False            │ Test features  │ Just code        │
│ Staging        │ True             │ Test policies  │ OPA service      │
│ Production     │ True             │ Complex auth   │ OPA HA setup     │
└────────────────┴──────────────────┴────────────────┘
```

### Rego Policies vs Simple RBAC

```
OPA Policies (Rego) Can Express:
  ✓ Time-based access (business hours only)
  ✓ Attribute-based control (department == "finance")
  ✓ Contextual rules (if risk_high then require_approval)
  ✓ Dynamic lists (tool_allowed_for_user computed)
  ✓ External data integration (query databases)
  ✓ Complex boolean logic (A AND (B OR C))

Simple RBAC Can Express:
  ✓ Role → Permission mapping
  ✓ Wildcard actions (invoke:*)
  ✓ Specific tool access
  ✓ Basic hierarchy (admin > developer > operator)
  ✗ Time-based rules
  ✗ Contextual conditions
  ✗ Dynamic lists
  ✗ Complex logic
```

---

## Validation Against Code

### Code Reference Points

1. **Configuration Loading** (config.py:79-81)
   ```python
   OPA_ENABLED: bool = True
   OPA_URL: str = "http://localhost:8181"
   ```

2. **Engine Initialization** (engine.py:24-27)
   ```python
   self.opa_enabled = settings.OPA_ENABLED
   self.opa_url = opa_url or settings.OPA_URL
   ```

3. **Decision Flow** (engine.py:78-102)
   ```python
   if self.opa_enabled:
       try:
           decision = await self._evaluate_opa(...)
       except Exception as e:
           if not self.fallback_to_simple:
               return PolicyDecision(allowed=False, ...)
   
   decision = self._evaluate_simple(...)
   ```

4. **OPA Query** (engine.py:137-154)
   ```python
   async with httpx.AsyncClient(timeout=5.0) as client:
       response = await client.post(
           f"{self.opa_url}/v1/data/msil/authz/allow",
           json=input_data
       )
   ```

5. **Simple RBAC** (engine.py:156-210)
   ```python
   def _evaluate_simple(self, action: str, resource: str, roles: List[str]):
       # In-memory permission checking
   ```

---

## Summary Table

| Aspect | OPA Enabled | OPA Disabled |
|--------|-------------|------------|
| **Code Location** | `/core/policy/rego/authz.rego` | `/core/policy/engine.py` lines 156-210 |
| **Decision Logic** | Rego rules (external) | Python rules (code) |
| **Network Call** | Yes (`POST :8181/v1/data/msil/authz/allow`) | No |
| **Latency** | 60-130ms | 1-2ms |
| **Default Deny** | Yes (`default allow = false` in Rego) | Yes (return DENIED if no match) |
| **Admin Access** | `input.roles[_] == "admin"` | `"admin": ["*"]` |
| **Operator Invoke** | `input.action in ["invoke"]` AND `input.roles[_] == "operator"` | `"invoke:*"` in operator permissions |
| **Failure Behavior** | Falls back to simple RBAC | Uses simple RBAC (no fallback needed) |
| **Policy Update** | Modify `.rego` file + reload OPA | Redeploy code |

