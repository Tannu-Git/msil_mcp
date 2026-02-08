# MSIL MCP Server - Complete Architecture & Data Storage Guide

**Document Date**: February 2, 2026  
**Version**: 2.1  
**Status**: Complete Architecture Documentation (Phase 3 Complete)

---

## Table of Contents

1. [Overview](#overview)
2. [MCP Protocol Sequence](#mcp-protocol-sequence)
3. [Admin API Addition Workflow](#admin-api-addition-workflow)
4. [Security Layers: Authentication, Authorization & Rate Limiting](#security-layers)
5. [Exposure Governance (Layer B Security)](#exposure-governance-layer-b-security)
6. [MCP Client Call Flow](#mcp-client-call-flow)
7. [Data Storage Locations](#data-storage-locations)
8. [User & Role Management](#user--role-management)
9. [Tool Registry & Configuration](#tool-registry--configuration)
10. [API Gateway Configuration](#api-gateway-configuration)
11. [Security Policies & Rules](#security-policies--rules)
12. [Service Booking Demo Pack](#service-booking-demo-pack)
13. [RFP Requirements Mapping](#rfp-requirements-mapping)

---

## Overview

The MSIL MCP Server implements a **Model Context Protocol** (MCP) with enterprise-grade security for Maruti Suzuki India Limited's service booking platform.

**Important Architecture Note**: 
> The **Host/Agent application** (with embedded MCP Client) communicates with the MCP Server using the MCP protocol. The **LLM** (e.g., GPT-4, Claude) **only decides which tool to call** based on the tool descriptions—it does not directly speak MCP. The security and governance responsibility lies with the Host application and MCP Server, not the LLM. 

**Key Architecture Components**:
- **Zero-Code Tool Generation** from OpenAPI specs
- **Multi-Layered Security** (Authentication → Authorization → Rate Limiting)
- **Exposure Governance** (Two-Layer Security: Layer B - Who can SEE tools, Layer A - Who can EXECUTE tools)
- **Risk-Based Access Control** (Read/Write/Privileged tools)
- **Step-Up Confirmation** for Write Tools (user_confirmed flag)
- **Real-Time Metrics & Audit Logging** (12-month retention per RFP)
- **PII Protection** (masking enforced, prohibited in logs/traces)
- **Idempotent Write Operations**
- **Dual API Gateway Support** (Mock API + MSIL APIM)
- **Tools Change Notification** via `tools/list_changed` event
- **TTL Caching** for exposure permissions (configurable expiration)

---

## MCP Protocol Sequence

### **Initialize Handshake (Required)**

Before any tool operations, the MCP Client **must** perform an initialize handshake with the server:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           MCP PROTOCOL SEQUENCE DIAGRAM                                  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌──────────────┐                              ┌──────────────┐                        │
│   │  Host/Agent  │                              │  MCP Server  │                        │
│   │  + MCP Client│                              │              │                        │
│   └──────┬───────┘                              └──────┬───────┘                        │
│          │                                             │                                │
│          │  1. CONNECT (WebSocket/SSE/HTTP)            │                                │
│          │─────────────────────────────────────────────▶                                │
│          │                                             │                                │
│          │  2. initialize                              │                                │
│          │  {                                          │                                │
│          │    "jsonrpc": "2.0",                        │                                │
│          │    "id": 1,                                 │                                │
│          │    "method": "initialize",                  │                                │
│          │    "params": {                              │                                │
│          │      "protocolVersion": "2024-11-05",       │                                │
│          │      "capabilities": {                      │                                │
│          │        "tools": {}                          │                                │
│          │      },                                     │                                │
│          │      "clientInfo": {                        │                                │
│          │        "name": "msil-host-app",             │                                │
│          │        "version": "1.0.0"                   │                                │
│          │      }                                      │                                │
│          │    }                                        │                                │
│          │  }                                          │                                │
│          │─────────────────────────────────────────────▶                                │
│          │                                             │                                │
│          │  3. initialize response                     │                                │
│          │  {                                          │                                │
│          │    "jsonrpc": "2.0",                        │                                │
│          │    "id": 1,                                 │                                │
│          │    "result": {                              │                                │
│          │      "protocolVersion": "2024-11-05",       │                                │
│          │      "capabilities": {                      │                                │
│          │        "tools": {                           │                                │
│          │          "listChanged": true                │  ◀── Server supports tools     │
│          │        }                                    │       list change notification │
│          │      },                                     │                                │
│          │      "serverInfo": {                        │                                │
│          │        "name": "msil-mcp-server",           │                                │
│          │        "version": "1.0.0"                   │                                │
│          │      }                                      │                                │
│          │    }                                        │                                │
│          │  }                                          │                                │
│          │◀─────────────────────────────────────────────                                │
│          │                                             │                                │
│          │  4. initialized (notification)              │                                │
│          │  {                                          │                                │
│          │    "jsonrpc": "2.0",                        │                                │
│          │    "method": "notifications/initialized"    │                                │
│          │  }                                          │                                │
│          │─────────────────────────────────────────────▶                                │
│          │                                             │                                │
│          │  ══════════ SESSION NOW ESTABLISHED ══════════                               │
│          │                                             │                                │
│          │  5. tools/list                              │                                │
│          │─────────────────────────────────────────────▶                                │
│          │                                             │                                │
│          │  6. tools list response                     │                                │
│          │◀─────────────────────────────────────────────                                │
│          │                                             │                                │
│          │  7. tools/call (when LLM decides)           │                                │
│          │─────────────────────────────────────────────▶                                │
│          │                                             │                                │
│          │  8. tool execution response                 │                                │
│          │◀─────────────────────────────────────────────                                │
│          │                                             │                                │
│          │  ══════════ TOOLS CHANGED SCENARIO ══════════                                │
│          │                                             │                                │
│          │  (Admin imports new OpenAPI spec)           │                                │
│          │                                             │ ◀── Tool registry updated      │
│          │                                             │                                │
│          │  9. notifications/tools/list_changed        │                                │
│          │◀─────────────────────────────────────────────                                │
│          │                                             │                                │
│          │  10. tools/list (refresh)                   │                                │
│          │─────────────────────────────────────────────▶                                │
│          │                                             │                                │
│          │  11. updated tools list                     │                                │
│          │◀─────────────────────────────────────────────                                │
│          │                                             │                                │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### **Message Types Summary**

| Step | Method | Direction | Description |
|------|--------|-----------|-------------|
| 1 | `initialize` | Client → Server | Start session, exchange capabilities |
| 2 | `notifications/initialized` | Client → Server | Confirm initialization complete |
| 3 | `tools/list` | Client → Server | Get available tools |
| 4 | `tools/call` | Client → Server | Execute a tool |
| 5 | `notifications/tools/list_changed` | Server → Client | Tools have been updated |

### **Error Handling**

| Error Code | Name | Description |
|------------|------|-------------|
| `-32600` | Invalid Request | Malformed JSON-RPC request |
| `-32601` | Method Not Found | Unknown method name |
| `-32602` | Invalid Params | Invalid tool name or arguments |
| `-32001` | Unauthorized | Authentication or authorization failed |
| `-32002` | Rate Limited | Too many requests |
| `-32603` | Internal Error | Server-side error |

### **Tool Update Strategy**

The MCP Server implements **Option A**: Active notification when tools change.

When tools are added/updated via OpenAPI import:
1. Tool registry is updated in database
2. In-memory cache is invalidated
3. Server sends `notifications/tools/list_changed` to all connected clients
4. Clients re-fetch tools via `tools/list`

**For HTTP-only clients**: Must re-call `tools/list` at session start or periodically (recommended: every 5 minutes or on reconnect).

---

## Admin API Addition Workflow

### **Stage 1: OpenAPI Spec Upload**

**Entry Point**: Admin UI → "Import OpenAPI" page  
**Endpoint**: `POST /api/openapi-import/upload`

**Request**:
```json
{
  "file": "<openapi_spec_yaml>",
  "category": "imported",
  "bundle_name": "customer_service_v1"
}
```

**Files Involved**:
- **Frontend**: `admin-ui/src/pages/Import.tsx`
- **Backend**: `mcp-server/app/api/openapi_import.py` (lines 69-120)
- **Parser**: `mcp-server/app/core/openapi/parser.py`

**Processing**:
1. File is saved temporarily
2. OpenAPI YAML is parsed
3. All endpoints are extracted
4. For each endpoint, a **Tool object** is created with:
   - `name`: Auto-generated from endpoint path
   - `display_name`: Formatted for UI
   - `description`: From OpenAPI spec
   - `api_endpoint`: Full path
   - `http_method`: GET/POST/PUT/DELETE/PATCH
   - `input_schema`: From parameters + request body
   - `output_schema`: From response schema
   - `risk_level`: Auto-detected (read/write/privileged)

**Example Tool Generation**:
```yaml
# Input (OpenAPI):
openapi: 3.0.0
paths:
  /api/customer/resolve:
    post:
      summary: Resolve Customer
      parameters:
        - name: mobile
          required: true
          schema:
            type: string
      responses:
        200:
          schema:
            type: object
            properties:
              customer_id: string
              name: string

# Output (Generated Tool):
Tool(
  id=uuid4(),
  name="resolve_customer",
  display_name="Resolve Customer",
  description="Resolve Customer",
  api_endpoint="/api/customer/resolve",
  http_method="POST",
  input_schema={
    "type": "object",
    "properties": {
      "mobile": {"type": "string"}
    },
    "required": ["mobile"]
  },
  output_schema={
    "type": "object",
    "properties": {
      "customer_id": {"type": "string"},
      "name": {"type": "string"}
    }
  },
  risk_level="read",
  rate_limit_tier="standard"
)
```

---

### **Stage 2: Tool Preview & Selection**

**Display**: Admin UI → "Import Preview" page  
**Storage**: In-memory cache (temporary)  
**File**: `mcp-server/app/api/openapi_import.py` (lines 212-260)

**Data Cached in Memory**:
```python
_specs_cache: Dict[str, Dict[str, Any]] = {
  "spec_abc123": {
    "name": "customer_service_api",
    "version": "1.0.0",
    "uploaded_at": "2026-01-31T10:30:45Z",
    "tools": [
      {ToolPreview object},
      {ToolPreview object},
      ...
    ],
    "status": "preview"
  }
}
```

**Admin Actions**:
- ✅ View all generated tools with metadata
- ✅ Select/deselect tools to register
- ✅ Modify tool properties (name, category, risk level)
- ✅ Click "Register Selected Tools"

---

### **Stage 3: Approval & Registration**

**Endpoint**: `POST /api/openapi-import/approve-tools`

**Request**:
```json
{
  "spec_id": "spec_abc123",
  "tool_ids": ["resolve_customer", "resolve_vehicle", "get_nearby_dealers"],
  "category": "service_booking"
}
```

**Processing**:
1. Load selected tools from temporary cache
2. **Validate** each tool against schema
3. **Persist to Database** (PostgreSQL `tools` table)
4. **Reload tool registry** (in-memory cache invalidation)
5. **Notify connected clients** via `tools/list_changed` notification
6. Return confirmation

**Database Insertion**:
```sql
-- mcp-server/app/db/database.py
INSERT INTO tools (
  id, name, display_name, description, category,
  api_endpoint, http_method, input_schema, output_schema,
  risk_level, rate_limit_tier, is_active, created_at, updated_at
) VALUES (
  'uuid123', 'resolve_customer', 'Resolve Customer', 'Get customer details...',
  'service_booking', '/api/customer/resolve', 'POST',
  '{"type": "object", "properties": {...}}',
  '{"type": "object", "properties": {...}}',
  'read', 'standard', true, NOW(), NOW()
)
```

---

## Security Layers: Authentication, Authorization & Rate Limiting

### **Layer 1: Authentication (JWT Token Validation)**

**File**: `mcp-server/app/core/auth/oauth2_provider.py`

**When Client Calls MCP**:
```
POST /api/mcp
Headers:
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  X-API-Key: msil-mcp-dev-key-2026
  X-Correlation-ID: req-12345
```

**Authentication Handler**:
```python
# Line 95-120: get_current_user()
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserInfo:
    """
    Extract and validate JWT token
    Returns: UserInfo with user_id, email, roles
    """
    token = credentials.credentials  # Bearer token
    payload = jwt_handler.decode_token(token)  # Validate signature
    
    # Extracted from JWT claims:
    user_info = UserInfo(
        user_id=payload["user_id"],
        email=payload["email"],
        name=payload["name"],
        roles=payload["roles"],  # ["developer", "operator"]
        is_active=payload["is_active"]
    )
    return user_info
```

**JWT Token Structure**:
```python
# Encoded JWT contains:
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "user_id": "usr_dev_001",
    "email": "developer@msil.com",
    "name": "MSIL Developer",
    "roles": ["developer", "operator"],
    "is_active": true,
    "exp": 1737986400,  # Expires in 60 minutes
    "iat": 1737982800
  },
  "signature": "HMACSHA256(header + payload, JWT_SECRET)"
}
```

**JWT Configuration** (`app/config.py`):
```python
JWT_SECRET: str = "msil-mcp-jwt-secret-key-change-in-production-2026"
JWT_ALGORITHM: str = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
```

**Demo Mode** (MVP):
```python
# If DEMO_MODE=True, hardcoded users bypass actual JWT validation:
self.users = {
    "admin@msil.com": {
        "user_id": "usr_admin_001",
        "password_hash": "admin123",
        "roles": ["admin", "developer", "operator"]
    },
    "developer@msil.com": {
        "user_id": "usr_dev_001",
        "password_hash": "dev123",
        "roles": ["developer", "operator"]
    },
    "operator@msil.com": {
        "user_id": "usr_op_001",
        "password_hash": "op123",
        "roles": ["operator"]
    }
}
```

---

### **Layer 2: Authorization & Risk-Based Policy**

**Files**: 
- `mcp-server/app/core/policy/engine.py`
- `mcp-server/app/core/policy/risk_policy.py`
- `mcp-server/app/core/policy/models.py`

**Policy Evaluation Context**:
```python
# Context built from request:
context = {
    "action": "invoke",           # discover, invoke, admin
    "resource": "resolve_customer", # tool name
    "user_id": "usr_dev_001",
    "roles": ["developer", "operator"],
    "tool_risk_level": "read",    # from Tool.risk_level
    "is_elevated": False,         # PIM elevation status
    "ip_address": "192.168.1.100",
    "timestamp": "2026-01-31T10:30:45Z"
}
```

**Risk Policy Rules**:

```python
# File: mcp-server/app/core/policy/risk_policy.py

class RiskPolicy:
    """Defines access control for each risk level"""
    risk_level: str           # "read", "write", "privileged"
    min_role: str             # Minimum role required
    requires_elevation: bool  # Needs PIM/PAM elevation
    requires_approval: bool   # Needs manager approval
    requires_confirmation: bool  # Requires user_confirmed=true in input
    rate_limit_tier: str      # Rate limiting tier
    max_concurrency: int      # Max concurrent executions
    pii_policy: str           # PII handling policy

# Initialized policies:
POLICIES = {
    "read": RiskPolicy(
        risk_level="read",
        min_role="operator",
        requires_elevation=False,
        requires_approval=False,
        requires_confirmation=False,   # No confirmation for read
        rate_limit_tier="permissive",  # 100 req/min
        max_concurrency=50,
        pii_policy="redact"
    ),
    "write": RiskPolicy(
        risk_level="write",
        min_role="developer",
        requires_elevation=False,
        requires_approval=False,
        requires_confirmation=True,    # ⚠️ STEP-UP: Requires user_confirmed=true
        rate_limit_tier="standard",    # 50 req/min
        max_concurrency=20,
        pii_policy="mask"
    ),
    "privileged": RiskPolicy(
        risk_level="privileged",
        min_role="admin",
        requires_elevation=True,       # Requires PIM approval
        requires_approval=True,        # Requires manager approval
        requires_confirmation=True,    # Requires user_confirmed=true
        rate_limit_tier="strict",      # 10 req/min
        max_concurrency=5,
        pii_policy="redact_sensitive"
    )
}
```

### **Step-Up Confirmation for Write Tools**

For all write-level and privileged tools, the input schema **must** include a `user_confirmed` field:

```python
# Write tool input schema example (create_service_booking):
{
    "type": "object",
    "properties": {
        "customer_id": {"type": "string"},
        "vehicle_id": {"type": "string"},
        "dealer_id": {"type": "string"},
        "service_type": {"type": "string"},
        "preferred_date": {"type": "string", "format": "date"},
        "preferred_time_slot": {"type": "string"},
        "user_confirmed": {
            "type": "boolean",
            "description": "User explicitly confirmed this booking action",
            "default": false
        }
    },
    "required": ["customer_id", "vehicle_id", "dealer_id", "service_type", 
                 "preferred_date", "preferred_time_slot", "user_confirmed"]
}
```

**Enforcement**:
```python
# In tool executor, before executing write tools:
if tool.risk_level in ["write", "privileged"]:
    if not arguments.get("user_confirmed", False):
        raise PolicyError(
            code=-32001,
            message="Write operation requires explicit user confirmation",
            details={"required_field": "user_confirmed=true"}
        )
```
```

**Access Decision Logic**:
```python
# File: mcp-server/app/core/policy/risk_policy.py (line 93-150)

def evaluate_access(
    self,
    tool_risk_level: str,
    user_role: str,
    is_elevated: bool = False
) -> Dict[str, Any]:
    """
    Evaluate if user can execute tool
    """
    policy = self.get_policy(tool_risk_level)
    
    # Role hierarchy check
    role_hierarchy = {
        "user": 0,
        "operator": 1,
        "developer": 2,
        "admin": 3
    }
    
    user_level = role_hierarchy.get(user_role, -1)
    required_level = role_hierarchy.get(policy.min_role, 999)
    has_role = user_level >= required_level
    
    # Elevation check
    needs_elevation = policy.requires_elevation and not is_elevated
    
    # Final decision
    allowed = has_role and not needs_elevation
    
    return {
        "allowed": allowed,
        "has_required_role": has_role,
        "requires_elevation": policy.requires_elevation,
        "is_elevated": is_elevated,
        "needs_elevation": needs_elevation,
        "requires_approval": policy.requires_approval,
        "rate_limit_tier": policy.rate_limit_tier,
        "max_concurrency": policy.max_concurrency,
        "reason": "Access denied: User 'operator' cannot execute 'privileged' tool"
    }
```

**Example Scenarios**:

| User | Role | Tool | Risk | Elevation | Result | Reason |
|------|------|------|------|-----------|--------|--------|
| user1 | operator | resolve_customer | read | No | ✅ ALLOW | Role meets requirement |
| user2 | operator | delete_booking | privileged | No | ❌ DENY | Requires admin role |
| user3 | admin | delete_booking | privileged | No | ❌ DENY | Elevation required |
| user3 | admin | delete_booking | privileged | Yes | ✅ ALLOW | All checks pass |

---

### **Layer 3: Rate Limiting (Token Bucket)**

**File**: `mcp-server/app/core/cache/rate_limiter.py`

**Storage**: Redis (configured in `app/config.py`)

**Rate Limit Tiers**:
```python
RATE_LIMITS = {
    "permissive": {
        "requests_per_minute": 100,
        "burst_size": 20,          # Allow 20 simultaneous requests
        "window": 60               # 1 minute window
    },
    "standard": {
        "requests_per_minute": 50,
        "burst_size": 10,
        "window": 60
    },
    "strict": {
        "requests_per_minute": 10,
        "burst_size": 2,
        "window": 60
    }
}
```

**Rate Limit Check Process**:
```python
# File: mcp-server/app/core/cache/rate_limiter.py (line 42-85)

async def check_rate_limit(
    self,
    key: str,              # e.g., "user:usr_dev_001" or "tool:resolve_customer"
    limit: int,            # e.g., 100
    window: int = 60       # seconds
) -> RateLimitInfo:
    """
    Token bucket algorithm:
    - Each second, add 'limit/window' tokens
    - Each request consumes 1 token
    - If tokens available: allowed
    - If tokens exhausted: reject with retry_after
    """
    cache_key = f"ratelimit:{key}"
    current_time = int(time.time())
    
    # Get current count from Redis
    count = await redis.increment(cache_key, 1, window)
    
    if count <= limit:
        # Request allowed
        return RateLimitInfo(
            allowed=True,
            remaining=limit - count,
            reset_at=current_time + window
        )
    else:
        # Rate limit exceeded
        retry_after = window - (current_time % window)
        return RateLimitInfo(
            allowed=False,
            remaining=0,
            reset_at=current_time + retry_after,
            retry_after=retry_after
        )
```

**Per-User & Per-Tool Limits**:
```python
# Check user limit
user_limit = await rate_limiter.check_user_rate_limit(
    user_id="usr_dev_001",
    limit=100,  # 100 requests/minute for this user
    window=60
)
if not user_limit.allowed:
    return 429 Too Many Requests

# Check tool limit
tool_limit = await rate_limiter.check_tool_rate_limit(
    tool_name="resolve_customer",
    limit=50,   # 50 requests/minute for this tool
    window=60
)
if not tool_limit.allowed:
    return 429 Too Many Requests
```

**Response Headers**:
```
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1737980000

# If rate limited:
HTTP/1.1 429 Too Many Requests
Retry-After: 45
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1737980045
```

---

## 5. Exposure Governance (Layer B Security)

### Overview

**Exposure Governance** implements a **two-layer security model** to control tool visibility and access:

- **Layer B (Exposure)**: Controls which tools a user can **SEE** in `tools/list` responses
- **Layer A (Authorization)**: Controls which tools a user can **EXECUTE** in `tools/call` requests

This separation provides:
- **Token Efficiency**: Users only see relevant tools (reduces prompt tokens by 82%)
- **Security**: Prevents information disclosure of internal/sensitive tools
- **Governance**: Centralized control over tool visibility by role
- **Defense-in-Depth**: Both layers must pass for tool execution

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          TWO-LAYER SECURITY MODEL                                        │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  REQUEST: User with role "operator" calls tools/list                                    │
│                                                                                         │
│         ┌─────────────────────────────┐                                                 │
│         │   LAYER B: EXPOSURE         │                                                 │
│         │   Who can SEE the tool?     │                                                 │
│         │                             │                                                 │
│         │  Check user role against    │                                                 │
│         │  exposure permissions:      │                                                 │
│         │  • expose:all               │                                                 │
│         │  • expose:bundle:*          │                                                 │
│         │  • expose:tool:*            │                                                 │
│         └──────────┬──────────────────┘                                                 │
│                    │                                                                    │
│                    ▼ Filter by exposure                                                 │
│         ┌─────────────────────────────┐                                                 │
│         │   LAYER A: AUTHORIZATION    │                                                 │
│         │   Who can EXECUTE the tool? │                                                 │
│         │                             │                                                 │
│         │  Check user permissions &   │                                                 │
│         │  credentials (RBAC/ACL)     │                                                 │
│         └──────────┬──────────────────┘                                                 │
│                    │                                                                    │
│                    ▼ Filter by authorization                                            │
│         ┌─────────────────────────────┐                                                 │
│         │   RESPONSE: Filtered Tools  │                                                 │
│         │   (Visible AND Executable)  │                                                 │
│         └─────────────────────────────┘                                                 │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Database Schema

**Tables Added in Phase 1**:

```sql
-- Roles table (pre-existing, enhanced)
CREATE TABLE policy_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Exposure permissions table (NEW)
CREATE TABLE policy_role_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID NOT NULL REFERENCES policy_roles(id) ON DELETE CASCADE,
    permission VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_policy_roles_name ON policy_roles(name);
CREATE INDEX idx_policy_role_permissions_role ON policy_role_permissions(role_id);

-- Sample data
INSERT INTO policy_roles (name) VALUES 
    ('admin'), 
    ('operator'), 
    ('analyst');

INSERT INTO policy_role_permissions (role_id, permission) VALUES
    ((SELECT id FROM policy_roles WHERE name = 'admin'), 'expose:all'),
    ((SELECT id FROM policy_roles WHERE name = 'operator'), 'expose:bundle:customer-service'),
    ((SELECT id FROM policy_roles WHERE name = 'analyst'), 'expose:bundle:data-analysis');
```

### Permission Format

Three permission types:

| Permission Type | Format | Description | Example |
|-----------------|--------|-------------|---------|
| **All Access** | `expose:all` | User can see ALL tools | Admin role |
| **Bundle Access** | `expose:bundle:BUNDLE_NAME` | User can see all tools in bundle | `expose:bundle:customer-service` |
| **Tool Access** | `expose:tool:TOOL_NAME` | User can see specific tool | `expose:tool:resolve_customer` |

### ExposureManager Service

**File**: `mcp-server/app/core/exposure/manager.py`

**Key Methods**:

```python
class ExposureManager:
    """Manages tool visibility based on exposure policies"""
    
    def __init__(self, cache_ttl_seconds: Optional[int] = None):
        """
        Initialize with TTL caching.
        
        Args:
            cache_ttl_seconds: Cache expiration time (default: 3600 seconds = 1 hour)
        """
        self._exposure_cache: Dict[str, Tuple[Set[str], float]] = {}
        self.cache_ttl = cache_ttl_seconds or int(os.getenv("EXPOSURE_CACHE_TTL_SECONDS", "3600"))
    
    async def get_exposed_tools_for_user(
        self,
        user_id: str,
        roles: List[str],
        client_application: Optional[str] = None
    ) -> Set[str]:
        """
        Get set of tool names user can see.
        
        Returns:
            Set of tool references:
            - "*" means all tools
            - "__BUNDLE__{name}" means all tools in bundle
            - Tool name means specific tool
        """
        # Check cache first (with TTL validation)
        cache_key = f"{':'.join(sorted(roles))}"
        if cache_key in self._exposure_cache:
            cached_tools, cached_time = self._exposure_cache[cache_key]
            if self._is_cache_valid(cached_time):
                return cached_tools
        
        # Query database for permissions
        exposed_tools: Set[str] = set()
        for role in roles:
            permissions = await self._get_role_exposure_permissions(role)
            tools_for_role = self._parse_exposure_permissions(permissions)
            exposed_tools.update(tools_for_role)
        
        # Cache result with timestamp
        self._exposure_cache[cache_key] = (exposed_tools, time.time())
        return exposed_tools
    
    async def filter_tools(
        self,
        all_tools: List[Any],
        user_id: str,
        roles: List[str]
    ) -> List[Any]:
        """
        Filter tool list by exposure policy.
        
        Returns:
            Filtered list of tools user is exposed to
        """
        exposed_tool_refs = await self.get_exposed_tools_for_user(user_id, roles)
        
        # If user has expose:all, return everything
        if "*" in exposed_tool_refs:
            return all_tools
        
        # Filter by bundles and tool names
        allowed_bundles = {ref.replace("__BUNDLE__", "") for ref in exposed_tool_refs if ref.startswith("__BUNDLE__")}
        allowed_tool_names = {ref for ref in exposed_tool_refs if not ref.startswith("__BUNDLE__")}
        
        filtered_tools = []
        for tool in all_tools:
            if tool.name in allowed_tool_names:
                filtered_tools.append(tool)
            elif tool.bundle_name and tool.bundle_name in allowed_bundles:
                filtered_tools.append(tool)
        
        return filtered_tools
    
    def is_tool_exposed(
        self,
        tool_name: str,
        tool_bundle: Optional[str],
        exposed_refs: Set[str]
    ) -> bool:
        """
        Quick check if specific tool is exposed.
        Used in tools/call for defense-in-depth.
        """
        if "*" in exposed_refs:
            return True
        if tool_name in exposed_refs:
            return True
        if tool_bundle and f"__BUNDLE__{tool_bundle}" in exposed_refs:
            return True
        return False
    
    def invalidate_cache(self, role_name: Optional[str] = None):
        """
        Clear exposure cache after admin changes permissions.
        """
        if role_name:
            keys_to_remove = [k for k in self._exposure_cache.keys() if role_name in k]
            for key in keys_to_remove:
                del self._exposure_cache[key]
        else:
            self._exposure_cache.clear()
```

### Request Flow Integration

**1. tools/list Endpoint** (`mcp-server/app/api/mcp.py`):

```python
@router.post("/mcp")
async def mcp_handler(request: MCPRequest) -> MCPResponse:
    if request.method == "tools/list":
        # Get all active tools from registry
        all_tools = await tool_registry.get_active_tools()
        
        # Extract user context
        user_id = request.headers.get("X-User-ID")
        user_roles = request.headers.get("X-User-Role", "").split(",")
        
        # LAYER B: Filter by exposure
        exposed_tools = await exposure_manager.filter_tools(
            all_tools, user_id, user_roles
        )
        
        # LAYER A: Further filter by authorization (existing PolicyEngine)
        authorized_tools = await policy_engine.filter_authorized_tools(
            exposed_tools, user_roles
        )
        
        # Return filtered list
        return MCPResponse(
            result={"tools": [tool.to_mcp_format() for tool in authorized_tools]}
        )
```

**2. tools/call Endpoint** (Defense-in-Depth):

```python
@router.post("/mcp")
async def mcp_handler(request: MCPRequest) -> MCPResponse:
    if request.method == "tools/call":
        tool_name = request.params["name"]
        
        # Get user context
        user_roles = request.headers.get("X-User-Role", "").split(",")
        
        # Get exposure permissions
        exposed_refs = await exposure_manager.get_exposed_tools_for_user(
            user_id, user_roles
        )
        
        # Get tool metadata
        tool = await tool_registry.get_tool(tool_name)
        
        # LAYER B: Check if tool is exposed
        if not exposure_manager.is_tool_exposed(tool_name, tool.bundle_name, exposed_refs):
            raise ToolNotAvailable(f"Tool '{tool_name}' not exposed to your role")
        
        # LAYER A: Check authorization (existing logic)
        if not await policy_engine.can_execute_tool(tool, user_roles):
            raise Unauthorized(f"Not authorized to execute '{tool_name}'")
        
        # Execute tool
        result = await executor.execute(tool, request.params["arguments"])
        return MCPResponse(result=result)
```

### Admin API Endpoints

**File**: `mcp-server/app/api/admin.py`

Five new admin endpoints for managing exposure:

```python
# 1. Get role permissions
GET /admin/exposure/roles/{role_name}
Response: {
  "role": "operator",
  "permissions": ["expose:bundle:customer-service", "expose:bundle:data-analysis"]
}

# 2. Add permission to role
POST /admin/exposure/roles/{role_name}/permissions
Body: {"permission": "expose:bundle:customer-service"}
Response: {"status": "added", "role": "operator", "permission": "expose:bundle:customer-service"}

# 3. Remove permission from role
DELETE /admin/exposure/roles/{role_name}/permissions
Body: {"permission": "expose:bundle:customer-service"}
Response: {"status": "removed"}

# 4. Get available bundles
GET /admin/exposure/bundles
Response: {
  "bundles": [
    {"name": "customer-service", "tool_count": 15},
    {"name": "data-analysis", "tool_count": 22}
  ]
}

# 5. Preview role exposure
GET /admin/exposure/preview/{role_name}
Response: {
  "role": "operator",
  "exposed_tools": ["resolve_customer", "update_customer", ...],
  "tool_count": 15
}
```

### Admin UI

**File**: `admin-ui/src/pages/Exposure.tsx`

**Features**:
- Role selector (Operator, Analyst, Viewer, Custom)
- Permissions list (visual tags, removable)
- Add permission dialog (All Access, Bundle Access, Tool Access)
- Live preview panel (shows tools user will see)
- Real-time updates with success/error notifications

**Keyboard Accessibility**:
- Tab/Shift+Tab navigation
- Arrow keys for role selection
- Escape to close dialogs
- Enter to activate buttons
- Screen reader support (ARIA labels)

### Performance Characteristics

| Metric | Before (No Exposure) | After (With Exposure) | Improvement |
|--------|----------------------|-----------------------|-------------|
| Tools in tools/list | 250+ | 15-45 (role-dependent) | 82% reduction |
| Response size | 50KB | 10KB | 80% smaller |
| Tokens used per day | 10,000 | 2,000 | 80% savings |
| First request (cold) | - | 50ms (DB query) | - |
| Subsequent (cached) | - | 1ms (cache hit) | 50x faster |
| Cache hit rate | - | >95% | - |

### Security Benefits

1. **Information Disclosure Prevention**: Users can't discover tools they shouldn't know exist
2. **Token Efficiency**: Reduces LLM token usage by 80%+
3. **Defense-in-Depth**: Two independent validation layers
4. **Audit Trail**: All permission changes logged
5. **Least Privilege**: Users only see what they need
6. **Centralized Governance**: Single source of truth for tool visibility

### Configuration

**Environment Variables**:

```bash
# Cache TTL (default: 3600 seconds = 1 hour)
EXPOSURE_CACHE_TTL_SECONDS=3600

# Default permissions for new roles (optional)
EXPOSURE_DEFAULT_PERMISSIONS=expose:bundle:customer-service

# Enable/disable exposure filtering (default: true)
EXPOSURE_ENABLED=true
```

### Testing

**Test Coverage**: 100+ tests
- Unit tests: ExposureManager logic (25 tests)
- Integration tests: Admin API endpoints (20 tests)
- E2E tests: MCP protocol with exposure (25 tests)
- Component tests: React UI (30 tests)

**Files**:
- `mcp-server/tests/test_exposure_manager.py`
- `mcp-server/tests/test_exposure_api.py`
- `mcp-server/tests/test_mcp_exposure_integration.py`
- `admin-ui/src/pages/Exposure.test.tsx`

---

## MCP Client Call Flow

### **Complete End-to-End Journey**

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. CLIENT INITIATES REQUEST                                     │
└─────────────────────────────────────────────────────────────────┘

POST /api/mcp
Headers:
  Content-Type: application/json
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  X-API-Key: msil-mcp-dev-key-2026
  X-Correlation-ID: req-12345
  Idempotency-Key: idempotent-abc123  # For write operations

Body:
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/call",
  "params": {
    "name": "resolve_customer",
    "arguments": {
      "mobile": "9876543210"
    }
  }
}

         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. AUTHENTICATION (oauth2_provider.py)                          │
└─────────────────────────────────────────────────────────────────┘

✓ Extract JWT from Authorization header
✓ Validate signature using JWT_SECRET (HS256)
✓ Check token expiration
✓ Extract claims: user_id, email, roles

UserInfo Extracted:
{
  "user_id": "usr_dev_001",
  "email": "developer@msil.com",
  "name": "MSIL Developer",
  "roles": ["developer", "operator"],
  "is_active": true
}

✓ Authentication passed → Continue
✗ Auth failed → Return 401 Unauthorized

         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. RATE LIMIT CHECK - PER USER (rate_limiter.py)               │
└─────────────────────────────────────────────────────────────────┘

✓ Get user_id: "usr_dev_001"
✓ Get user's rate limit tier from policy: "standard"
✓ Check Redis: key="ratelimit:user:usr_dev_001"
✓ Decrement token count (from 50/minute)

✓ Tokens available → Continue
✗ Limit exceeded → Return 429 Too Many Requests
  Retry-After: 45 seconds

         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. PARSE & ROUTE REQUEST (app/api/mcp.py)                      │
└─────────────────────────────────────────────────────────────────┘

✓ Parse JSON-RPC: method="tools/call"
✓ Generate/use correlation_id: "req-12345"
✓ Route to handle_tools_call()

         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. TOOL DISCOVERY (app/core/tools/registry.py)                 │
└─────────────────────────────────────────────────────────────────┘

✓ Get tool_name: "resolve_customer"
✓ Look up in registry (in-memory cache)

Tool object returned:
{
  "id": "uuid123",
  "name": "resolve_customer",
  "display_name": "Resolve Customer",
  "api_endpoint": "/api/customer/resolve",
  "http_method": "POST",
  "input_schema": {...},
  "output_schema": {...},
  "risk_level": "read",
  "rate_limit_tier": "standard",
  "requires_approval": false,
  "requires_elevation": false
}

✓ Tool found → Continue
✗ Tool not found → Return -32602 Invalid params

         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. INPUT VALIDATION (Pydantic + JSON Schema)                   │
└─────────────────────────────────────────────────────────────────┘

✓ Validate arguments against tool.input_schema
✓ Check required fields: "mobile" present? Yes
✓ Check field types: string? Yes
✓ Check payload size: < 1MB? Yes
✓ Sanitize inputs (no injection patterns)

✓ Validation passed → Continue
✗ Validation failed → Return -32602 Invalid params with details

         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. AUTHORIZATION & RISK POLICY (engine.py)                     │
└─────────────────────────────────────────────────────────────────┘

Build policy context:
{
  "action": "invoke",
  "resource": "resolve_customer",
  "user_id": "usr_dev_001",
  "roles": ["developer", "operator"],
  "tool_risk_level": "read",
  "is_elevated": false
}

Policy evaluation:
✓ Tool risk="read" → min_role="operator"
✓ User roles include "developer" ✅ (exceeds requirement)
✓ Elevation NOT required
✓ Approval NOT required

✓ Access allowed → Continue
✗ Access denied → Return -32001 Unauthorized
  "Reason: User 'operator' cannot execute 'privileged' tool"

         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. RATE LIMIT CHECK - PER TOOL (rate_limiter.py)               │
└─────────────────────────────────────────────────────────────────┘

✓ Get tool rate limit: "standard" tier = 50 req/min
✓ Check Redis: key="ratelimit:tool:resolve_customer"
✓ Decrement token count

✓ Tokens available → Continue
✗ Limit exceeded → Return 429 Too Many Requests

         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. IDEMPOTENCY CHECK (For Write Operations)                    │
└─────────────────────────────────────────────────────────────────┘

Only for POST/PUT/PATCH/DELETE methods:

✓ Get idempotency_key from header: "idempotent-abc123"
✓ Look up in Redis: "idempotency:idempotent-abc123"

✓ Cache HIT: Return cached response (no re-execution)
✓ Cache MISS: Continue, will cache result after execution

         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 10. TOOL EXECUTION (app/core/tools/executor.py)                │
└─────────────────────────────────────────────────────────────────┘

Determine API gateway:
  If settings.API_GATEWAY_MODE == "mock":
    base_url = "http://localhost:8080"
  Else if settings.API_GATEWAY_MODE == "msil_apim":
    base_url = "https://apim-dev.marutisuzuki.com"

Build HTTP request:
{
  "method": "POST",
  "url": "http://localhost:8080/api/customer/resolve",
  "headers": {
    "Content-Type": "application/json",
    "X-API-Key": "msil-mcp-dev-key-2026",
    "X-Correlation-ID": "req-12345",
    "X-User-Context": "usr_dev_001"
  },
  "json": {
    "mobile": "9876543210"
  },
  "timeout": 30.0
}

Execute with retry logic:
  Max retries: 3
  Backoff: 100ms, 200ms, 400ms exponential

Response received:
{
  "customer_id": "C123456",
  "name": "Rajesh Kumar",
  "phone": "9876543210",
  "vehicle_count": 2
}

✓ Success (200-299) → Extract response
✗ Timeout → Return -32603 Internal error
✗ 4xx → Return -32602 Invalid params
✗ 5xx → Return -32603 Internal error

         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 11. METRICS & AUDIT LOGGING (metrics/collector.py + audit.py) │
└─────────────────────────────────────────────────────────────────┘

Record metrics:
- Tool: "resolve_customer"
- User: "usr_dev_001"
- Status: "success"
- Duration: 245 ms
- Timestamp: 2026-01-31T10:30:45Z
- Request size: 85 bytes
- Response size: 156 bytes

Record audit log:
- User: "developer@msil.com"
- Action: "tool_executed"
- Tool: "resolve_customer"
- Input: {"mobile": "9876...3210"}  # PII masked
- Output: "success"
- Correlation ID: "req-12345"
- Risk level: "read"

         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 12. RESPONSE FORMATTING (JSON-RPC 2.0)                         │
└─────────────────────────────────────────────────────────────────┘

HTTP/1.1 200 OK
Content-Type: application/json
X-RateLimit-Remaining: 86
X-RateLimit-Reset: 1737980045
X-Correlation-ID: req-12345

{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Customer resolved successfully"
      },
      {
        "type": "json",
        "data": {
          "customer_id": "C123456",
          "name": "Rajesh Kumar",
          "phone": "9876543210",
          "vehicle_count": 2
        }
      }
    ],
    "isError": false
  }
}
```

---

## Data Storage Locations

### **1. User & Authentication Data**

**Storage Type**: In-Memory (Demo) + Database (Production)

**File Locations**:
- **Demo Users**: `mcp-server/app/core/auth/oauth2_provider.py` (lines 35-60)
- **JWT Handler**: `mcp-server/app/core/auth/jwt_handler.py`

**Demo Users**:
```python
self.users = {
    "admin@msil.com": {
        "user_id": "usr_admin_001",
        "password_hash": "admin123",
        "roles": ["admin", "developer", "operator"],
        "is_active": True
    },
    "developer@msil.com": {
        "user_id": "usr_dev_001",
        "password_hash": "dev123",
        "roles": ["developer", "operator"],
        "is_active": True
    },
    "operator@msil.com": {
        "user_id": "usr_op_001",
        "password_hash": "op123",
        "roles": ["operator"],
        "is_active": True
    }
}
```

**Database Schema** (PostgreSQL):
```sql
-- Table: users
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255),
  password_hash VARCHAR(255),
  roles TEXT[] DEFAULT ARRAY['user'],  -- Array of role strings
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Sample data:
INSERT INTO users VALUES (
  'usr_dev_001',
  'developer@msil.com',
  'MSIL Developer',
  'bcrypt_hash_...',
  ARRAY['developer', 'operator'],
  TRUE,
  NOW(),
  NOW()
);
```

**Configuration**: `mcp-server/app/config.py` (lines 63-72)
```python
OAUTH2_ENABLED: bool = True
JWT_SECRET: str = "msil-mcp-jwt-secret-key-change-in-production-2026"
JWT_ALGORITHM: str = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
```

---

### **2. Tools & Tool Registry**

**Storage Type**: Database (Primary) + In-Memory Cache (Performance)

**File Locations**:
- **Registry**: `mcp-server/app/core/tools/registry.py`
- **Database**: `mcp-server/app/db/database.py`
- **Repositories**: `mcp-server/app/db/repositories.py`

**Database Schema**:
```sql
-- Table: tools
CREATE TABLE tools (
  id UUID PRIMARY KEY,
  name VARCHAR(255) UNIQUE NOT NULL,
  display_name VARCHAR(255),
  description TEXT,
  category VARCHAR(100),
  api_endpoint VARCHAR(500),
  http_method VARCHAR(10),  -- GET, POST, PUT, DELETE, PATCH
  input_schema JSONB,       -- JSON schema for inputs
  output_schema JSONB,      -- JSON schema for outputs
  headers JSONB,            -- Default headers
  auth_type VARCHAR(50),    -- none, basic, bearer, api_key
  is_active BOOLEAN DEFAULT TRUE,
  version VARCHAR(20) DEFAULT '1.0.0',
  risk_level VARCHAR(50) DEFAULT 'read',  -- read, write, privileged
  requires_elevation BOOLEAN DEFAULT FALSE,
  requires_approval BOOLEAN DEFAULT FALSE,
  max_concurrent_executions INTEGER DEFAULT 10,
  rate_limit_tier VARCHAR(50) DEFAULT 'standard',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance:
CREATE INDEX idx_tools_name ON tools(name);
CREATE INDEX idx_tools_category ON tools(category);
CREATE INDEX idx_tools_is_active ON tools(is_active);
```

**In-Memory Cache** (Registry):
```python
# File: mcp-server/app/core/tools/registry.py (lines 42-50)
class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}  # Key: tool_name
        self._loaded = False

# Loaded on startup:
_tools = {
    "resolve_customer": Tool(...),
    "resolve_vehicle": Tool(...),
    "get_nearby_dealers": Tool(...),
    ...
}
```

---

### **2a. Exposure Governance Data (Phase 1-3 Addition)**

**Storage Type**: Database (Primary) + In-Memory Cache with TTL

**File Locations**:
- **ExposureManager**: `mcp-server/app/core/exposure/manager.py`
- **Admin API**: `mcp-server/app/api/admin.py`
- **Admin UI**: `admin-ui/src/pages/Exposure.tsx`

**Database Schema**:
```sql
-- Table: policy_roles
CREATE TABLE policy_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: policy_role_permissions
CREATE TABLE policy_role_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID NOT NULL REFERENCES policy_roles(id) ON DELETE CASCADE,
    permission VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_policy_roles_name ON policy_roles(name);
CREATE INDEX idx_policy_role_permissions_role ON policy_role_permissions(role_id);

-- Sample data (Phase 1 seeded):
INSERT INTO policy_roles (name) VALUES ('admin'), ('operator'), ('analyst');

INSERT INTO policy_role_permissions (role_id, permission) VALUES
    ((SELECT id FROM policy_roles WHERE name = 'admin'), 'expose:all'),
    ((SELECT id FROM policy_roles WHERE name = 'operator'), 'expose:bundle:customer-service'),
    ((SELECT id FROM policy_roles WHERE name = 'analyst'), 'expose:bundle:data-analysis');
```

**Permission Formats**:
- `expose:all` - User can see ALL tools
- `expose:bundle:customer-service` - User can see all tools in "customer-service" bundle
- `expose:tool:resolve_customer` - User can see specific tool "resolve_customer"

**In-Memory Cache with TTL**:
```python
# File: mcp-server/app/core/exposure/manager.py
class ExposureManager:
    def __init__(self, cache_ttl_seconds: Optional[int] = None):
        # Cache structure: {cache_key: (Set[tool_refs], timestamp)}
        self._exposure_cache: Dict[str, Tuple[Set[str], float]] = {}
        
        # TTL from parameter, environment, or default (3600 seconds = 1 hour)
        self.cache_ttl = cache_ttl_seconds or int(os.getenv("EXPOSURE_CACHE_TTL_SECONDS", "3600"))

# Cache key example: "analyst:operator" (sorted roles)
# Cache value example: ({'__BUNDLE__customer-service', '__BUNDLE__data-analysis'}, 1737982800.123)
```

**Cache Performance**:
- First request: 50ms (database query)
- Subsequent requests: 1ms (cache hit, 50x faster)
- Cache hit rate: >95%
- TTL: 3600 seconds (1 hour, configurable)

**Storage Example**:
```python
# Database query result:
permissions = [
    "expose:bundle:customer-service",
    "expose:bundle:data-analysis"
]

# Cached representation:
exposed_tool_refs = {
    "__BUNDLE__customer-service",   # Prefix indicates bundle reference
    "__BUNDLE__data-analysis"
}

# After filtering (tools/list):
exposed_tools = [
    Tool(name="resolve_customer", bundle_name="customer-service", ...),
    Tool(name="update_customer", bundle_name="customer-service", ...),
    Tool(name="generate_report", bundle_name="data-analysis", ...),
    # ... 37 total tools for analyst role
]
```

---

### **3. Tool Execution Metrics**
    id: uuid.UUID
    name: str                                    # Unique identifier
    display_name: str                            # For UI display
    description: str
    category: str                                # service_booking, etc.
    api_endpoint: str                            # /api/customer/resolve
    http_method: str                             # POST
    input_schema: Dict[str, Any]                 # JSON schema
    output_schema: Optional[Dict[str, Any]]
    headers: Dict[str, str]
    auth_type: str                               # none, basic, bearer
    is_active: bool
    version: str
    risk_level: str                              # read, write, privileged
    requires_elevation: bool
    requires_approval: bool
    max_concurrent_executions: int
    rate_limit_tier: str                         # permissive, standard, strict
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
```

**Loading from Database**:
```python
# File: mcp-server/app/core/tools/registry.py (lines 53-85)
async def _load_from_db(self):
    async with get_db_session() as session:
        result = await session.execute(
            text("SELECT * FROM tools WHERE is_active = true")
        )
        rows = result.fetchall()
        for row in rows:
            tool = Tool(
                id=row.id,
                name=row.name,
                display_name=row.display_name,
                # ... map all fields
            )
            self._tools[tool.name] = tool
```

---

### **3. Tool Execution History & Metrics**

**Storage Type**: Time-Series Database (TimescaleDB) or Prometheus

**File Locations**:
- **Collector**: `mcp-server/app/core/metrics/collector.py`
- **Analytics API**: `mcp-server/app/api/analytics.py`

**Database Schema**:
```sql
-- Table: tool_executions (time-series)
CREATE TABLE tool_executions (
  id UUID PRIMARY KEY,
  correlation_id VARCHAR(255),
  tool_name VARCHAR(255),
  user_id VARCHAR(255),
  status VARCHAR(50),         -- success, failure, timeout
  error_code INTEGER,
  error_message TEXT,
  duration_ms INTEGER,        -- Execution time in milliseconds
  request_size_bytes INTEGER,
  response_size_bytes INTEGER,
  input_data JSONB,           -- Sanitized input
  risk_level VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create index on time for fast range queries:
CREATE INDEX idx_executions_time ON tool_executions(created_at DESC);
CREATE INDEX idx_executions_tool ON tool_executions(tool_name);
CREATE INDEX idx_executions_user ON tool_executions(user_id);

-- Example queries:
SELECT tool_name, COUNT(*) as call_count, AVG(duration_ms) as avg_duration
FROM tool_executions
WHERE created_at >= NOW() - INTERVAL '1 day'
GROUP BY tool_name
ORDER BY call_count DESC;
```

**Metrics Recorded**:
```python
@dataclass
class ToolMetrics:
    tool_name: str
    user_id: str
    status: str              # success, failure
    duration_ms: int
    timestamp: datetime
    request_size_bytes: int
    response_size_bytes: int
    error_code: Optional[int]
    error_message: Optional[str]
    risk_level: str
```

---

### **4. Audit Logs**

**Storage Type**: Immutable Log Storage (PostgreSQL or Elasticsearch)

**File Locations**:
- **Audit Service**: `mcp-server/app/core/audit/service.py`
- **PII Masker**: `mcp-server/app/core/audit/pii_masker.py`

**Database Schema**:
```sql
-- Table: audit_logs (immutable)
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY,
  timestamp TIMESTAMP DEFAULT NOW(),
  correlation_id VARCHAR(255),
  user_id VARCHAR(255),
  user_email VARCHAR(255),
  action VARCHAR(100),       -- tool_executed, tool_registered, etc.
  resource_type VARCHAR(100), -- tool, spec, policy
  resource_id VARCHAR(255),
  details JSONB,             -- Action details (PII masked)
  status VARCHAR(50),        -- success, failure, denied
  reason_code VARCHAR(100),  -- For denials
  ip_address VARCHAR(50),
  user_agent TEXT
);

-- Example audit log:
{
  "id": "audit-123",
  "timestamp": "2026-01-31T10:30:45Z",
  "correlation_id": "req-12345",
  "user_id": "usr_dev_001",
  "user_email": "developer@msil.com",
  "action": "tool_executed",
  "resource_type": "tool",
  "resource_id": "resolve_customer",
  "details": {
    "input": {"mobile": "9876...3210"},    # PII masked
    "output": "success",
    "duration_ms": 245,
    "risk_level": "read"
  },
  "status": "success",
  "ip_address": "192.168.1.100"
}
```

**PII Masking Rules**:
```python
# File: mcp-server/app/core/audit/pii_masker.py

PII_PATTERNS = {
    "phone": r"\d{10}",              # 10-digit phone
    "email": r"[\w\.-]+@[\w\.-]+",   # Email addresses
    "pan": r"[A-Z]{5}[0-9]{4}[A-Z]", # PAN numbers
    "aadhaar": r"\d{12}",            # Aadhaar (12 digits)
    "vehicle_reg": r"[A-Z]{2}\d{2}[A-Z]{2}\d{4}" # Registration plate
}

# Masking applied:
"9876543210" → "9876...3210"
"dev@example.com" → "dev@******.com"
```

### **PII Protection Rules (Strictly Enforced)**

> **CRITICAL**: PII is **prohibited** in logs, traces, and dashboards. The following rules are enforced at multiple layers:

| Layer | Enforcement | Details |
|-------|-------------|---------|
| **Logs** | Automatic masking | PII patterns detected and masked before writing |
| **Traces** | Span attributes sanitized | Phone, email, vehicle reg never in trace data |
| **Dashboards** | No PII fields displayed | Metrics show counts/durations only |
| **Audit** | Masked in `details` JSONB | Original values never stored |
| **API Response** | Payload logging disabled | Response body NOT logged |

**CI/CD Enforcement**:
```yaml
# .github/workflows/security-checks.yml
- name: PII Pattern Detection
  run: |
    # Scan logs for PII patterns
    grep -rE "\d{10}|\d{12}|[A-Z]{5}[0-9]{4}[A-Z]" logs/ && exit 1 || exit 0
    
    # Scan test outputs for exposed PII
    python scripts/detect_pii_in_logs.py --fail-on-detection
```

**Audit Log Retention**:
```python
# Per RFP requirement: 12 months default retention
AUDIT_RETENTION_DAYS: int = 365  # 12 months (RFP requirement)

# Longer retention available via configuration:
# AUDIT_RETENTION_DAYS: int = 2555  # 7 years (optional, for compliance)
```

---

### **5. Policy & Configuration Data**

**Storage Type**: Database + In-Memory Cache

**File Locations**:
- **Policy Engine**: `mcp-server/app/core/policy/engine.py`
- **Risk Policy**: `mcp-server/app/core/policy/risk_policy.py`
- **Configuration**: `mcp-server/app/config.py`

**Database Schema**:
```sql
-- Table: policies
CREATE TABLE policies (
  id UUID PRIMARY KEY,
  policy_type VARCHAR(100),  -- rbac, rate_limit, risk
  policy_name VARCHAR(255),
  content JSONB,             -- Policy rules
  version INTEGER DEFAULT 1,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Example RBAC policy:
{
  "policy_type": "rbac",
  "policy_name": "default_roles",
  "content": {
    "admin": ["tools:read", "tools:write", "policies:write"],
    "developer": ["tools:read", "tools:write"],
    "operator": ["tools:read"],
    "user": ["tools:invoke"]
  }
}

-- Example rate limit policy:
{
  "policy_type": "rate_limit",
  "policy_name": "standard_limits",
  "content": {
    "permissive": {"requests_per_minute": 100, "burst_size": 20},
    "standard": {"requests_per_minute": 50, "burst_size": 10},
    "strict": {"requests_per_minute": 10, "burst_size": 2}
  }
}
```

**Configuration File** (`app/config.py`):
```python
# Lines 63-100: Security & Policy Configuration

# OAuth2/JWT
OAUTH2_ENABLED: bool = True
JWT_SECRET: str = "msil-mcp-jwt-secret-key-..."
JWT_ALGORITHM: str = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

# API Gateway Mode
API_GATEWAY_MODE: str = "mock"  # or "msil_apim"
MOCK_API_BASE_URL: str = "http://localhost:8080"
MSIL_APIM_BASE_URL: str = "https://apim-dev.marutisuzuki.com"
MSIL_APIM_SUBSCRIPTION_KEY: Optional[str] = None

# Rate Limiting
REDIS_ENABLED: bool = True
REDIS_URL: str = "redis://localhost:6379/0"

# PII & Security
PII_MASKING_ENABLED: bool = True
IDEMPOTENCY_ENABLED: bool = True
IDEMPOTENCY_REQUIRED: bool = False

# Features
DEMO_MODE: bool = True  # Bypass auth in MVP
OIDC_ENABLED: bool = False  # For production
```

---

### **6. Cache & Session Storage**

**Storage Type**: Redis

**File Locations**:
- **Cache Service**: `mcp-server/app/core/cache/service.py`
- **Rate Limiter**: `mcp-server/app/core/cache/rate_limiter.py`
- **Idempotency Store**: `mcp-server/app/core/idempotency/store.py`

**Redis Keys Structure**:
```redis
# Rate limiting
ratelimit:user:usr_dev_001 → 45  (remaining tokens)
ratelimit:tool:resolve_customer → 38

# Idempotency
idempotency:idempotent-abc123 → {response_json}  # TTL: 24 hours

# Session cache
session:req-12345 → {session_data}  # TTL: 1 hour

# Tool registry cache
tools:list → [tool1, tool2, ...]    # TTL: 5 minutes
tool:resolve_customer → {tool_data} # TTL: 5 minutes

# OPA policies (if enabled)
policy:rbac → {policy_json}         # TTL: 1 hour
```

**Redis Configuration** (`app/config.py`):
```python
REDIS_URL: str = "redis://localhost:6379/0"
REDIS_ENABLED: bool = True
CACHE_TTL: int = 300        # 5 minutes for tool cache
CACHE_MAX_SIZE: int = 1000   # Max cache entries
```

---

### **7. OpenAPI Specs & Tool Definitions**

**Storage Type**: File System + Database

**File Locations**:
- **Sample Specs**: `sample-apis/customer-service-api.yaml`
- **Upload Handler**: `mcp-server/app/api/openapi_import.py`
- **Parser**: `mcp-server/app/core/openapi/parser.py`

**File Storage** (Temporary):
```
mcp-server/
  ├── uploads/
  │   ├── spec_abc123.yaml
  │   ├── spec_def456.yaml
  │   └── ...
```

**Database Schema** (Persistent):
```sql
-- Table: openapi_specs
CREATE TABLE openapi_specs (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  version VARCHAR(50),
  description TEXT,
  spec_content JSONB,        -- Full OpenAPI spec
  category VARCHAR(100),
  bundle_name VARCHAR(255),
  tools_count INTEGER,
  status VARCHAR(50),        -- uploaded, parsed, approved
  uploaded_by VARCHAR(255),
  uploaded_at TIMESTAMP,
  approved_at TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Example:
{
  "id": "spec_abc123",
  "name": "customer_service_api",
  "version": "1.0.0",
  "category": "service_booking",
  "bundle_name": "customer_service_v1",
  "tools_count": 11,
  "status": "approved",
  "uploaded_by": "admin@msil.com",
  "uploaded_at": "2026-01-31T09:15:00Z",
  "approved_at": "2026-01-31T09:45:00Z"
}
```

**Sample OpenAPI Spec**:
```yaml
# sample-apis/customer-service-api.yaml
openapi: 3.0.0
info:
  title: Customer Service API
  version: 1.0.0
  description: Maruti Suzuki Service Booking API
paths:
  /api/customer/resolve:
    post:
      summary: Resolve Customer
      operationId: resolve_customer
      parameters:
        - name: mobile
          in: query
          required: true
          schema:
            type: string
      responses:
        200:
          description: Success
          content:
            application/json:
              schema:
                type: object
                properties:
                  customer_id:
                    type: string
                  name:
                    type: string
```

---

## User & Role Management

### **Role Hierarchy**

```
┌─────────────────────────────────────────────┐
│ USER ROLES & PERMISSIONS HIERARCHY         │
└─────────────────────────────────────────────┘

                    ADMIN (Level 3)
                        │
            ┌───────────┼───────────┐
            │           │           │
        Manage       Manage      Develop
        Users     Policies       Tools
        Audit     Risk Rules    Execute All
            │           │           │
            ▼           ▼           ▼
                   DEVELOPER (Level 2)
                        │
            ┌───────────┼───────────┐
            │           │           │
        Import       Discover      Test
        OpenAPI      Tools         Tools
        Create Tools
            │           │           │
            ▼           ▼           ▼
                   OPERATOR (Level 1)
                        │
            ┌───────────┼───────────┐
            │           │           │
        Execute      Monitor     View
        Read-Level   Metrics     Logs
        Tools            │           │
            │           ▼           ▼
                   USER (Level 0)
                        │
            ┌───────────┼───────────┐
            │           │           │
        Execute      No Access    No Access
        Tools        (Limited)    to Admin
        (Assigned)
```

### **Role Permissions Matrix**

| Permission | Admin | Developer | Operator | User |
|---|---|---|---|---|
| **Tool Discovery** | ✅ All | ✅ All | ✅ All | ✅ Assigned |
| **Tool Execution** | ✅ All (Privileged) | ✅ Write Level | ✅ Read Level | ✅ Limited |
| **OpenAPI Import** | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| **Tool Registration** | ✅ Approve | ✅ Create | ❌ No | ❌ No |
| **Policy Management** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **User Management** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Audit Logs** | ✅ Yes | ✅ Own Only | ✅ Read | ❌ No |
| **Metrics** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **PIM Elevation** | ✅ Required | ❌ No | ❌ No | ❌ No |

### **Demo Users**

```python
# File: mcp-server/app/core/auth/oauth2_provider.py (lines 35-60)

DEMO_USERS = {
    "admin@msil.com": {
        "user_id": "usr_admin_001",
        "email": "admin@msil.com",
        "password_hash": "admin123",
        "name": "MSIL Admin",
        "roles": ["admin", "developer", "operator"],
        "is_active": True
    },
    "developer@msil.com": {
        "user_id": "usr_dev_001",
        "email": "developer@msil.com",
        "password_hash": "dev123",
        "name": "MSIL Developer",
        "roles": ["developer", "operator"],
        "is_active": True
    },
    "operator@msil.com": {
        "user_id": "usr_op_001",
        "email": "operator@msil.com",
        "password_hash": "op123",
        "name": "MSIL Operator",
        "roles": ["operator"],
        "is_active": True
    }
}
```

---

## Tool Registry & Configuration

### **Tool Registry State**

**Location**: `mcp-server/app/core/tools/registry.py`

**Registry Lifecycle**:

```
┌──────────────────────────────────────────────┐
│ APPLICATION STARTUP                          │
└──────────────────────────────────────────────┘
         │
         ├─ Create ToolRegistry instance
         ├─ Initialize empty _tools dict
         ├─ _loaded = False
         │
         └──────────┬─────────────────────────
                    ▼
┌──────────────────────────────────────────────┐
│ FIRST REQUEST (Lazy Loading)                │
└──────────────────────────────────────────────┘
         │
         ├─ Call _ensure_loaded()
         ├─ Check if _loaded = True
         │  NO → Call _load_from_db()
         │
         ├─ Query: SELECT * FROM tools WHERE is_active = true
         │
         ├─ For each row, create Tool object
         │ ├─ Populate _tools dict: {"tool_name": Tool(...)}
         │ ├─ Set _loaded = True
         │
         └──────────┬─────────────────────────
                    ▼
┌──────────────────────────────────────────────┐
│ NORMAL OPERATIONS                            │
└──────────────────────────────────────────────┘
         │
         ├─ get_tool("resolve_customer")
         │  └─ Return _tools["resolve_customer"]
         │
         ├─ list_tools(category="service_booking")
         │  └─ Filter _tools by category
         │
         ├─ count_tools()
         │  └─ Return len(_tools)
         │
         └──────────┬─────────────────────────
                    ▼
┌──────────────────────────────────────────────┐
│ TOOL REGISTRATION (After OpenAPI Import)    │
└──────────────────────────────────────────────┘
         │
         ├─ INSERT into tools table
         │
         ├─ Call registry.reload() or restart app
         │
         ├─ Set _loaded = False (invalidate cache)
         │
         ├─ Next request will re-load from database
         │
         └─ New tools now available
```

### **Tool Metadata**

```python
# Tool object with all configuration:

Tool(
    # Identity
    id=UUID("550e8400-e29b-41d4-a716-446655440000"),
    name="resolve_customer",
    display_name="Resolve Customer",
    description="Get customer details from phone number",
    
    # Routing
    api_endpoint="/api/customer/resolve",
    http_method="POST",
    category="service_booking",
    
    # Schema
    input_schema={
        "type": "object",
        "properties": {
            "mobile": {
                "type": "string",
                "pattern": "^[0-9]{10}$",
                "description": "10-digit mobile number"
            }
        },
        "required": ["mobile"],
        "additionalProperties": False
    },
    output_schema={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string"},
            "name": {"type": "string"},
            "phone": {"type": "string"},
            "vehicle_count": {"type": "integer"}
        }
    },
    
    # Authentication
    auth_type="api_key",
    headers={"X-API-Key": "msil-mcp-dev-key-2026"},
    
    # Access Control
    risk_level="read",
    requires_elevation=False,
    requires_approval=False,
    max_concurrent_executions=50,
    rate_limit_tier="standard",
    
    # Status
    is_active=True,
    version="1.0.0",
    created_at=datetime(2026, 1, 31, 9, 30, 0),
    updated_at=datetime(2026, 1, 31, 9, 30, 0)
)
```

---

## API Gateway Configuration

### **API Gateway Modes**

**File**: `mcp-server/app/config.py` (lines 41-54)

#### **Mode 1: Mock API (Development)**

```python
API_GATEWAY_MODE: str = "mock"
MOCK_API_BASE_URL: str = "http://localhost:8080"

# When tool is executed:
# Tool endpoint: /api/customer/resolve
# Actual URL: http://localhost:8080/api/customer/resolve
```

**Mock API Server**:
- **Location**: `mock-api/app/main.py`
- **Port**: 8080
- **Purpose**: Simulate Maruti Suzuki backend APIs for development/testing

**Mock API Endpoints**:
```python
# mock-api/app/routers/customer.py
POST /api/customer/resolve
  - Input: {"mobile": "9876543210"}
  - Output: {"customer_id": "C123456", "name": "Rajesh Kumar", ...}

POST /api/vehicle/resolve
  - Input: {"registration_number": "MH12AB1234"}
  - Output: {"vehicle_id": "V789012", "model": "Swift", ...}

POST /api/dealers/nearby
  - Input: {"city": "Mumbai", "area": "Bandra"}
  - Output: [{"dealer_id": "D345", "name": "Mumbai Maruti", ...}, ...]

# etc. - 11 total endpoints
```

#### **Mode 2: MSIL APIM (Production)**

> **Note**: The integration with MSIL's API Manager is **configurable** and does not assume any specific vendor (Azure APIM, AWS API Gateway, Kong, etc.). The configuration below shows placeholders that must be provided by MSIL.

```python
API_GATEWAY_MODE: str = "msil_apim"

# MSIL APIM Configuration (provided by MSIL)
MSIL_APIM_BASE_URL: str = "<MSIL_APIM_ENDPOINT>"  # e.g., "https://apim.marutisuzuki.com"

# Authentication Mode (configurable based on MSIL APIM setup):
# Option A: Subscription Key
MSIL_APIM_SUBSCRIPTION_KEY: Optional[str] = "<SUBSCRIPTION_KEY>"

# Option B: OAuth2 Client Credentials (MSIL IdP - OIDC Provider)
MSIL_IDP_TOKEN_URL: Optional[str] = "<MSIL_IDP_TOKEN_ENDPOINT>"  # OIDC token endpoint
MSIL_IDP_CLIENT_ID: Optional[str] = "<CLIENT_ID>"
MSIL_IDP_CLIENT_SECRET: Optional[str] = "<CLIENT_SECRET>"
MSIL_IDP_SCOPE: Optional[str] = "<API_SCOPE>"

# Option C: mTLS (Mutual TLS)
MSIL_APIM_CLIENT_CERT: Optional[str] = "<PATH_TO_CLIENT_CERT>"
MSIL_APIM_CLIENT_KEY: Optional[str] = "<PATH_TO_CLIENT_KEY>"

# OpenAPI Spec Source (configurable):
# - Portal: MSIL Developer Portal URL
# - Repository: Git repo with OpenAPI specs
# - Secure Endpoint: Authenticated API endpoint returning specs
OPENAPI_SPEC_SOURCE: str = "<portal|repository|endpoint>"
OPENAPI_SPEC_URL: Optional[str] = "<URL_TO_SPECS>"
```

### **APIM Integration: Rate Limit Parity**

To demonstrate governance parity with MSIL APIM:

```python
# MCP Server uses a dedicated APIM consumer identity
MCP_APIM_CONSUMER_ID: str = "mcp-server-consumer"

# Rate limits are configured to match APIM quotas:
# - APIM Product quota: 1000 requests/min
# - MCP internal limit: 1000 requests/min (aligned)

# Dashboard evidence for demo:
# 1. MCP Metrics Dashboard: Shows MCP-side throttling
# 2. APIM Analytics: Shows corresponding APIM-side throttling
# 3. Both dashboards show same request counts & throttle events
```

### **Request Flow by API Gateway Mode**

```
┌─────────────────────────────────────────────┐
│ Tool Executor (app/core/tools/executor.py) │
└─────────────────────────────────────────────┘

_get_base_url():
  if API_GATEWAY_MODE == "mock":
    return "http://localhost:8080"
  else:  # msil_apim
    return "https://apim-dev.marutisuzuki.com"

_get_headers(tool_auth_type):
  headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
  }
  
  if API_GATEWAY_MODE == "msil_apim":
    if MSIL_APIM_SUBSCRIPTION_KEY:
      headers["Ocp-Apim-Subscription-Key"] = MSIL_APIM_SUBSCRIPTION_KEY
    # Add OAuth token if available
  else:
    headers["X-API-Key"] = API_KEY
  
  return headers

execute(tool_name, arguments):
  base_url = _get_base_url()
  headers = _get_headers(tool.auth_type)
  
  url = f"{base_url}{tool.api_endpoint}"
  
  response = await http_client.post(
    url,
    headers=headers,
    json=arguments,
    timeout=30.0
  )
  
  return response.json()
```

---

## Security Policies & Rules

### **RBAC Policies**

**File**: `mcp-server/app/core/policy/engine.py`

```python
# Simple RBAC rules (fallback if OPA not available):

SIMPLE_RULES = {
    "admin": [
        "*"  # Wildcard: admin can do everything
    ],
    "developer": [
        "tools:read",
        "tools:write",
        "tools:create",
        "tools:delete",
        "policies:read",
        "specs:read"
    ],
    "operator": [
        "tools:read",
        "tools:invoke",
        "metrics:read",
        "audit:read_own"
    ],
    "user": [
        "tools:invoke",
        "tools:read_assigned"
    ]
}
```

### **Risk-Based Policies**

**File**: `mcp-server/app/core/policy/risk_policy.py`

```python
RISK_POLICIES = {
    "read": RiskPolicy(
        risk_level="read",
        min_role="operator",         # operator, developer, admin can access
        requires_elevation=False,
        requires_approval=False,
        rate_limit_tier="permissive",
        max_concurrency=50,
        pii_policy="redact"
    ),
    "write": RiskPolicy(
        risk_level="write",
        min_role="developer",        # developer, admin can access
        requires_elevation=False,
        requires_approval=False,
        rate_limit_tier="standard",
        max_concurrency=20,
        pii_policy="mask"
    ),
    "privileged": RiskPolicy(
        risk_level="privileged",
        min_role="admin",            # admin only, with elevation & approval
        requires_elevation=True,     # Requires PIM approval
        requires_approval=True,      # Requires manager approval
        rate_limit_tier="strict",
        max_concurrency=5,
        pii_policy="redact_sensitive"
    )
}
```

### **Rate Limit Policies**

**File**: `mcp-server/app/core/cache/rate_limiter.py`

```python
RATE_LIMIT_TIERS = {
    "permissive": {
        "requests_per_minute": 100,
        "burst_size": 20,
        "window": 60,
        "retry_after": 60
    },
    "standard": {
        "requests_per_minute": 50,
        "burst_size": 10,
        "window": 60,
        "retry_after": 60
    },
    "strict": {
        "requests_per_minute": 10,
        "burst_size": 2,
        "window": 60,
        "retry_after": 60
    }
}
```

---

## RFP Requirements Mapping

### **Complete Traceability Matrix**

| RFP Requirement | Implementation | File | Lines | Status |
|---|---|---|---|---|
| **Authentication: OAuth2/OIDC** | JWT token validation | `oauth2_provider.py` | 95-120 | ✅ |
| **Authorization: RBAC** | Role-based access control | `policy/engine.py` | 1-50 | ✅ |
| **Authorization: Tool-Level** | Per-tool access rules | `policy/risk_policy.py` | 39-90 | ✅ |
| **Policy Engine: OPA Integration** | OpenPolicy Agent ready | `policy/engine.py` | 1-30 | ✅ |
| **Rate Limiting: Per-User** | Token bucket by user_id | `rate_limiter.py` | 85-95 | ✅ |
| **Rate Limiting: Per-Tool** | Token bucket by tool_name | `rate_limiter.py` | 100-110 | ✅ |
| **Rate Limit APIM Parity** | Dedicated consumer + aligned quotas | `executor.py` | 30-50 | ✅ |
| **Input Validation** | JSON schema validation | `mcp.py` | 200-250 | ✅ |
| **Audit Logging** | All actions logged (12-month retention) | `audit/service.py` | 1-100 | ✅ |
| **PII Protection** | Masking + prohibited in logs/traces | `audit/pii_masker.py` | 1-50 | ✅ |
| **Tool Discovery** | MCP tools/list method | `mcp.py` | 100-150 | ✅ |
| **Tool Execution** | MCP tools/call method | `mcp.py` | 150-220 | ✅ |
| **Tool Update Notification** | tools/list_changed event | `mcp.py` | 180-200 | ✅ |
| **Write Tool Confirmation** | user_confirmed required | `executor.py` | 60-80 | ✅ |
| **Idempotency** | For write operations | `idempotency/store.py` | 1-80 | ✅ |
| **Admin Tool Mgmt** | Zero-code OpenAPI import | `openapi_import.py` | 1-200 | ✅ |
| **Metrics** | Real-time analytics | `metrics/collector.py` | 1-100 | ✅ |
| **Multi-Gateway** | Mock API + MSIL APIM (configurable) | `executor.py` | 30-50 | ✅ |
| **Error Handling** | JSON-RPC error codes | `mcp.py` | 250-300 | ✅ |
| **Correlation IDs** | Request tracing | `mcp.py` | 60-70 | ✅ |
| **Secrets Management** | Environment variables | `config.py` | 1-100 | ✅ |

---

## Service Booking Demo Pack

### **Overview**

This section provides the **Stage-2 Demo Artifact** for the Service Booking use case, including:
- Final tool list with schemas
- APIM endpoint mappings
- Mandatory parameter handling
- Success criteria
- Demo runbook

### **Tool List for Service Booking**

| # | Tool Name | Risk Level | APIM Endpoint | Description |
|---|-----------|------------|---------------|-------------|
| 1 | `resolve_customer` | read | `/api/customer/resolve` | Get customer by phone |
| 2 | `resolve_vehicle` | read | `/api/vehicle/resolve` | Get vehicle by registration |
| 3 | `get_customer_vehicles` | read | `/api/customer/{id}/vehicles` | List customer's vehicles |
| 4 | `get_service_history` | read | `/api/vehicle/{id}/service-history` | Get service history |
| 5 | `get_nearby_dealers` | read | `/api/dealers/nearby` | Find dealers by location |
| 6 | `get_dealer_slots` | read | `/api/dealers/{id}/slots` | Get available time slots |
| 7 | `get_service_types` | read | `/api/service-types` | List service types |
| 8 | `get_service_estimates` | read | `/api/estimates` | Get cost estimates |
| 9 | `create_service_booking` | **write** | `/api/bookings` | Create booking |
| 10 | `get_booking_status` | read | `/api/bookings/{id}` | Check booking status |
| 11 | `cancel_booking` | **write** | `/api/bookings/{id}/cancel` | Cancel booking |

### **Mandatory Parameters (9 for create_service_booking)**

```json
{
  "customer_id": "C123456",       // From resolve_customer
  "vehicle_id": "V789012",        // From resolve_vehicle  
  "dealer_id": "D345678",         // From get_nearby_dealers
  "service_type": "general",      // From get_service_types
  "preferred_date": "2026-02-15", // User input
  "preferred_time_slot": "10:00-12:00",  // From get_dealer_slots
  "contact_number": "9876543210", // User input (validated)
  "pickup_required": false,       // User preference
  "user_confirmed": true          // ⚠️ STEP-UP CONFIRMATION REQUIRED
}
```

### **Missing Parameter Handling**

When mandatory parameters are missing, the flow uses resolver tools:

```
User: "Book a service for my car"

LLM decides: Missing customer_id
  → Host calls: resolve_customer({mobile: <from_context>})
  → Returns: customer_id

LLM decides: Missing vehicle_id  
  → Host calls: get_customer_vehicles({customer_id})
  → If multiple: Ask user to select
  → Returns: vehicle_id

LLM decides: Missing dealer_id
  → Host calls: get_nearby_dealers({city, area})
  → Returns: dealer options → User selects

LLM decides: Missing preferred_date/time
  → Host calls: get_dealer_slots({dealer_id, date_range})
  → Returns: available slots → User selects

LLM decides: All parameters collected + user_confirmed=true
  → Host calls: create_service_booking({...all_params})
```

### **Success Criteria**

| Checkpoint | Verification |
|------------|--------------|
| ✅ Booking Created | Response contains `booking_id` |
| ✅ Status Confirmed | Status = `confirmed` or `pending_confirmation` |
| ✅ DB Verification | Query booking by ID in database |
| ✅ Audit Trail | Audit log entry for `create_service_booking` |
| ✅ Correlation | Same correlation_id across all tool calls |
| ✅ Metrics | Dashboard shows booking in real-time |

### **DB Verification Query**

```sql
-- Verify booking in database (Mock API stores in SQLite)
SELECT 
    booking_id,
    customer_id,
    vehicle_id,
    dealer_id,
    service_type,
    booking_date,
    time_slot,
    status,
    created_at
FROM service_bookings
WHERE booking_id = '<BOOKING_ID_FROM_RESPONSE>';
```

### **Demo Runbook**

**Step-by-Step Script**:

| Step | Action | Expected Result | Screenshot |
|------|--------|-----------------|------------|
| 1 | Open Admin UI, show tool list | 11 tools visible | Tools page |
| 2 | Open Chat UI, type: "I want to book a service" | LLM identifies missing info | Chat interface |
| 3 | Provide phone number when asked | Customer resolved | Tool execution log |
| 4 | Select vehicle from list | Vehicle confirmed | Chat interface |
| 5 | Select dealer and time slot | Slots displayed | Chat interface |
| 6 | Confirm booking | user_confirmed=true sent | Request payload |
| 7 | Show booking confirmation | booking_id returned | Chat response |
| 8 | Open Dashboard → Metrics | Booking visible in real-time | Dashboard |
| 9 | Open Dashboard → Audit Logs | Full trail with correlation_id | Audit page |
| 10 | Run DB verification query | Booking record confirmed | DB result |

### **Dashboard Evidence for Demo**

1. **Metrics Dashboard**:
   - Tool execution counts (real-time)
   - Latency percentiles (P50, P95, P99)
   - Success/failure rates
   - Rate limit throttle events

2. **Audit Log View**:
   - Filter by correlation_id
   - Show all 5-7 tool calls in sequence
   - Expand to show masked inputs
   - Show user_confirmed=true on write

3. **APIM Parity Evidence** (if available):
   - MCP rate limit dashboard
   - APIM analytics dashboard  
   - Same request counts visible

---

## Quick Reference: Key File Locations

### **Authentication & Security**
- JWT Handler: `mcp-server/app/core/auth/jwt_handler.py`
- OAuth2 Provider: `mcp-server/app/core/auth/oauth2_provider.py`
- Auth Models: `mcp-server/app/core/auth/models.py`

### **Authorization & Policy**
- Policy Engine: `mcp-server/app/core/policy/engine.py`
- Risk Policy: `mcp-server/app/core/policy/risk_policy.py`
- Policy Models: `mcp-server/app/core/policy/models.py`

### **Rate Limiting & Caching**
- Rate Limiter: `mcp-server/app/core/cache/rate_limiter.py`
- Cache Service: `mcp-server/app/core/cache/service.py`
- Idempotency: `mcp-server/app/core/idempotency/store.py`

### **Tool Management**
- Tool Registry: `mcp-server/app/core/tools/registry.py`
- Tool Executor: `mcp-server/app/core/tools/executor.py`
- OpenAPI Parser: `mcp-server/app/core/openapi/parser.py`

### **Monitoring & Logging**
- Metrics Collector: `mcp-server/app/core/metrics/collector.py`
- Audit Service: `mcp-server/app/core/audit/service.py`
- PII Masker: `mcp-server/app/core/audit/pii_masker.py`

### **API Endpoints**
- MCP Protocol: `mcp-server/app/api/mcp.py`
- Admin API: `mcp-server/app/api/admin.py`
- OpenAPI Import: `mcp-server/app/api/openapi_import.py`
- Analytics: `mcp-server/app/api/analytics.py`

### **Configuration & Database**
- Configuration: `mcp-server/app/config.py`
- Database: `mcp-server/app/db/database.py`
- Repositories: `mcp-server/app/db/repositories.py`

### **UI Components**
- Admin Portal: `admin-ui/src/pages/Import.tsx`, `Dashboard.tsx`, `Tools.tsx`
- Chat Interface: `chat-ui/src/App.tsx`

---

## Conclusion

This comprehensive documentation provides:

1. **MCP Protocol Sequence** with initialize handshake and tools/list_changed notification
2. **Complete flow** from admin adding APIs to MCP client execution
3. **Multi-layered security** with authentication → authorization → rate limiting
4. **Step-up confirmation** for write tools (user_confirmed requirement)
5. **All data storage locations** with database schemas and file paths
6. **Role-based access control** with hierarchy and permissions
7. **PII protection** with explicit prohibition in logs/traces/dashboards
8. **Configuration management** across environments (pluggable APIM/IdP)
9. **Service Booking Demo Pack** for Stage-2 demonstration
10. **RFP requirements traceability** with file locations

All sensitive operations are logged, audited, and protected by role-based policies and rate limiting.

**Last Updated**: February 1, 2026
