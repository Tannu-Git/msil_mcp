# MSIL MCP Platform - Comprehensive Technical Guide
## Complete Architecture, Security, and Implementation Details

**Document Version**: 1.0  
**Date**: February 8, 2026  
**Confidentiality**: Client-Facing Technical Documentation  
**Audience**: Technical Decision Makers, Architects, Security Teams

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Platform Architecture](#platform-architecture)
3. [Authentication & Security Foundation](#authentication--security-foundation)
4. [Two-Layer Security Model](#two-layer-security-model)
5. [RBAC and Policy Engine (OPA)](#rbac-and-policy-engine-opa)
6. [Request Lifecycle - End-to-End](#request-lifecycle---end-to-end)
7. [Risk Management & Elevation](#risk-management--elevation)
8. [Rate Limiting & Quota Management](#rate-limiting--quota-management)
9. [Audit, Logging & Compliance](#audit-logging--compliance)
10. [Tool Registry & Discovery](#tool-registry--discovery)
11. [LLM Integration & Chat Interface](#llm-integration--chat-interface)
12. [Service Booking Demo - Stage 2](#service-booking-demo---stage-2)
13. [AWS APIM Integration](#aws-apim-integration)
14. [Operational Deployment](#operational-deployment)

---

## Executive Summary

The MSIL MCP (Model Context Protocol) Platform is a sophisticated, enterprise-grade tool orchestration and execution layer designed to safely expose backend services through a controlled, policy-driven interface. The platform sits between client applications and backend APIs, providing:

- **Secure Tool Discovery**: Users only see tools they're authorized to use
- **Fine-Grained Authorization**: RBAC + OPA for policy-driven access control
- **Risk-Based Access**: Tools can require elevation, confirmation, or approval
- **Comprehensive Auditability**: Every action is logged for compliance
- **LLM Integration**: Natural language interface for tool discovery and execution
- **Production-Grade Resilience**: Rate limiting, idempotency, circuit breakers, caching

### Key Innovation: Two-Layer Security Model

Unlike traditional monolithic authorization, MSIL separates **visibility** (exposure) from **execution** (authorization):

- **Layer B - Exposure**: "Who can SEE this tool?"
  - Bundle-level exposure (service_booking exposes ~45 tools)
  - Role-based permission management
  - Significant token reduction (250 tools → 45 visible)
  - Cached for performance

- **Layer A - Authorization**: "Who can EXECUTE this tool?"
  - RBAC with OPA fallback
  - Risk-based policies (read/write/privileged)
  - Tool-specific requirements (elevation, confirmation)
  - Rate limiting enforcement

This separation allows organizations to implement granular control without overwhelming users with unnecessary options.

---

## Platform Architecture

### High-Level System Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT APPLICATIONS                              │
│                    (Web, Mobile, Agent, LLM plugins)                       │
└────────────────────────────┬─────────────────────────────────────────────────┘
                             │
                   ┌─────────▼──────────┐
                   │  FastAPI Gateway   │
                   │  (Port 8000)       │
                   └─────────┬──────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐        ┌─────▼──────┐      ┌──────▼────┐
   │  /mcp    │        │  /chat     │      │  /admin   │
   │ endpoints│        │ endpoints  │      │endpoints  │
   └────┬────┘        └─────┬──────┘      └──────┬────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
        ┌────────────────────▼────────────────────────────┐
        │     SECURITY & GOVERNANCE LAYER                │
        │  ┌────────────────────────────────────────┐    │
        │  │ 1. Authentication (JWT/OIDC)           │    │
        │  │ 2. Exposure Manager (Layer B)          │    │
        │  │ 3. Policy Engine (RBAC + OPA)          │    │
        │  │ 4. Risk Management & Elevation         │    │
        │  │ 5. Rate Limiting & Quotas              │    │
        │  └────────────────────────────────────────┘    │
        └────────────┬─────────────────────────────────────┘
                     │
        ┌────────────▼─────────────────────────────┐
        │    CORE EXECUTION LAYER                  │
        │  ┌──────────────────────────────────┐    │
        │  │ Tool Registry                    │    │
        │  │ Tool Executor                    │    │
        │  │ Idempotency Store                │    │
        │  │ Response Shaper                  │    │
        │  └──────────────────────────────────┘    │
        └────────────┬─────────────────────────────┘
                     │
        ┌────────────▼─────────────────────────────┐
        │    INTEGRATION LAYER                     │
        │  ┌──────────────────────────────────┐    │
        │  │ Audit Service                    │    │
        │  │ Metrics Collection               │    │
        │  │ Cache Layer (Redis)              │    │
        │  │ Circuit Breakers                 │    │
        │  └──────────────────────────────────┘    │
        └────────────┬─────────────────────────────┘
                     │
        ┌────────────▼──────────────────────────────────────┐
        │              BACKEND SYSTEMS                      │
        │  ┌──────────────────┐    ┌────────────────┐      │
        │  │ MSIL APIM (AWS)  │    │ Mock API (Dev) │      │
        │  │ • Service APIs   │    │                │      │
        │  │ • Dealer Mgmt    │    │ Local Testing  │      │
        │  │ • Booking        │    │                │      │
        │  └──────────────────┘    └────────────────┘      │
        └───────────────────────────────────────────────────┘
```

### Core Components

1. **FastAPI Gateway** (Port 8000)
   - Request routing
   - CORS handling
   - Async request processing
   - Middleware for logging, metrics

2. **Endpoints**
   - `/mcp` - Model Context Protocol (tools/list, tools/call)
   - `/chat` - LLM chat interface with tool orchestration
   - `/admin` - Administrative operations
   - `/metrics` - Dashboard data
   - `/health` - Service health

3. **Request Pipeline** (In Order)
   - Authentication (JWT/OIDC validation)
   - RequestContext extraction (user, roles, elevation status)
   - Rate limiting check
   - Method routing (tools/list, tools/call, etc.)
   - Exposure filtering (Layer B)
   - Policy evaluation (Layer A)
   - Tool execution or response shaping

4. **Data Storage**
   - PostgreSQL: Tool registry, roles, permissions, audit logs
   - Redis: Caching, rate limiting, idempotency
   - S3: WORM audit storage (immutable, long-term retention)

---

## Authentication & Security Foundation

### Authentication Methods

The platform supports multiple authentication mechanisms:

#### 1. JWT Bearer Token Authentication
```
Request Header:
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Flow:
  1. Client obtains JWT token from OAuth2/OIDC provider
  2. Includes token in Authorization header
  3. Server validates JWT signature using configured secret
  4. Extracts claims: user_id, roles, scopes, elevation status
```

**JWT Claims Structure**:
```json
{
  "sub": "user@company.com",
  "user_id": "usr_123",
  "roles": ["operator", "developer"],
  "scopes": ["tool:invoke", "tool:read"],
  "elevation": {
    "is_elevated": true,
    "elevated_at": 1707392440,
    "elevation_expires_at": 1707396040
  },
  "iat": 1707392440,
  "exp": 1707479440
}
```

#### 2. OIDC (OpenID Connect)
When OAuth2/OIDC is enabled:
- Validates token against JWKS endpoint
- Verifies issuer and audience
- Checks required scopes
- Integrates with enterprise IAM (Azure AD, Okta, Keycloak)

#### 3. Development Mode
For local development and testing:
- `DEMO_MODE=true` allows unauthenticated requests
- Default user context: user_id="demo-user", roles=["admin"]
- Useful for Postman testing and local development

#### 4. API Key Authentication
- Optional X-API-Key header for backward compatibility
- Used alongside JWT for dual authentication
- Useful for service-to-service calls

### RequestContext - Normalized Security Context

Every request is normalized into a `RequestContext` containing:

```python
RequestContext:
  user_id: str              # User identifier (from JWT sub/user_id claim)
  roles: List[str]          # User roles (from JWT roles claim)
  scopes: List[str]         # Permission scopes (from JWT scope claim)
  client_id: str            # Client application ID
  correlation_id: str       # Request trace ID
  ip: str                   # Client IP address
  env: str                  # Environment (dev, staging, prod)
  is_elevated: bool         # Elevation status (from JWT elevation claim)
```

This context is passed through all security decisions (exposure, policy, rate limiting).

### Security Headers & CORS

The platform implements comprehensive CORS handling:

```
Allowed Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD
Allowed Headers: 
  - Content-Type
  - Authorization (Bearer tokens)
  - X-API-Key
  - X-Correlation-ID
  - X-User-ID, X-User-Roles (fallback headers)
  - Idempotency-Key (write operations)

Credentials Support: true (CORS credentials allowed)
Max-Age: 86400 (24-hour preflight caching)
```

---

## Two-Layer Security Model

This is the **key architectural innovation** that differentiates MSIL from traditional IAM systems.

### Problem It Solves

In traditional systems:
- Users request tool access → System grants or denies
- All tools are returned in discovery → User confusion (250+ tools)
- Token burn is high (sending all tool metadata)
- Fine-grained control is difficult

MSIL Solution:
- **Separate visibility from execution**
- Users only SEE relevant tools
- Users only EXECUTE permitted tools
- Security is enforced at two points (defense-in-depth)

### Layer B: Exposure Governance

**Question**: "Who can SEE this tool in tools/list?"

**Purpose**:
- Control tool visibility
- Reduce cognitive load (45 tools vs 250)
- Improve token efficiency
- Reduce API surface area

**How It Works**:

1. **Permission Types** (stored in database):
   ```
   expose:all              → User sees ALL tools
   expose:bundle:SERVICE   → User sees all tools in SERVICE bundle
   expose:tool:GET_DEALER  → User sees specific tool
   ```

2. **Resolution Process**:
   ```
   Query: SELECT permissions WHERE role IN ['operator', 'developer']
   
   Results:
     - operator has: expose:bundle:Service Booking
     - developer has: expose:all
   
   User Exposure Set = union of all role permissions
                     = { "expose:all" }
   
   Since "expose:all" present = all 250 tools visible
   Otherwise = union of all bundles + specific tools
   ```

3. **Execution Flow in tools/list**:
   ```
   Client Request:
     X-User-ID: user123
     X-User-Roles: operator
   
   Handler:
     1. Extract roles from context
     2. Query DB for expose:* permissions
     3. Parse permissions to tool references
     4. Cache result (TTL: 1 hour)
     5. Filter all_tools list by exposure set
     6. Apply policy engine to filtered tools
     7. Return only exposed + policy-approved tools
   ```

4. **Caching Strategy**:
   - **Key**: Combination of roles (sorted)
   - **Value**: Set of tool references
   - **TTL**: 1 hour (configurable)
   - **Benefit**: Dramatically reduces database queries
   - **Invalidation**: Manual cache clear on permission change

### Layer A: Authorization via Policy Engine

**Question**: "Can this user EXECUTE this tool right now?"

**Purpose**:
- Enforce fine-grained authorization
- Check tool-specific requirements
- Enforce rate limits
- Verify risk level allowed for user

**How It Works**:

1. **RBAC (Role-Based Access Control)**:
   ```
   Role Permissions:
     admin:     [invoke:*, read:*, write:*, delete:*]
     developer: [invoke:*, read:*, write:tool, write:config]
     operator:  [invoke:*, read:*]
     user:      [invoke:allowed_tools, read:tool]
   
   Decision Logic:
     For action "invoke" on resource "book_appointment":
       → Check if user's roles have permission
       → Match: invoke:* or invoke:book_appointment
       → Fallback: invoke:allowed_tools
   ```

2. **Risk-Based Authorization**:
   ```
   Tool Risk Levels:
     read      → Requires: user+ role, no elevation
     write     → Requires: operator+ role, no elevation
     privileged→ Requires: developer+ role, elevation required
   
   User Role Hierarchy:
     user (0) < operator (1) < developer (2) < admin (3)
   
   Access Decision:
     Tool risk_level: write
     User role: operator
     Is elevated: false
     
     Result: ALLOWED (operator >= write threshold)
   ```

3. **Policy Engine Flow**:
   ```
   Request: tools/call with tool=update_dealer
   
   Step 1: Check tool risk level (example: write)
     User role: operator → Can access write-level tools ✓
   
   Step 2: Check tool-specific requirements
     requires_elevation: false → No elevation needed ✓
     requires_confirmation: false → No confirmation needed ✓
   
   Step 3: Query OPA (if enabled) / Fallback to RBAC
     OPA Decision: Policy allows operator to invoke update_dealer ✓
   
   Step 4: Evaluate policy
     Decision: ALLOWED, Reason: "operator can invoke write tools"
   
   If DENIED → Return 403 with reason
   If ALLOWED → Proceed to execution
   ```

### Defense-in-Depth: Two Checks

The platform enforces both layers at different points:

```
Request Flow:
  ├─ tools/list
  │  ├─ Layer B Check: Is tool in user's exposure set?
  │  ├─ Layer A Check: Can user read this tool?
  │  └─ Response: Filtered list of tools
  │
  └─ tools/call
     ├─ Layer B Check (again): Is tool in user's exposure set?
     │  (Defense: prevents direct API calls to tool)
     ├─ Layer A Check: Can user execute this tool?
     ├─ Risk Check: Elevation? Confirmation? Required?
     ├─ Rate Limiting: Within quota?
     └─ Execute or Deny (403/409/429)
```

---

## RBAC and Policy Engine (OPA)

### RBAC Architecture

The system implements a robust role-based access control system with support for OPA (Open Policy Agent) as the policy decision engine.

#### Database Schema

```sql
-- Roles table
CREATE TABLE policy_roles (
  id UUID PRIMARY KEY,
  name VARCHAR(255) UNIQUE,           -- admin, developer, operator, user
  description TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Permissions table
CREATE TABLE policy_role_permissions (
  id UUID PRIMARY KEY,
  role_id UUID REFERENCES policy_roles(id),
  permission VARCHAR(255),            -- invoke:*, read:tool, expose:bundle:X
  created_at TIMESTAMP,
  UNIQUE(role_id, permission)
);

-- User role assignments
CREATE TABLE user_role_assignments (
  id UUID PRIMARY KEY,
  user_id VARCHAR(255),
  role_id UUID REFERENCES policy_roles(id),
  created_at TIMESTAMP,
  UNIQUE(user_id, role_id)
);
```

#### Permission Format

Permissions follow a structured syntax:

```
{action}:{resource}

Examples:
  invoke:*              → Invoke any tool
  invoke:book_appointment → Invoke specific tool
  read:*                → Read any tool metadata
  write:tool            → Write to tools (admin)
  read:config           → Read configuration
  expose:all            → See all tools
  expose:bundle:X       → See all tools in bundle X
  expose:tool:Y         → See specific tool Y
```

#### Built-in Roles

1. **Admin Role**
   - Permissions: ["*"] (wildcard - everything)
   - Purpose: Full system access
   - Examples: System administrators, support team

2. **Developer Role**
   - Permissions: 
     - invoke:*
     - read:*
     - write:tool
     - write:config
   - Purpose: Development and configuration
   - Examples: Backend engineers, DevOps

3. **Operator Role**
   - Permissions:
     - invoke:*
     - read:*
     - expose:bundle:Service Booking (or specific bundles)
   - Purpose: Day-to-day operations
   - Examples: Service advisors, booking agents

4. **User Role**
   - Permissions:
     - invoke:allowed_tools
     - read:tool
   - Purpose: Limited access to specific tools
   - Examples: Customers, basic users

### Policy Engine Implementation

#### Simple RBAC (Fallback)

When OPA is unavailable, the system uses built-in RBAC:

```python
Decision Logic:
  1. Extract user roles from request context
  2. For each role:
     a. Get role's permission list
     b. Check for wildcard permission (*) → ALLOW
     c. Check for exact permission match (action:resource) → ALLOW
     d. Check for wildcard action (action:*) → ALLOW
  3. If no role matches → DENY

Example Decision:
  Action: invoke
  Resource: book_appointment
  User Roles: [operator]
  
  Role operator permissions: [invoke:*, read:*]
  Match found: invoke:*
  Result: ALLOWED - "operator can invoke any tool"
```

#### OPA Integration (Optional)

When enabled, OPA provides advanced policy capabilities:

```python
Request to OPA:
  POST /v1/data/msil/authz/allow
  {
    "input": {
      "action": "invoke",
      "resource": "book_appointment",
      "user": "user@company.com",
      "roles": ["operator"],
      "timestamp": "2026-02-08T10:00:00Z",
      "metadata": {
        "ip": "192.168.1.100",
        "client": "mobile-app"
      }
    }
  }

OPA Policy Example (Rego):
  package msil.authz
  
  allow {
    input.action == "invoke"
    input.roles[_] == "operator"         # User has operator role
    allowed_tools["book_appointment"]    # Tool is in allowed list
  }
  
  allow {
    input.roles[_] == "admin"            # Admin can do anything
  }

Response from OPA:
  {
    "result": {
      "allow": true,
      "reason": "operator can invoke booking tools",
      "policies": ["msil.authz.allow"],
      "metadata": {...}
    }
  }
```

#### Fallback Behavior

```
Policy Evaluation Flow:
  
  If OPA enabled:
    Try: Query OPA → Get decision
    If timeout/error:
      Log warning
      If fallback_to_simple=true:
        Fallback to RBAC
      Else:
        Return DENY (fail-safe)
  Else:
    Use RBAC directly
```

---

## Request Lifecycle - End-to-End

This section walks through a complete request from entry to exit, highlighting every security checkpoint and validation.

### Complete Request Flow Example

Scenario: An Operator user calls "book_appointment" tool via tools/call

```
═══════════════════════════════════════════════════════════════════════════

STEP 1: REQUEST ARRIVES AT SERVER
─────────────────────────────────
HTTP POST /mcp
Headers:
  Content-Type: application/json
  Authorization: Bearer eyJhbGc...
  X-Correlation-ID: req-abc-123
  X-API-Key: msil-key-2026

Body:
  {
    "jsonrpc": "2.0",
    "id": "1",
    "method": "tools/call",
    "params": {
      "name": "book_appointment",
      "arguments": {
        "customer_id": "cust_456",
        "vehicle_id": "veh_789",
        "dealer_id": "dealer_101",
        "service_type": "regular_service",
        "preferred_date": "2026-02-15"
      }
    }
  }

═══════════════════════════════════════════════════════════════════════════

STEP 2: CORS & TRANSPORT LAYER
─────────────────────────────────
ASGI Middleware checks:
  ✓ CORS preflight (if OPTIONS) → Return 200 OK
  ✓ TLS/HTTPS validation (in production)
  ✓ Request size limits
  ✓ Content-Type validation (application/json)

Result: Pass through to FastAPI

═══════════════════════════════════════════════════════════════════════════

STEP 3: AUTHENTICATION
─────────────────────────────────
File: app/core/request_context.py

Handler "get_request_context" executes:
  
  a) Extract Authorization header
     Value: "Bearer eyJhbGc..."
  
  b) Validate JWT token (or OIDC if enabled)
     - Decode JWT with secret key
     - Verify signature (HMAC-SHA256)
     - Check expiration (iat, exp claims)
     - Verify issuer (if OIDC)
     - Verify audience (if OIDC)
     
     If validation fails:
       → Raise HTTPException(401, "Unauthorized")
       → Client receives 401 response
     
     If validation succeeds:
       → Extract payload claims
  
  c) Build RequestContext from claims
     payload = {
       "sub": "operator@company.com",
       "user_id": "usr_789",
       "roles": ["operator"],
       "scopes": ["tool:invoke"],
       "elevation": { "is_elevated": false }
     }
     
     RequestContext = {
       user_id: "usr_789",
       roles: ["operator"],
       scopes: ["tool:invoke"],
       client_id: None,
       correlation_id: "req-abc-123",
       ip: "203.0.113.42",
       env: "production",
       is_elevated: false
     }
  
  d) If AUTH_REQUIRED=true and no token:
     → Raise HTTPException(401, "Authentication required")

Result: RequestContext object available for downstream handlers

═══════════════════════════════════════════════════════════════════════════

STEP 4: MCP HANDLER ROUTING
─────────────────────────────────
File: app/api/mcp.py

@router.post("/mcp")
async def mcp_handler(request, context, x_api_key, idempotency_key):
  
  a) Check API Key (if configured)
     if settings.API_KEY and x_api_key != settings.API_KEY:
       if not settings.DEBUG:
         → Return JSON-RPC error: "Invalid API Key"
  
  b) Identify method from request
     method = "tools/call"
  
  c) Route to appropriate handler
     → Call handle_tools_call(params, correlation_id, context)

Result: Request routed to tools/call handler

═══════════════════════════════════════════════════════════════════════════

STEP 5: RATE LIMITING (OPTIONAL)
─────────────────────────────────
File: app/core/cache/rate_limiter.py

Check user rate limit:
  
  a) Get user's rate limit quota
     Default: 1000 requests per minute
     For "write" operations: 300 per minute
     For "privileged" operations: 100 per minute
  
  b) Check Redis counter for user
     Key: "user:usr_789:requests"
     
  c) If counter >= limit
     → Return rate limit error
     → HTTPException(429, "Rate limit exceeded")
     → Include Retry-After header (60 seconds)
     → Log rate limit decision
  
  d) If counter < limit
     → Increment counter
     → Set TTL to 1 minute
     → Continue to next step

Result: Rate limit validated

═══════════════════════════════════════════════════════════════════════════

STEP 6: TOOL LOOKUP
─────────────────────────────────
File: app/core/tools/executor.py & registry.py

a) Query tool registry for "book_appointment"
   Source: PostgreSQL tools table
   
   Result:
   {
     name: "book_appointment",
     display_name: "Book Appointment",
     bundle_name: "Service Booking",
     http_method: "POST",
     api_endpoint: "/api/booking/book",
     risk_level: "write",
     requires_elevation: false,
     requires_confirmation: false,
     rate_limit_tier: "standard",
     input_schema: {...}
   }

b) If tool not found
   → Tool Registry returns None
   → HTTPException(404, "Tool not found")
   → Return 404 to client

Result: Tool loaded successfully

═══════════════════════════════════════════════════════════════════════════

STEP 7: LAYER B - EXPOSURE CHECK (First Validation)
─────────────────────────────────────────────────────
File: app/core/exposure/manager.py & executor.py

Purpose: Verify tool is in user's exposure set (defense-in-depth)

a) Get user's exposed tools
   
   Query DB:
     SELECT DISTINCT permission
     FROM policy_roles pr
     JOIN policy_role_permissions prp ON pr.id = prp.role_id
     WHERE pr.name IN ('operator')
     AND prp.permission LIKE 'expose:%'
   
   Result: ["expose:bundle:Service Booking"]
   
   Check Cache:
     Key: "operator" (role hash)
     TTL: 1 hour
     Value: Set of tool references
   
   Cache miss → Query DB → Parse permissions
   
b) Parse exposure permissions
   
   Permission "expose:bundle:Service Booking"
     → Represents all tools in Service Booking bundle
     → Includes: book_appointment, resolve_customer, get_nearby_dealers, etc.
   
c) Check if tool_exposed
   
   Is tool.name in exposed set?
   Is tool.bundle in exposed set?
   
   Evaluation:
     Tool: book_appointment (bundle: Service Booking)
     User exposed bundles: [Service Booking]
     Result: EXPOSED ✓
   
d) If NOT exposed
   → Raise ToolNotExposedError
   → HTTPException(403, "Tool not exposed for this role")
   → Audit: Log the denial
   → Return 403

Result: Tool is exposed to user

═══════════════════════════════════════════════════════════════════════════

STEP 8: LAYER B - EXPOSURE FILTERING (tools/list)
──────────────────────────────────────────────────
(Note: This is skipped for tools/call but enforced in tools/list)

In handle_tools_list:
  
  a) Get all tools from registry (250 tools)
  b) Call exposure_manager.filter_tools(all_tools, user_id, roles)
  c) Apply policy engine evaluation for "read" action
  d) Return only exposed tools (45 tools in this case)

Result: Only visible tools are returned in discovery

═══════════════════════════════════════════════════════════════════════════

STEP 9: LAYER A - AUTHORIZATION CHECK
──────────────────────────────────────
File: app/core/policy/engine.py

Purpose: Verify user can actually EXECUTE this tool

a) Evaluate policy
   
   Inputs:
     Action: "invoke"
     Resource: "book_appointment"
     User context:
       - roles: ["operator"]
       - user_id: "usr_789"
       - is_elevated: false
   
b) Check tool risk level
   
   Tool risk_level: "write"
   Operator role requires: operator+ (hierarchy: operator=1)
   Check: operator >= write threshold?
   Result: YES ✓
   
c) Check elevation requirement
   
   Tool requires_elevation: false
   User is_elevated: false
   Check: false == false?
   Result: YES ✓
   
d) Check confirmation requirement
   
   Tool requires_confirmation: false
   user_confirmed in arguments: false
   Check: false == false?
   Result: YES ✓
   
e) Query OPA (if enabled) OR use simple RBAC
   
   Simple RBAC evaluation:
     For role "operator":
       Permissions: [invoke:*, read:*]
       Match check: invoke:* (wildcard) ✓
   
   Result: ALLOWED - "operator can invoke any tool"

f) If policy denied
   → PolicyDecision.allowed = false
   → Audit: Log policy denial
   → HTTPException(403, decision.reason)
   → Return 403

Result: User is authorized to execute

═══════════════════════════════════════════════════════════════════════════

STEP 10: RATE LIMITING - TOOL LEVEL
────────────────────────────────────
File: app/core/cache/rate_limiter.py

a) Get tool-specific rate limit quota
   
   Tool rate_limit_tier: "standard"
   Rate multiplier for "write":
     → 3x stricter than read
   
   Tool limit: 100 calls per minute
   
b) Check Redis counter for tool
   Key: "tool:book_appointment:requests"
   
c) If counter >= limit
   → HTTPException(429, "Rate limit exceeded")
   → Retry-After header
   → Return 429

Result: Tool rate limit validated

═══════════════════════════════════════════════════════════════════════════

STEP 11: IDEMPOTENCY CHECK
──────────────────────────
File: app/core/idempotency/store.py

Purpose: Prevent duplicate execution for write operations

a) Is this a write operation?
   HTTP method: POST, PUT, DELETE, PATCH?
   Tool.http_method: POST → YES, write operation
   
b) Was idempotency key provided?
   Header: Idempotency-Key: book-apt-2026-02-15
   
c) Check Redis for previous execution with same key
   Key: "idem:{user_id}:{idempotency_key}"
   
   If result cached:
     → Return cached result immediately
     → Skip actual tool execution
     → Log: "Idempotent retry, returning cached result"
   
   Else:
     → Continue to execution
     → After success, cache result with 24-hour TTL

Result: Idempotency validated

═══════════════════════════════════════════════════════════════════════════

STEP 12: TOOL EXECUTION
────────────────────────
File: app/core/tools/executor.py

a) Build request to backend API
   
   Base URL: Get from settings based on API_GATEWAY_MODE
     If "msil_apim": Use AWS APIM URL
     Else: Use mock API URL
   
   Headers:
     Content-Type: application/json
     Authorization: Bearer {jwt_token}
     Ocp-Apim-Subscription-Key: {subscription_key} (if APIM)
     X-Correlation-ID: req-abc-123 (trace correlation)
   
   URL: {base_url}/api/booking/book
   Method: POST
   Body: {
     "customer_id": "cust_456",
     "vehicle_id": "veh_789",
     "dealer_id": "dealer_101",
     "service_type": "regular_service",
     "preferred_date": "2026-02-15"
   }

b) Execute HTTP call with resilience
   
   Circuit Breaker: Check if service is healthy
   Retry Policy: Exponential backoff
     - Max 3 attempts
     - Wait 100ms, 300ms, 900ms between attempts
   
   async with httpx.AsyncClient() as client:
     response = await client.post(
       url,
       headers=headers,
       json=body,
       timeout=30.0
     )

c) Handle response
   
   Status 200-299:
     result = response.json()
     Proceed to logging
   
   Status 4xx/5xx:
     Raise exception
     error_message = response.text
     Proceed to error handling

Result: Backend API called, result obtained

═══════════════════════════════════════════════════════════════════════════

STEP 13: AUDIT LOGGING
────────────────────────
File: app/core/audit/service.py

a) Create audit event
   
   Event:
   {
     event_type: "tool_call",
     correlation_id: "req-abc-123",
     user_id: "usr_789",
     tool_name: "book_appointment",
     action: "invoke",
     status: "success",
     latency_ms: 145,
     request_size: 156,
     response_size: 894,
     error_message: None,
     timestamp: 2026-02-08T10:15:30.123Z,
     metadata: {
       params: {customer_id, vehicle_id, ...},
       result: {appointment_id, booking_ref, ...}
     }
   }

b) Mask PII in metadata
   - Customer email → masked
   - Phone numbers → partially masked
   - Vehicle details → preserved (business-critical)
   
c) Write to storage (dual-write)
   
   Write to PostgreSQL:
     INSERT INTO audit_logs (...)
     VALUES (...)
   
   Write to S3 WORM bucket:
     s3://msil-audit-prod/
        2026/02/08/
        req-abc-123.json
     
     (immutable, 12-year retention, encrypted)
   
d) Log to application logger
   
   INFO: AUDIT: tool_call | invoke | success | user=usr_789 | 
         tool=book_appointment | correlation=req-abc-123

Result: Action audited for compliance

═══════════════════════════════════════════════════════════════════════════

STEP 14: METRICS COLLECTION
──────────────────────────────
File: app/core/metrics/collector.py

a) Record execution metrics
   
   - Increment total tool executions
   - Record execution time (145 ms)
   - Track tool frequency
   - Update per-user metrics
   - Update per-role metrics

b) Store in memory (backed by Redis for HA)
   
   Metrics:
   {
     total_executions: 12453,
     tools_by_category: {service_booking: 5432, ...},
     latency_p50: 120ms,
     latency_p95: 850ms,
     latency_p99: 2100ms,
     error_rate: 0.02,
     rate_limit_hits: 15
   }

Result: Metrics available for dashboard

═══════════════════════════════════════════════════════════════════════════

STEP 15: RESPONSE SHAPING
──────────────────────────
File: app/core/response/shaper.py

a) Shape tool result into MCP format
   
   Tool result:
   {
     appointment_id: "apt_123456",
     booking_reference: "SB-2026-02-456",
     dealer_name: "ABC Motors Delhi",
     appointment_datetime: "2026-02-15T10:00:00Z",
     service_advisor: "Raj Kumar"
   }
   
b) Format as JSON-RPC response
   
   MCPResponse = {
     "jsonrpc": "2.0",
     "id": "1",
     "result": {
       "content": [
         {
           "type": "text",
           "text": "{\n  \"appointment_id\": \"apt_123456\",..."
         }
       ],
       "isError": false
     }
   }

Result: Response formatted for client

═══════════════════════════════════════════════════════════════════════════

STEP 16: RESPONSE SENT TO CLIENT
─────────────────────────────────

HTTP 200 OK
Headers:
  Content-Type: application/json
  Access-Control-Allow-Origin: *
  X-Correlation-ID: req-abc-123
  X-RateLimit-Remaining: 299
  X-RateLimit-Reset: 1707392460

Body:
  {
    "jsonrpc": "2.0",
    "id": "1",
    "result": {
      "content": [...],
      "isError": false
    }
  }

═══════════════════════════════════════════════════════════════════════════

COMPLETE REQUEST JOURNEY SUMMARY:

  1. ✓ Request arrives at FastAPI gateway
  2. ✓ CORS & transport validation
  3. ✓ JWT authentication
  4. ✓ RequestContext extracted
  5. ✓ MCP routing (tools/call identified)
  6. ✓ Rate limiting check (user level)
  7. ✓ Tool registry lookup
  8. ✓ Layer B - Exposure check (defense-in-depth)
  9. ✓ Layer A - Authorization (RBAC + OPA)
  10. ✓ Risk enforcement (elevation, confirmation)
  11. ✓ Rate limiting check (tool level)
  12. ✓ Idempotency check
  13. ✓ HTTP call to backend API
  14. ✓ Audit logging (PostgreSQL + S3)
  15. ✓ Metrics collection
  16. ✓ Response shaping (MCP format)
  17. ✓ Response sent to client

Total path: 17 security/validation checkpoints
Total latency introduced by MSIL: ~150-200ms (including backend time)
Audit footprint: Full compliance trail maintained
All actions traceable via correlation_id
```

---

## Risk Management & Elevation

### Risk Tiers for Tools

Every tool in the registry has a risk classification:

```python
Tool Risk Levels:

1. READ (Low Risk)
   - Example: get_nearby_dealers, resolve_customer, get_vehicle_info
   - What it does: Retrieves information only
   - Authority required: user+ (any authenticated user)
   - Elevation required: NO
   - Confirmation required: NO
   - Rate limit: Permissive (1000/min per user)
   - PII handling: Mask

2. WRITE (Medium Risk)
   - Example: book_appointment, update_dealer, cancel_booking
   - What it does: Modifies system state
   - Authority required: operator+ (service advisors, operations)
   - Elevation required: NO (normally)
   - Confirmation required: Sometimes (for destructive ops)
   - Rate limit: Standard (300/min per user)
   - PII handling: Mask

3. PRIVILEGED (High Risk)
   - Example: delete_booking, modify_user_roles, financial_settlement
   - What it does: Highly sensitive operations
   - Authority required: developer+ (administrators)
   - Elevation required: YES (must authenticate with elevated privileges)
   - Confirmation required: YES (explicit user acknowledgment)
   - Rate limit: Strict (100/min per user, max 5 concurrent)
   - PII handling: Redact
   - Approval: May require manager approval
```

### Elevation Mechanism (PIM/PAM-like)

When a tool requires elevation, users must authenticate with special privileges:

#### How Elevation Works

1. **User Requests Elevation**
   ```
   Initial JWT (regular token):
     {
       "user_id": "admin@company.com",
       "roles": ["developer"],
       "elevation": {"is_elevated": false}
     }
   
   User action: Click "Request Elevation"
   System action: Redirect to elevation authentication
   ```

2. **Elevation Authentication**
   ```
   Multi-factor authentication (MFA) required:
     - Verify password again (or passkey)
     - Enter OTP from authenticator app
     - Hardware security key (optional)
   
   Upon success:
     - Issue elevated JWT with elevation claim
     - elevation.is_elevated = true
     - elevation.elevated_at = current_timestamp
     - elevation.expires_at = current_timestamp + 1 hour  (configurable)
   ```

3. **Using Elevated Privileges**
   ```
   New request with elevated JWT:
   {
     "jsonrpc": "2.0",
     "method": "tools/call",
     "params": {
       "name": "delete_booking",
       "arguments": {...}
     }
   }
   
   Request headers:
     Authorization: Bearer {elevated_jwt}
   
   Server validation:
     Extract elevation claim
     Check: is_elevated == true?
     Check: elevation.expires_at > now?
     If yes → Allow privileged operation
     If no (expired) → Deny, request re-elevation
   ```

#### Elevation Enforcement in Code

```python
# In tool executor
async def execute(
    tool_name: str,
    arguments: Dict,
    is_elevated: bool = False,  # From JWT elevation claim
    ...
) -> Dict:
    tool = await tool_registry.get_tool(tool_name)
    
    # Check elevation requirement
    if tool.requires_elevation and not is_elevated:
        raise AuthorizationError(
            f"Tool '{tool_name}' requires elevation. "
            "Please authenticate with elevated privileges."
        )
    
    # Proceed to execution
    return await self._call_backend_api(tool, arguments)
```

### Confirmation Requirement

For destructive operations, explicit user confirmation is required:

```python
# Tool definition
delete_booking_tool = Tool(
    name="delete_booking",
    requires_confirmation=True,
    risk_level="privileged"
)

# Client must provide confirmation
request_body = {
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "delete_booking",
    "arguments": {
      "booking_id": "apt_123456",
      "user_confirmed": true,  # MUST be true
      "confirmation_code": "DELETE-APT-123456"  # Challenge-response
    }
  }
}

# Server validation
if tool.requires_confirmation and not arguments.get("user_confirmed"):
    raise PolicyError(
        f"Tool '{tool_name}' requires explicit confirmation. "
        "Please add 'user_confirmed': true."
    )
```

### Approval Workflows

For certain operations, manager approval may be required:

```python
# Example: Financial settlement tool

if tool.requires_approval:
    # Create approval request
    approval_request = {
        id: "apr_789",
        tool: "financial_settlement",
        requester: "user@company.com",
        amount: 50000,
        status: "pending",
        created_at: "2026-02-08T10:00:00Z",
        approvers: ["manager1@company.com", "manager2@company.com"]
    }
    
    # Store in database
    await approval_store.create(approval_request)
    
    # Wait for approval
    # Manager approves → update status to "approved"
    # System re-evaluates permission → allow execution
    
    # Timeout: 24 hours (configurable)
```

---

## Rate Limiting & Quota Management

### Rate Limiting Architecture

The platform implements sophisticated rate limiting to prevent abuse and ensure fair resource allocation.

#### Types of Limits

1. **Per-User Limits**
   ```
   Default: 1000 requests per minute per user
   
   Configuration per risk tier:
     read operations: 1000/min
     write operations: 300/min
     privileged operations: 100/min
   
   Storage: Redis sorted sets
     Key: "user:{user_id}:requests"
     Value: Sliding window counter
     TTL: 1 minute
   ```

2. **Per-Tool Limits**
   ```
   Default: 100 calls per minute per tool
   
   Configuration per risk tier:
     read tools: 1000/min (tools are cheap)
     write tools: 300/min (state modification)
     privileged tools: 50/min (sensitive)
   
   Storage: Redis
     Key: "tool:{tool_name}:requests"
     Value: Sliding window counter
     TTL: 1 minute
   ```

3. **Per-Role Limits** (future enhancement)
   ```
   Different quota for different user roles:
     admin: Unlimited (high trust)
     developer: 500/min
     operator: 1000/min
     user: 100/min
   ```

### Rate Limit Decision Flow

```
Check if rate limiting enabled:
  if RATE_LIMIT_ENABLED == true:
    
    Step 1: Get user's quota
      multiplier = get_rate_limit_multiplier(tool.rate_limit_tier)
      user_limit = RATE_LIMIT_PER_USER * multiplier
      
      // Multipliers by tier
      standard: 1.0x
      permissive: 0.5x (double the limit)
      strict: 3.0x (one-third the limit)
    
    Step 2: Check user counter
      user_count = Redis.get("user:{user_id}:requests")
      
      if user_count >= user_limit:
        remaining_time = Redis.TTL("user:{user_id}:requests")
        raise HTTPException(429, "Rate limit exceeded")
        response.headers["Retry-After"] = remaining_time
    
    Step 3: Get tool's quota
      tool_limit = RATE_LIMIT_PER_TOOL * multiplier
    
    Step 4: Check tool counter
      tool_count = Redis.get("tool:{tool_name}:requests")
      
      if tool_count >= tool_limit:
        remaining_time = Redis.TTL("tool:{tool_name}:requests")
        raise HTTPException(429, "Rate limit exceeded")
        response.headers["Retry-After"] = remaining_time
    
    Step 5: Increment both counters
      Redis.incr("user:{user_id}:requests")
      Redis.incr("tool:{tool_name}:requests")
      Redis.expire("user:{user_id}:requests", 60)
      Redis.expire("tool:{tool_name}:requests", 60)
      
    Step 6: Allow request to proceed
```

### Handling Rate Limit Responses

When rate limit is exceeded, client receives:

```http
HTTP 429 Too Many Requests
Retry-After: 45
Content-Type: application/json

{
  "detail": "Rate limit exceeded",
  "retry_after": 45,
  "limit_type": "tool",
  "reset_at": "2026-02-08T10:01:45Z"
}

Client behavior:
  - Store Retry-After header (45 seconds)
  - Wait before retrying
  - Show user: "Service busy, please try again in 45 seconds"
```

### Distributed Rate Limiting

For multi-instance deployments, rate limiting uses central Redis:

```python
# All instances share same Redis
REDIS_URL = "redis://redis-prod.example.com:6379"

# Lock on write
user_count = await redis.incr(f"user:{user_id}")
# All instances see incremented value
# Rate limiting is globally consistent
```

---

## Audit, Logging & Compliance

### Audit Trail Architecture

The platform maintains comprehensive, immutable audit trails for compliance.

#### Event Types Logged

1. **Tool Call Events**
   ```json
   {
     "event_type": "tool_call",
     "correlation_id": "req-abc-123",
     "timestamp": "2026-02-08T10:15:30.123Z",
     "user_id": "usr_789",
     "tool_name": "book_appointment",
     "action": "invoke",
     "status": "success",
     "latency_ms": 145,
     "request_size": 156,
     "response_size": 894,
     "metadata": {
       "params": {...},
       "result": {...}
     }
   }
   ```

2. **Policy Decision Events**
   ```json
   {
     "event_type": "policy_decision",
     "correlation_id": "req-def-456",
     "timestamp": "2026-02-08T10:16:00.000Z",
     "user_id": "usr_790",
     "tool_name": "delete_booking",
     "action": "invoke",
     "status": "denied",
     "error_message": "requires elevation",
     "metadata": {
       "decision": {
         "allowed": false,
         "reason": "Tool requires elevation"
       },
       "context": {
         "roles": ["operator"],
         "is_elevated": false
       }
     }
   }
   ```

3. **Authentication Events**
   ```json
   {
     "event_type": "authentication",
     "timestamp": "2026-02-08T10:00:00.000Z",
     "user_id": "usr_789",
     "action": "login",
     "status": "success",
     "auth_method": "oidc",
     "ip_address": "203.0.113.42"
   }
   ```

4. **Administrative Events**
   ```json
   {
     "event_type": "admin_action",
     "timestamp": "2026-02-08T11:00:00.000Z",
     "admin_user": "admin@company.com",
     "action": "create_role",
     "resource": "operator",
     "status": "success"
   }
   ```

#### PII Handling

The system masks PII in logs:

```python
# Before logging
metadata = {
  "customer_email": "john.doe@example.com",
  "phone": "9876543210",
  "vehicle_number": "MH12AB1234"
}

# After PII masking
metadata = {
  "customer_email": "john.d***@example.com",
  "phone": "987654****",
  "vehicle_number": "MH12AB1234"  # Business-critical, not masked
}
```

### Dual-Write Audit Storage

Audit logs are written to two systems for resilience and compliance:

1. **PostgreSQL (Hot Storage)**
   ```sql
   CREATE TABLE audit_logs (
     id UUID PRIMARY KEY,
     event_type VARCHAR(50),
     correlation_id VARCHAR(100),
     timestamp TIMESTAMP,
     user_id VARCHAR(255),
     tool_name VARCHAR(255),
     action VARCHAR(50),
     status VARCHAR(20),
     error_message TEXT,
     request_size INT,
     response_size INT,
     latency_ms INT,
     metadata JSONB,
     created_at TIMESTAMP DEFAULT NOW(),
     INDEX (user_id, created_at),
     INDEX (tool_name, created_at),
     INDEX (correlation_id)
   );
   ```
   - Used for: Dashboard queries, recent audit review
   - Retention: 90 days (hot)
   - Performance: Queries fast
   
2. **S3 WORM Storage (Archive)**
   ```
   Bucket: s3://msil-audit-prod/
   Structure:
     2026/02/08/
       req-abc-123.json
       req-def-456.json
       req-ghi-789.json
   
   Configuration:
     - Write Once Read Many (WORM)
     - No deletion possible
     - Server-side encryption
     - Versioning enabled
     - MFA delete enabled
     - Retention policy: 12 years (compliance)
   ```
   - Used for: Compliance audits, legal inquiries
   - Retention: 12 years (long-term)
   - Access: Highly restricted

### Audit Query Examples

```sql
-- Find all operations by a user
SELECT * FROM audit_logs
WHERE user_id = 'usr_789'
ORDER BY timestamp DESC;

-- Find failed policy decisions
SELECT * FROM audit_logs
WHERE event_type = 'policy_decision'
AND status = 'denied'
ORDER BY timestamp DESC;

-- Find high-latency operations
SELECT * FROM audit_logs
WHERE event_type = 'tool_call'
AND latency_ms > 1000
ORDER BY latency_ms DESC;

-- Track tool usage over time
SELECT 
  DATE(timestamp) as date,
  tool_name,
  COUNT(*) as call_count,
  AVG(latency_ms) as avg_latency
FROM audit_logs
WHERE event_type = 'tool_call'
GROUP BY date, tool_name
ORDER BY date DESC;
```

---

## Tool Registry & Discovery

### Tool Metadata

Each tool in the registry contains comprehensive metadata:

```python
@dataclass
class Tool:
    # Identity
    id: UUID
    name: str                          # Unique identifier
    display_name: str                  # User-friendly name
    description: str                   # What the tool does
    
    # Classification
    category: str                      # service_booking, dealer_mgmt, etc.
    bundle_name: str                   # Group of related tools
    
    # API Configuration
    api_endpoint: str                  # /api/booking/book
    http_method: str                   # POST, GET, etc.
    input_schema: Dict                 # JSON Schema for input validation
    output_schema: Optional[Dict]      # Response format
    headers: Dict[str, str]            # Custom headers
    auth_type: str                     # Authentication type
    
    # Status
    is_active: bool                    # Active/inactive
    version: str                       # Tool version
    created_at: datetime
    updated_at: datetime
    
    # Risk & Security
    risk_level: str                    # read, write, privileged
    requires_elevation: bool           # Needs elevated auth
    requires_confirmation: bool        # Needs explicit approval
    requires_approval: bool            # Needs manager sign-off
    
    # Resource Management
    max_concurrent_executions: int     # Concurrency limit
    rate_limit_tier: str              # standard, permissive, strict
```

### Tool Discovery Flow

#### A) Discovery via tools/list

```
Client Request:
  GET /mcp
  Method: "tools/list"

Server Flow:
  1. Authenticate user → Get context (roles, elevation)
  2. Query tool registry → Load ALL tools
  3. Apply exposure filter → See only exposed tools
  4. Apply policy filter → See only authorized tools
  5. Build tool definitions → Schema + metadata
  6. Shape response → MCP format
  7. Return 45 tools (from 250) to operator user

Sample Response:
  {
    "tools": [
      {
        "name": "resolve_customer",
        "description": "Resolve customer from mobile number",
        "inputSchema": {...},
        "bundle": "Service Booking"
      },
      {
        "name": "resolve_vehicle",
        "description": "Get vehicle details",
        "inputSchema": {...},
        "bundle": "Service Booking"
      },
      ...
    ]
  }
```

#### B) Discovery via LLM Chat

```
User message: "I want to book a service for my car"

Chat Handler:
  1. Extract user context from JWT
  2. Load all tools from registry (250)
  3. Apply exposure filter (45 tools visible)
  4. Apply policy filter (all 45 authorized)
  5. Send tool definitions to OpenAI
  6. LLM decides which tools to recommend
  7. LLM response: "I can help. Let me first resolve your customer details..."
  
LLM has context:
  - 45 relevant tools
  - Descriptions and schemas
  - Only tools user can actually execute
```

### Tool Loading & Caching

```python
class ToolRegistry:
    
    async def list_tools(self) -> List[Tool]:
        """Get all active tools"""
        # Check in-memory cache first
        if self._loaded:
            return self._tools.values()
        
        # Load from database on first call
        await self._load_from_db()
        self._loaded = True
        
        return self._tools.values()
    
    async def _load_from_db(self):
        """Load tools from PostgreSQL"""
        # Query all tools
        # Build Tool objects
        # Cache in memory
        
    async def get_tool(self, name: str) -> Optional[Tool]:
        """Get specific tool by name"""
        await self._ensure_loaded()
        return self._tools.get(name)
```

---

## LLM Integration & Chat Interface

### Chat Flow Architecture

The chat interface orchestrates LLM with tool access:

```
User Input (Natural Language)
  ↓
[Chat Handler]
  ├─ Extract context (user, roles, elevation)
  ├─ Load available tools (filtered by exposure/policy)
  ├─ Send to OpenAI with tool definitions
  ├─ Get response with tool calls
  ├─ Execute requested tools (with security checks)
  └─ Return results to LLM
  ↓
LLM Response (Natural Language)
  ↓
Client (Web/Mobile/Agent)
```

### Full Conversation Flow Example

```
STEP 1: User Sends Message
─────────────────────────────
User (in chat UI): 
  "I want to book a regular service for my Maruti Swift"

Request body:
{
  "session_id": "sess_abc123",
  "message": "I want to book a regular service for my Maruti Swift"
}

STEP 2: Chat Handler Processes
─────────────────────────────────
Handler executed:
  - Extract RequestContext from JWT
    user_id: "usr_456"
    roles: ["customer"]
    is_elevated: false
  
  - Load tools for this user
    Get all tools → 250
    Apply exposure filter
    Apply policy filter
    Available tools: ~45
  
  - Create system prompt with tools
    "You have access to these tools..."
  
  - Send to OpenAI API
    model: "gpt-4"
    messages: [
      {"role": "system", "content": {...}},
      {"role": "user", "content": "I want to book..."}
    ]
    tools: [
      {name: "resolve_customer", ...},
      {name: "resolve_vehicle", ...},
      ...
    ]

STEP 3: LLM Responds
──────────────────────
OpenAI decides:
  "I need to resolve customer and vehicle details first"

Response:
{
  "choices": [
    {
      "finish_reason": "tool_calls",
      "message": {
        "tool_calls": [
          {
            "id": "call_123",
            "function": {
              "name": "resolve_customer",
              "arguments": "{\"mobile\": \"9876543210\"}"
            }
          }
        ]
      }
    }
  ]
}

STEP 4: Execute Tool (with Checks)
────────────────────────────────────
Tool: "resolve_customer"
Arguments: {"mobile": "9876543210"}

Execution:
  1. Check if tool exposed to user (Layer B)
     → User role: customer
     → Customer has access to Service Booking bundle
     → Tool is in Service Booking bundle
     → EXPOSED ✓
  
  2. Check authorization (Layer A)
     → Action: invoke
     → Tool: resolve_customer
     → Risk level: read
     → User role: customer
     → Policy: customer can invoke read tools
     → AUTHORIZED ✓
  
  3. Call backend API
     POST http://mock-api/api/customer/resolve
     Body: {"mobile": "9876543210"}
     
     Response:
     {
       "customer_id": "cust_789",
       "name": "Rajesh Kumar",
       "email": "rajesh@example.com",
       "phone": "9876543210",
       "vehicle_count": 2
     }
  
  4. Return to LLM
     tool_result: {customer_id: "cust_789", name: "Rajesh Kumar", ...}

STEP 5: LLM Continues
──────────────────────
LLM has customer details now, decides:
  "Now I need to get vehicle details"

Makes another tool call:
  Tool: "resolve_vehicle"
  Arguments: {"registration_number": "MH12AB5678"}
  
  (Execution follows same checks)
  
  Response:
  {
    "vehicle_id": "veh_123",
    "registration": "MH12AB5678",
    "model": "Maruti Swift",
    "year": 2020
  }

STEP 6: LLM Final Response
────────────────────────────
With customer & vehicle details, LLM responds:

"Great! I found your details:
- Name: Rajesh Kumar
- Vehicle: Maruti Swift (2020) - MH12AB5678

To book a regular service, I'll need:
1. Preferred service date
2. Preferred dealer location
3. Any specific concerns

Would you like to proceed?"

STEP 7: User Provides More Info
────────────────────────────────
User: "I want to book for February 15 at the Delhi dealer"

LLM:
  1. Calls "get_nearby_dealers" (to verify)
  2. Calls "book_appointment" with full details
  3. Returns confirmation with booking reference

STEP 8: Response Sent to Client
─────────────────────────────────
Chat Response:
{
  "message": "✓ Appointment booked successfully!",
  "booking_details": {
    "booking_reference": "SB-2026-02-001",
    "date": "2026-02-15T10:00:00Z",
    "dealer": "ABC Motors Delhi",
    "service_type": "Regular Service"
  }
}

User sees this in chat interface ✓
```

---

## Service Booking Demo - Stage 2

### Demo Scenario Overview

When the MSIL MCP platform is connected to the client's pre-prod AWS APIM, Stage 2 demo will showcase:

#### **Setup**
- Client has MSIL APIM/pre-prod deployed in AWS
- Service booking APIs available at: `https://apim-preprod.client.com/api/`
- MSIL MCP Server connects to this APIM
- Demo users created with operator, customer roles

#### **Key APIs Used**

1. **Customer Resolution**
   ```
   POST /api/customer/resolve
   Body: {"mobile": "9876543210"}
   Response: {customer_id, name, email, phone, vehicle_count}
   ```

2. **Vehicle Resolution**
   ```
   POST /api/vehicle/resolve
   Body: {"registration_number": "MH12AB1234"}
   Response: {vehicle_id, registration, model, year, service_history}
   ```

3. **Dealer Search**
   ```
   POST /api/dealers/nearby
   Body: {"city": "Delhi", "area": "South Delhi"}
   Response: [{dealer_id, name, location, phone, services}]
   ```

4. **Service Slot Availability**
   ```
   GET /api/dealerships/{dealer_id}/slots
   Params: {date, service_type}
   Response: [{slot_id, time, available}]
   ```

5. **Book Appointment**
   ```
   POST /api/booking/book
   Body: {
     customer_id, vehicle_id, dealer_id,
     service_type, preferred_date, service_advisor_id
   }
   Response: {appointment_id, booking_reference, confirmation}
   ```

### Stage 2 Demo Script

#### **Demo Part 1: Tool Discovery**

Presenter shows:

```
"Demo begins at 10:00 AM. A customer service advisor (operator role) 
opens the MSIL MCP dashboard in their browser."

Tools List Response:
  [Filtered to Service Booking bundle only]
  
  ✓ Resolve Customer (from mobile)
  ✓ Resolve Vehicle (from registration)
  ✓ Get Nearby Dealers (by city/area)
  ✓ Check Service Slots (date/time)
  ✓ Book Appointment (create booking)
  ✓ Cancel Appointment (requires confirmation)
  ✓ Reschedule Service (manager approval)
  
  "As an operator, you see ONLY the 7 tools you need.
   All 250 backend tools are hidden - you don't see dealer admin,
   financial stuff, or system configuration tools."
```

**Key Point**: Operator sees only service booking tools despite having context to more. This is Layer B (Exposure).

#### **Demo Part 2: Chat-Based Booking**

Presenter shows chat interface:

```
AGENT (into chat): "I have a customer who wants to book a service.
                    His mobile is 9876543210 and he has a Maruti Swift."

System response (behind the scenes):
  1. Call resolve_customer("9876543210")
     ✓ Found: Rajesh Kumar (8 previous services)
  2. Call resolve_vehicle("MH12AB5678") via LLM understanding
     ✓ Found: Maruti Swift 2020

Chat output:
  "Found customer Rajesh Kumar with Maruti Swift (2020).
   Last service 3 months ago. Vehicle in good condition.
   Where would you like to book the service?"

AGENT: "Delhi, South Delhi area, around Feb 15"

System response:
  1. Call get_nearby_dealers("Delhi", "South Delhi")
     ✓ Found: ABC Motors, XYZ Service Center
  2. Call check_service_slots(dealer_id, "2026-02-15")
     ✓ Slots available: 9:00 AM, 10:00 AM, 2:00 PM

Chat output:
  "Available slots at ABC Motors (South Delhi):
   • 9:00 AM - Regular Service (4 hours)
   • 10:00 AM - Premium Check-up (2 hours)
   • 2:00 PM - Regular Service (4 hours)"

AGENT: "Book 10:00 AM at ABC Motors"

System response:
  1. Check authorization (Layer A)
     ✓ Operator can invoke book_appointment
     ✓ No elevation required
     ✓ No confirmation required (standard booking)
  
  2. Call book_appointment(customer_id, vehicle_id, dealer_id, 
                          "2026-02-15T10:00:00Z", "Premium Check-up")
  
  3. Call log_audit_event(event_type="tool_call", tool_name="book_appointment", ...)
     ✓ Written to PostgreSQL (hot storage)
     ✓ Written to S3 WORM (immutable archive)
  
  4. Collect metrics
     ✓ Execution latency: 234 ms
     ✓ Tool popularity: +1
     ✓ Success rate: maintained

Chat output:
  "✓ BOOKING CONFIRMED!
   Booking Reference: SB-2026-02-001234
   Date: February 15, 2026 at 10:00 AM
   Location: ABC Motors, South Delhi
   Service: Premium Check-up (2 hours)
   Service Advisor: Raj Kumar (8 years experience)
   
   Customer will receive SMS and email confirmation shortly."
```

**Key Points**:
- LLM orchestrated 4 tool calls automatically
- User didn't need to know API details
- All tool calls passed both security layers
- Full audit trail created
- Natural language interface hides complexity

#### **Demo Part 3: Authorization Denial** (Optional)

To show security working:

```
SCENARIO: Admin user tries to call financial settlement tool

Request:
  Tool: "financial_settlement"
  Amount: $5000
  
System evaluation:
  1. Tool found in registry ✓
  2. Check exposure (Layer B)
     ✓ Admin has "expose:all"
  3. Check authorization (Layer A)
     ✓ Tool: financial_settlement (privileged risk level)
     ✓ User: admin role ✓
  4. Check elevation requirement
     ✓ Tool requires_elevation: true
     ✓ User is_elevated: false
     ✓ ELEVATION REQUIRED!

Response: 403 "Tool requires elevation"

Admin clicks "Request Elevation"
  → Redirected to MFA
  → Enters password + OTP
  → Gets elevated JWT

Retry request with elevated JWT:
  ✓ All checks pass
  ✓ Tool executes
  ✓ Settlement processed
  ✓ Audit: {event: "elevation_used", tool: "financial_settlement", ...}
```

**Key Point**: Security isn't a blocker, it's a "trust but verify" mechanism. Admin can still do job, but actions are verified and audited.

#### **Demo Part 4: Audit Trail**

Presenter shows admin dashboard:

```
Audit Trail for 2026-02-08:
  10:00 AM - AUTHENTICATION | Login | Success | user=operator@company.com
  10:01 AM - TOOL_CALL | resolve_customer | Success | latency=89ms
  10:01 AM - TOOL_CALL | resolve_vehicle | Success | latency=142ms
  10:02 AM - TOOL_CALL | get_nearby_dealers | Success | latency=156ms
  10:02 AM - TOOL_CALL | check_service_slots | Success | latency=234ms
  10:03 AM - TOOL_CALL | book_appointment | Success | latency=567ms
  10:03 AM - POLICY_DECISION | Authorization | Allowed | tool=book_appointment
  
  [Click appointment booking]
    Event Details:
    - request_id: req-abc-123
    - user: operator@company.com
    - tool: book_appointment
    - arguments: {customer_id, vehicle_id, dealer_id, ...}
    - result: {appointment_id: apt_123, booking_ref: SB-2026-02-001}
    - latency: 567 ms
    - status: success

Metrics Dashboard:
  - Total bookings today: 47
  - Avg latency: 234 ms
  - Success rate: 98.9%
  - Most used tool: book_appointment (13 calls)
  - Rate limit hits: 0
```

**Key Point**: Complete audit trail for compliance. Every action is traceable.

---

## AWS APIM Integration

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    CLIENT ENVIRONMENT (AWS)                 │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │         Azure API Management (APIM)                    │  │
│ │  (Pre-prod: apim-preprod.client.com)                  │  │
│ │                                                        │  │
│ │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐   │  │
│ │  │   Service    │  │   Dealer     │  │ Financial  │   │  │
│ │  │   Booking    │  │ Management   │  │ Settlement │   │  │
│ │  │   APIs       │  │   APIs       │  │   APIs     │   │  │
│ │  └──────┬───────┘  └──────┬───────┘  └────────────┘   │  │
│ │         │                 │                            │  │
│ │         └─────────────────┴────────────────────────┐   │  │
│ │                                                    │   │  │
│ │                          ┌──────────────────────────┘   │  │
│ │                          │                              │  │
│ │               ┌──────────▼────────────┐                │  │
│ │               │  APIM Gateway         │                │  │
│ │               │  Authentication       │                │  │
│ │               │  Rate Limiting        │                │  │
│ │               │  Logging              │                │  │
│ │               └──────────┬────────────┘                │  │
│ │                          │                             │  │
│ └──────────────────────────┼─────────────────────────────┘  │
│                            │                                 │
│                 ┌──────────▼──────────┐                      │
│                 │   AWS WAF/Security  │                      │
│                 │   AWS CloudFront    │                      │
│                 └──────────┬──────────┘                      │
└──────────────────────────────┼──────────────────────────────┘
                               │
                               │ (Inbound)
                               │
┌──────────────────────────────▼──────────────────────────────┐
│         MSIL MCP SERVER (Client Deployed)                   │
│         (Port 8000)                                         │
│                                                            │
│ ┌──────────────────────────────────────────────────────┐  │
│ │          FastAPI Router                             │  │
│ │          /mcp, /chat, /admin                        │  │
│ └────────────┬─────────────────────────────────────────┘  │
│              │                                            │
│ ┌────────────▼─────────────────────────────────────────┐  │
│ │     Security & Governance Layer                      │  │
│ │     (Auth, Exposure, Policy, Rate Limiting)          │  │
│ └────────────┬─────────────────────────────────────────┘  │
│              │                                            │
│ ┌────────────▼─────────────────────────────────────────┐  │
│ │     Tool Executor                                    │  │
│ │     (Calls backend APIs)                             │  │
│ └────────────┬─────────────────────────────────────────┘  │
│              │                                            │
│ ┌────────────▼─────────────────────────────────────────┐  │
│ │     HTTP Client (httpx)                              │  │
│ │     • Retries with exponential backoff               │  │
│ │     • Circuit breaker for fault tolerance            │  │
│ │     • Request/response logging                       │  │
│ └────────────┬─────────────────────────────────────────┘  │
└──────────────┼──────────────────────────────────────────────┘
               │
               │ (Outbound - HTTPS)
               │
               ▼
        ┌──────────────┐
        │  Client APIM │
        │   (Pre-prod) │
        └──────────────┘
```

### Integration Configuration

#### API Gateway Mode: MSIL_APIM

```python
# config.py
API_GATEWAY_MODE = "msil_apim"  # or "mock_api" for dev

# MSIL APIM settings
MSIL_APIM_BASE_URL = "https://apim-preprod.client.com"
MSIL_APIM_SUBSCRIPTION_KEY = "xxxx-yyyy-zzzz-wwww"

# Dual authentication
API_KEY = "msil-key-production-2026"
JWT_SECRET = "secret-key-for-internal-signing"
```

#### Request Flow to APIM

```
MSIL Server Outbound Request:

POST https://apim-preprod.client.com/api/booking/book

Headers:
  Content-Type: application/json
  Accept: application/json
  Ocp-Apim-Subscription-Key: xxxx-yyyy-zzzz-wwww
  x-api-key: msil-key-production-2026
  Authorization: Bearer mock-jwt-token-datetime-based
  X-Correlation-ID: req-abc-123  (trace correlation)
  User-Agent: MSIL-MCP/1.0.0

Body:
  {
    "customer_id": "cust_456",
    "vehicle_id": "veh_789",
    "dealer_id": "dealer_101",
    "service_type": "regular_service",
    "preferred_date": "2026-02-15T10:00:00Z",
    "service_advisor_id": "advisor_001"
  }

---

APIM Processing:

1. Validate subscription key
   ✓ Ocp-Apim-Subscription-Key is valid
2. Check rate limits (APIM level)
   ✓ Within quota
3. Log request
   ✓ Write to APIM analytics
4. Route to backend service
   → POST /api/booking/book
5. Process request
   → Create appointment
   → Update system state
6. Return response
   → 200 OK with result

---

Response:

HTTP 200 OK

{
  "appointment_id": "apt_123456",
  "booking_reference": "SB-2026-02-001",
  "customer_id": "cust_456",
  "vehicle_id": "veh_789",
  "dealer_id": "dealer_101",
  "appointment_datetime": "2026-02-15T10:00:00Z",
  "service_Type": "Regular Service",
  "service_advisor": "Raj Kumar",
  "service_center_phone": "+91-11-XXXX-XXXX",
  "confirmation_id": "CONF-2026-02-001"
}

---

MSIL Processing Response:

1. Receive response from APIM
2. Check status code
   ✓ 200 OK - success
3. Parse response JSON
4. Audit log creation
   event: tool_call
   status: success
   latency: 567 ms
5. Metrics update
6. Shape for client (JSON-RPC)
7. Return to client
```

### Resilience & Fault Tolerance

The integration includes sophisticated error handling:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=100, max=1000),
    retry=retry_if_exception_type(httpx.HTTPError)
)
@circuit(failure_threshold=5, recovery_timeout=60)
async def _call_apim(url, headers, body):
    """
    Call APIM with retry and circuit breaker
    
    Retry policy:
      - 3 attempts maximum
      - Exponential backoff: 100ms, 300ms, 900ms
      - Only retry on network errors (not 4xx/5xx from APIM)
    
    Circuit breaker:
      - Break after 5 consecutive failures
      - Stay broken for 60 seconds
      - Then attempt half-open test
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=body)
        return response
```

### Error Handling

```python
try:
    response = await self._call_apim(...)
except CircuitBreakerError:
    # APIM is down, return 503
    raise HTTPException(
        status_code=503,
        detail="Backend service unavailable, circuit breaker open"
    )
except httpx.TimeoutError:
    # Request timed out after retries
    raise HTTPException(
        status_code=504,
        detail="Backend service timeout"
    )
except httpx.HTTPError as e:
    # Other network errors
    raise HTTPException(
        status_code=502,
        detail="Backend service error"
    )
```

---

## Operational Deployment

### Infrastructure Requirements

For production deployment connected to client's AWS APIM:

#### Compute
```
Container: Docker image
  - Base: Python 3.13-slim
  - FastAPI + Uvicorn
  - Size: ~200 MB
  - Memory: 512 MB baseline, 1-2 GB recommended
  - CPU: 0.5-1 vCPU minimum

Orchestration: Kubernetes or ECS
  - Multiple replicas (3-5 for HA)
  - Auto-scaling based on CPU/memory
  - Health checks: /health endpoint
  - Readiness checks: DB connectivity
```

#### Database
```
PostgreSQL 13+
  - Tools table (~300 rows)
  - Users and roles
  - Audit logs (1 year)
  - Replicated for HA
  - Backup: Daily, 30-day retention
  - Connection pooling: PgBouncer
```

#### Cache
```
Redis 6.0+
  - Rate limiting counters (1-min TTL)
  - Session cache (24-hour TTL)
  - Exposure cache (1-hour TTL)
  - Idempotency store (24-hour TTL)
  - AOF persistence enabled
  - Replication for HA
```

#### Storage
```
S3 WORM Bucket
  - Audit logs (12-year retention)
  - Server-side encryption (KMS)
  - MFA delete enabled
  - Versioning enabled
  - Object lock enabled
```

### Configuration for Client APIM

Environment variables for deployment:

```bash
# API Gateway Integration
API_GATEWAY_MODE=msil_apim
MSIL_APIM_BASE_URL=https://apim-preprod.client.com
MSIL_APIM_SUBSCRIPTION_KEY=${CLIENT_APIM_KEY}

# Authentication
AUTH_REQUIRED=true
OIDC_ENABLED=true
OIDC_ISSUER=https://auth.client.com
OIDC_JWKS_URL=https://auth.client.com/.well-known/jwks.json
OIDC_AUDIENCE=msil-mcp

# Security
JWT_SECRET=${RANDOM_SECRET_KEY}
API_KEY=${MSIL_API_KEY}

# Database
DATABASE_URL=postgresql://user:pass@db-host:5432/msil_mcp
DATABASE_POOL_SIZE=20

# Cache
REDIS_URL=redis://redis-host:6379
REDIS_ENABLED=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_USER=1000
RATE_LIMIT_PER_TOOL=100

# Audit
AUDIT_DUAL_WRITE=true
S3_BUCKET=msil-audit-prod
S3_REGION=us-east-1

# Logging
LOG_LEVEL=INFO
AUDIT_LOG_LEVEL=DEBUG
```

### Deployment Checklist

- [ ] Database schema created and seeded
- [ ] Redis cluster deployed
- [ ] S3 WORM bucket created with retention policy
- [ ] Container image built and pushed to ECR
- [ ] Kubernetes manifests created
- [ ] OIDC/OAuth integration configured
- [ ] Client APIM subscription key validated
- [ ] TLS certificates installed
- [ ] WAF rules configured
- [ ] Monitoring/alerting setup
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Documentation reviewed with client team
- [ ] Runbooks created for operations
- [ ] Backup/disaster recovery plan ready

---

## Summary & Key Takeaways

### Platform Strengths

1. **Two-Layer Security Model**
   - Separation of visibility (exposure) from execution (authorization)
   - Defense-in-depth architecture
   - Reduces cognitive load for users

2. **Enterprise-Grade Authorization**
   - RBAC with OPA support
   - Risk-based access control
   - Elevation mechanism for sensitive operations
   - Confirmation workflows for destructive actions

3. **Comprehensive Auditability**
   - Immutable audit trail (S3 WORM)
   - PII masking for compliance
   - Full correlation tracing
   - Audit retention: 12 years

4. **Production Resilience**
   - Rate limiting at user and tool level
   - Circuit breakers for fault tolerance
   - Idempotency for exactly-once semantics
   - Exponential backoff for retries
   - Caching for performance

5. **Natural Language Interface**
   - LLM integration (OpenAI GPT-4)
   - Tool orchestration via chat
   - User doesn't need to know API details
   - Reduces training requirements

### Implementation Timeline

For client integration:

```
Phase 1: Setup & Configuration (2 weeks)
  - Infrastructure provisioning (AWS/Kubernetes)
  - Client APIM integration
  - OIDC/OAuth setup
  - Database schema deployment

Phase 2: Customization (2-3 weeks)
  - Tool registry customization
  - Role hierarchy definition
  - Exposure permission design
  - Custom policies via OPA (if used)

Phase 3: Integration Testing (1 week)
  - End-to-end testing with APIM
  - Security testing
  - Load testing
  - UAT with client team

Phase 4: Deployment (1 week)
  - Production deployment
  - Monitoring setup
  - Runbook creation
  - Support handoff

Total: 6-7 weeks to production readiness
```

### Performance Characteristics

```
Typical Latency Breakdown (per tool call):

Authentication:        ~5 ms
  (JWT validation, claims extraction)

Exposure Filter:       ~10 ms
  (Cache hit typical, DB query if miss)

Policy Evaluation:     ~8 ms
  (RBAC check or OPA query)

Rate Limiting:         ~3 ms
  (Redis incr/check)

Idempotency Check:     ~3 ms
  (Redis lookup)

Backend API Call:      ~200-500 ms
  (Network latency to client APIM)

Audit Logging:         ~10 ms
  (Async write to PostgreSQL + S3)

Response Shaping:      ~5 ms
  (JSON parsing/building)

─────────────────────
Total (typical):       ~240-540 ms
  (Dominated by backend API call time)

Without backend call:  ~40-50 ms
  (All security/governance overhead)
```

### Success Metrics for Client

After deployment, monitor:

```
Availability:
  - Target: 99.95% uptime
  - Monitor via /health endpoint
  - Alert on failures

Performance:
  - Target latency p95: <1 second
  - Target latency p99: <2 seconds
  - Monitor degradation trends

Security:
  - Access control denials: Should be rare (<1%)
  - Rate limit activations: Should be minimal
  - Audit trail completeness: 100%
  - Elevation requests: Log and review weekly

Usage:
  - Tool discovery frequency
  - Most-used tools
  - User adoption rate
  - LLM integration usage

Cost:
  - Database query count
  - Redis memory usage
  - S3 storage for audit logs
  - API calls to backend APIM
```

---

## Conclusion

The MSIL MCP Platform provides a sophisticated, production-ready layer between client applications and backend APIs. By separating concerns (exposure vs authorization), enforcing security at multiple checkpoints, and maintaining comprehensive audit trails, it enables:

- **Safe API access**: Users see only what they're authorized for
- **Audit compliance**: Every action is traceable and immutable
- **Natural interfaces**: Chat-based tool discovery reduces friction
- **Enterprise features**: Elevation, confirmation, rate limiting
- **Operational transparency**: Metrics and dashboards for management

When integrated with the client's AWS APIM, it becomes the single point of control for tool discovery, orchestration, and execution across all applications and users.

---

**Document Version**: 1.0  
**Last Updated**: February 8, 2026  
**Status**: Ready for Client Presentation
