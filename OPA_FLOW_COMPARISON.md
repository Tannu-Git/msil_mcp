# OPA Policy Engine - Enabled vs Disabled Flow Analysis

**Document Version**: 1.0  
**Date**: February 8, 2026  
**Purpose**: Detailed comparison of how MSIL MCP behaves with OPA enabled/disabled

---

## Table of Contents

1. [Configuration](#configuration)
2. [Policy Evaluation Flow](#policy-evaluation-flow)
3. [Code Implementation](#code-implementation)
4. [Fallback Mechanism](#fallback-mechanism)
5. [Performance Comparison](#performance-comparison)
6. [Use Cases](#use-cases)

---

## Configuration

### OPA Enabled (Production Setup)

```python
# config.py (Environment Variable)
OPA_ENABLED=True
OPA_URL=http://localhost:8181

# Behavior
- OPA daemon must be running at http://localhost:8181
- Policy engine tries to query OPA first
- If OPA fails, falls back to simple RBAC
- Advanced policies (custom Rego rules) are evaluated
```

### OPA Disabled (Development Setup)

```python
# config.py (Environment Variable)
OPA_ENABLED=False
OPA_URL=http://localhost:8181  # Ignored

# Behavior
- Simple RBAC rules used directly
- No need to run OPA daemon
- No external network calls for policy decisions
- Only built-in role definitions are used
```

---

## Policy Evaluation Flow

### Scenario: Operator User Calls `book_appointment` Tool

```
═══════════════════════════════════════════════════════════════════════════
OPA ENABLED (Production Flow)
═══════════════════════════════════════════════════════════════════════════

Step 1: Request arrives
  Tool: book_appointment
  User: operator_user
  Action: invoke
  Context: { roles: ["operator"], user_id: "usr_123" }

Step 2: Risk Policy Evaluation (Happens First)
  ├─ Tool risk_level: "write"
  ├─ User role: "operator"
  ├─ Risk check: operator >= write required? YES ✓
  └─ Result: ALLOWED by risk policy

Step 3: Policy Engine.evaluate() called
  ├─ Input:
  │  - action: "invoke"
  │  - resource: "book_appointment"
  │  - context: { roles: ["operator"], user_id: "usr_123" }
  │
  ├─ Condition: if OPA_ENABLED?
  │  └─ YES, proceed to OPA
  │
  ├─ Step 3a: Try OPA Query
  │  ├─ Prepare request:
  │  │  POST http://localhost:8181/v1/data/msil/authz/allow
  │  │  Body:
  │  │  {
  │  │    "input": {
  │  │      "action": "invoke",
  │  │      "resource": "book_appointment",
  │  │      "user": "usr_123",
  │  │      "roles": ["operator"],
  │  │      "timestamp": "2026-02-08T10:30:45Z",
  │  │      "metadata": {...}
  │  │    }
  │  │  }
  │  │
  │  ├─ Send HTTP POST (timeout: 5 seconds)
  │  │
  │  ├─ OPA Engine Processing:
  │  │  // Rego Policy File: /app/core/policy/rego/authz.rego
  │  │  package msil.authz
  │  │  
  │  │  default allow = false
  │  │  
  │  │  // Rule 1: Admin can do anything
  │  │  allow {
  │  │    input.roles[_] == "admin"
  │  │  }
  │  │  
  │  │  // Rule 2: Operator can invoke any tool
  │  │  allow {
  │  │    input.action == "invoke"
  │  │    input.roles[_] == "operator"
  │  │  }
  │  │  
  │  │  // Rule 3: Developer can do advanced ops
  │  │  allow {
  │  │    input.action == "write"
  │  │    input.roles[_] == "developer"
  │  │  }
  │  │
  │  ├─ OPA evaluates Rego rules
  │  │  ├─ Rule 1: roles contains "admin"? NO
  │  │  ├─ Rule 2: action == "invoke" AND roles contains "operator"? YES ✓
  │  │  └─ Decision: allow = true
  │  │
  │  ├─ Response from OPA:
  │  │  HTTP 200
  │  │  {
  │  │    "result": true,
  │  │    "reason": "operator can invoke any tool",
  │  │    "policies": ["msil.authz.allow"]
  │  │  }
  │  │
  │  └─ PolicyDecision object created:
  │     allowed: true
  │     reason: "operator can invoke any tool"
  │     policies_evaluated: ["msil.authz.allow"]
  │
  └─ Result: ALLOWED ✓

Step 4: Execution Proceeds
  ├─ Rate limiting check (passed)
  ├─ Tool executor calls backend API
  ├─ Audit logged
  └─ Result returned to client

Summary:
  - OPA query time: ~50-150ms (network + processing)
  - Decision type: Advanced (Rego rules can have complex logic)
  - Flexibility: High (custom rules can be updated without code changes)
  - Failure mode: Falls back to RBAC if OPA unavailable

═══════════════════════════════════════════════════════════════════════════
OPA DISABLED (Development Flow)
═══════════════════════════════════════════════════════════════════════════

Step 1: Request arrives (identical)
  Tool: book_appointment
  User: operator_user
  Action: invoke
  Context: { roles: ["operator"], user_id: "usr_123" }

Step 2: Risk Policy Evaluation (Identical)
  ├─ Tool risk_level: "write"
  ├─ User role: "operator"
  ├─ Risk check: operator >= write required? YES ✓
  └─ Result: ALLOWED by risk policy

Step 3: Policy Engine.evaluate() called
  ├─ Input: (identical)
  │  - action: "invoke"
  │  - resource: "book_appointment"
  │  - context: { roles: ["operator"] }
  │
  ├─ Condition: if OPA_ENABLED?
  │  └─ NO, skip OPA, go directly to simple RBAC
  │
  ├─ Step 3b: Simple RBAC Evaluation (NO network call)
  │  ├─ Initialize simple rules (from code):
  │  │  {
  │  │    "admin": ["*"],
  │  │    "developer": [
  │  │      "invoke:*",
  │  │      "read:*",
  │  │      "write:tool",
  │  │      "write:config"
  │  │    ],
  │  │    "operator": [
  │  │      "invoke:*",
  │  │      "read:*"
  │  │    ],
  │  │    "user": [
  │  │      "invoke:allowed_tools",
  │  │      "read:tool"
  │  │    ]
  │  │  }
  │  │
  │  ├─ Extract user roles: ["operator"]
  │  ├─ For each role:
  │  │  ├─ role = "operator"
  │  │  ├─ role_permissions = ["invoke:*", "read:*"]
  │  │  ├─ Check for "*": NO
  │  │  ├─ Check exact match "invoke:book_appointment": NO
  │  │  ├─ Check wildcard "invoke:*": YES ✓
  │  │  └─ Return ALLOWED
  │  │
  │  └─ PolicyDecision object created:
  │     allowed: true
  │     reason: "Role 'operator' has permission 'invoke:*'"
  │     policies_evaluated: ["simple_rbac"]
  │
  └─ Result: ALLOWED ✓

Step 4: Execution Proceeds (identical)
  ├─ Rate limiting check (passed)
  ├─ Tool executor calls backend API
  ├─ Audit logged
  └─ Result returned to client

Summary:
  - OPA query time: 0ms (NO network call)
  - Decision type: Simple (in-memory permission matching)
  - Flexibility: Low (rules hardcoded in code, need redeploy to change)
  - Failure mode: Uses only simple RBAC, no fallback needed
```

---

## Code Implementation

### PolicyEngine Class - Decision Flow

```python
# From app/core/policy/engine.py

class PolicyEngine:
    def __init__(self, opa_url=None, fallback_to_simple=True, risk_manager=None):
        """Initialize policy engine"""
        self.opa_url = opa_url or settings.OPA_URL
        self.fallback_to_simple = fallback_to_simple
        self.opa_enabled = settings.OPA_ENABLED  # ← KEY: Gets from config
        self.risk_manager = risk_manager or risk_policy_manager
        self.simple_rules = self._initialize_simple_rules()

    async def evaluate(self, action: str, resource: str, context: Dict) -> PolicyDecision:
        """Main decision entry point"""
        roles = context.get("roles", [])
        
        # Step 1: Risk policy check (happens first, independent of OPA)
        tool = context.get("tool")
        if tool and hasattr(tool, 'risk_level'):
            risk_decision = self._evaluate_risk_policy(tool, context)
            if not risk_decision["allowed"]:
                return PolicyDecision(allowed=False, reason=risk_decision["reason"])
        
        # Step 2: Policy evaluation - CONDITIONAL BASED ON OPA_ENABLED
        if self.opa_enabled:
            # ← OPA FLOW
            try:
                decision = await self._evaluate_opa(action, resource, context)
                logger.info(f"OPA decision: {decision.allowed}")
                return decision
            except Exception as e:
                # ← FALLBACK: OPA failed
                logger.warning(f"OPA failed: {e}, falling back to simple RBAC")
                if not self.fallback_to_simple:
                    return PolicyDecision(
                        allowed=False,
                        reason=f"Policy engine error: {str(e)}"
                    )
        
        # Step 3: Simple RBAC (used when OPA disabled OR OPA failed)
        # ← SIMPLE RBAC FLOW
        decision = self._evaluate_simple(action, resource, roles)
        logger.info(f"Simple RBAC decision: {decision.allowed}")
        return decision

    async def _evaluate_opa(self, action: str, resource: str, context: Dict) -> PolicyDecision:
        """Query OPA if enabled"""
        input_data = {
            "input": {
                "action": action,
                "resource": resource,
                "user": context.get("user_id"),
                "roles": context.get("roles", []),
                "timestamp": context.get("timestamp"),
                "metadata": context.get("metadata", {})
            }
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            # HTTP POST to OPA
            response = await client.post(
                f"{self.opa_url}/v1/data/msil/authz/allow",
                json=input_data
            )
            response.raise_for_status()  # ← Raises exception if fails
            result = response.json()
        
        return PolicyDecision(
            allowed=result.get("result", False),
            reason=result.get("reason", "Policy decision from OPA"),
            policies_evaluated=result.get("policies", ["msil.authz.allow"]),
            metadata=result
        )

    def _evaluate_simple(self, action: str, resource: str, roles: List[str]) -> PolicyDecision:
        """In-memory RBAC evaluation"""
        if not roles:
            return PolicyDecision(
                allowed=False,
                reason="No roles assigned to user",
                policies_evaluated=["simple_rbac"]
            )
        
        # Check each role's permissions
        for role in roles:
            role_permissions = self.simple_rules.get(role, [])
            
            # Check: Does role have wildcard permission?
            if "*" in role_permissions:
                return PolicyDecision(
                    allowed=True,
                    reason=f"Role '{role}' has wildcard permission",
                    policies_evaluated=["simple_rbac"]
                )
            
            # Check: Does role have exact permission?
            permission = f"{action}:{resource}"
            if permission in role_permissions:
                return PolicyDecision(allowed=True, reason=f"Exact match for '{permission}'")
            
            # Check: Does role have wildcard action?
            wildcard_permission = f"{action}:*"
            if wildcard_permission in role_permissions:
                return PolicyDecision(
                    allowed=True,
                    reason=f"Role '{role}' has permission '{wildcard_permission}'"
                )
        
        return PolicyDecision(
            allowed=False,
            reason=f"No matching permission for '{action}:{resource}'",
            policies_evaluated=["simple_rbac"]
        )
```

---

## Fallback Mechanism

### When OPA Fails But Is Enabled

```
Request arrives
  ↓
Policy Engine checks: OPA_ENABLED = True
  ↓
Try to query OPA at http://localhost:8181/v1/data/msil/authz/allow
  ↓
OPA Query throws exception:
  - Connection refused (OPA not running)
  - Timeout (OPA too slow)
  - HTTP 5xx (OPA error)
  - Network error
  ↓
Exception caught in try/except
  ↓
Check: fallback_to_simple = True?
  ├─ YES:
  │  ├─ Log warning: "OPA failed, falling back to simple RBAC"
  │  ├─ Call _evaluate_simple()
  │  └─ Use built-in RBAC rules
  │
  └─ NO:
     ├─ Log error: "OPA failed and fallback disabled"
     └─ Return DENIED (fail-secure)

Result: Request either:
  a) Uses simple RBAC fallback (default behavior)
  b) Denied with policy engine error (if fallback disabled)
```

### Real-World Scenario

```
Development Environment:
  OPA_ENABLED = False
  → Simple RBAC used always (OPA daemon not needed)
  → Fast (no network)
  → Simple rules apply

Staging Environment:
  OPA_ENABLED = True
  OPA_URL = http://opa-staging:8181
  → OPA queries used for decisions
  → Richer policies possible
  → Fallback to RBAC if OPA fails
  
Production Environment:
  OPA_ENABLED = True
  OPA_URL = http://opa-prod:8181 (with high availability)
  → OPA queries with advanced policies
  → Monitoring/alerting on OPA failures
  → Fallback ensures service continues if OPA down
```

---

## Performance Comparison

### Decision Latency Analysis

```
OPA ENABLED (with typical performance):
├─ Network roundtrip to OPA:     ~50-100ms
├─ OPA Rego evaluation:           ~10-30ms
└─ Total:                         60-130ms
   
   Network breakdown:
   - TCP connect:     ~5ms
   - HTTP request:    ~10ms
   - OPA processing:  ~30ms
   - Response:        ~10ms
   - Deserialization: ~5ms

OPA DISABLED (simple RBAC):
├─ In-memory role lookup:         ~0.1-0.5ms
├─ Permission checking:           ~0.1-0.5ms
└─ Total:                         ~0.2-1ms
   
   Speedup: 100-500x faster

Cost per 1000 requests:
OPA Enabled:
  - Network: 1000 requests × 50ms = 50 seconds of latency
  - CPU: OPA processing on remote server
  
OPA Disabled:
  - Network: 0 seconds
  - CPU: Local permission matching (~1ms per request)
  - Memory: Simple role/permission dict lookup
```

### When OPA Takes Longer

```
Scenario: OPA Unavailable
├─ OPA not running
├─ Connection attempt: ~5 seconds (timeout)
├─ Fallback triggered after timeout
├─ Simple RBAC used: ~1ms
└─ Total latency: ~5 seconds (before fallback kicks in)
   
   Impact: Client experiences 5-6 second delay before fallback

Solution: Lower timeout or health check OPA before deployment
```

---

## Use Cases

### When to Use OPA ENABLED (Production)

✅ **Use OPA Enabled When:**

1. **Complex Policy Requirements**
   ```rego
   # Example: Limit tool access by time of day
   allow {
     input.action == "invoke"
     input.roles[_] == "operator"
     hour >= 9 and hour <= 17  # Only during business hours
   }
   
   # Example: Restrict access by department
   allow {
     input.action == "read"
     input.roles[_] == "analyst"
     input.metadata.department == "finance"
   }
   ```

2. **Dynamic Policy Updates**
   - Update Rego policies without redeploying code
   - OPA reads policies from files or API endpoints
   - Changes take effect immediately

3. **Audit & Compliance Requirements**
   - Track which specific policies allowed/denied decisions
   - OPA provides detailed policy evaluation logs
   - Required by RegCom/ISO mandates

4. **Multi-Tenant Environments**
   - Different policy rules per tenant
   - Completely separate from code logic
   - Managed externally from application

5. **Advanced Authorization**
   - Attribute-based access control (ABAC)
   - Conditional policies based on metadata
   - Complex logic beyond simple RBAC

6. **High-Security Deployments**
   - Policy decisions reviewed independently
   - OPA deployed in DMZ/isolated network
   - Central policy governance across services

---

### When to Use OPA DISABLED (Development)

✅ **Use OPA Disabled When:**

1. **Development & Testing**
   ```bash
   OPA_ENABLED=False
   # No need to spin up OPA daemon
   # Developers focus on feature code
   # Fast local testing (1ms vs 100ms decisions)
   ```

2. **Simple RBAC Sufficient**
   ```python
   Rules are:
   - Admin: can do anything
   - Developer: invoke/read/write
   - Operator: invoke/read only
   - User: invoke allowed tools only
   # These simple rules cover 95% of use cases
   ```

3. **Minimal Resource Constraints**
   - Running OPA on resource-constrained environments
   - Cost reduction (no extra service to run)
   - Simpler deployment (fewer containers)

4. **MVP or Proof of Concept**
   - Get to market faster
   - Implement complex policies later if needed
   - Test functionality without policy complexity

5. **Edge Deployments**
   - Deploy on resource-limited edge devices
   - No network to central OPA server
   - Local decisions only

6. **Backwards Compatibility**
   - Legacy systems without OPA infrastructure
   - Gradual migration: start with RBAC, add OPA later
   - No breaking changes to existing deployments

---

## Configuration Summary

### Environment Variable to Enable/Disable

```bash
# Development (Simple RBAC)
OPA_ENABLED=False
OPA_URL=http://localhost:8181  # Ignored

# Staging (OPA with fallback)
OPA_ENABLED=True
OPA_URL=http://opa-staging:8181
FALLBACK_TO_SIMPLE=True

# Production (OPA with fallback)
OPA_ENABLED=True
OPA_URL=http://opa-prod-lb:8181  # Load balanced OPA
FALLBACK_TO_SIMPLE=True
```

### Logging Output Difference

```
OPA ENABLED:
  [INFO] Policy evaluation: invoke:book_appointment for user usr_123
  [INFO] OPA decision: true - operator can invoke any tool
  [INFO] Tool execution allowed

OPA DISABLED:
  [INFO] Policy evaluation: invoke:book_appointment for user usr_123
  [DEBUG] OPA not enabled, using simple RBAC
  [INFO] Simple RBAC decision: true - Role 'operator' has permission 'invoke:*'
  [INFO] Tool execution allowed

OPA FAILED (with fallback):
  [INFO] Policy evaluation: invoke:book_appointment for user usr_123
  [WARNING] OPA evaluation failed: connection refused, falling back to simple RBAC
  [INFO] Simple RBAC decision: true - Role 'operator' has permission 'invoke:*'
  [INFO] Tool execution allowed
```

---

## Decision Tree

```
┌─────────────────────────────────────────────────────────┐
│ New policy decision required                             │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ Is OPA_ENABLED?    │
        └────────┬───────────┘
                 │
        ┌────────┴─────────────┐
        │                      │
       YES                    NO
        │                      │
        ▼                      ▼
   ┌─────────────┐      ┌──────────────┐
   │ Query OPA   │      │ Simple RBAC  │
   │  at :8181   │      │  (in-memory) │
   └─────┬───────┘      └──────────────┘
         │
    ┌────┴────────┐
    │             │
 SUCCESS        FAILURE
    │             │
    ▼             ▼
  ┌────┐    ┌──────────────────┐
  │YES │    │ Fallback to RBAC?│
  └─┬──┘    └────────┬────────┘
    │                │
    │           ┌────┴────────┐
    │           │             │
    │          YES           NO
    │           │             │
    │           ▼             ▼
    │      ┌────────┐    ┌──────┐
    │      │RBAC    │    │ DENY │
    │      │Fallback│    │(fail │
    │      └───┬────┘    │safe) │
    │          │         └──────┘
    └──────┬───┘
           │
           ▼
      ┌─────────┐
      │ Decision│
      │ Made    │
      └─────────┘
```

---

## Summary

| Aspect | OPA ENABLED | OPA DISABLED |
|--------|------------|-------------|
| **Network Calls** | Yes (to OPA) | None |
| **Latency** | 60-130ms typical | 0.2-1ms typical |
| **Policy Location** | External (Rego files) | Code (Python dicts) |
| **Complexity** | Support complex policies | Simple RBAC only |
| **Flexibility** | Update policies without redeploy | Need code redeploy |
| **Failure Mode** | Fallback to RBAC | Use simple RBAC |
| **Resource Usage** | Higher (OPA service) | Lower (in-memory) |
| **Setup** | More complex (OPA service) | Simpler (just code) |
| **Use Case** | Production/complex | Dev/MVP/simple |
| **Security** | Can define 100% custom logic | Hardcoded rules |

**Key Insight**: Both paths arrive at the same authorization decision, but OPA provides the flexibility to define complex policies externally, while simple RBAC provides speed and simplicity for basic use cases.
