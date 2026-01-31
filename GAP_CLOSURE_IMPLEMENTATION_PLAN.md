# MSIL MCP Server - Gap Closure Implementation Plan

**Document Version**: 1.0  
**Date**: January 31, 2026  
**Status**: Phase 7 Planning  
**Context**: Address gaps between Phase 6 implementation and RFP requirements

---

## Executive Summary

Phase 6 delivered **OpenAPI-driven tool generation** and **real metrics collection**, achieving core MCP functionality. However, critical **security, compliance, and resilience** features required by the RFP are missing.

**Current Status**: ✅ DEMO-READY, ❌ NOT PRODUCTION-READY

**Gap Categories**:
- **P0 Critical**: 5 gaps (Security & Compliance) - **BLOCKS CLIENT ACCEPTANCE**
- **P1 High**: 5 gaps (Resilience & Production) - **BLOCKS PRODUCTION DEPLOYMENT**
- **P2 Medium**: 4 gaps (Enhancements) - **IMPROVES USER EXPERIENCE**

**Total Effort Estimate**: 10 days (80 hours)

---

## Table of Contents

1. [P0 Critical Gaps (Must-Have for Client Demo)](#p0-critical-gaps)
2. [P1 High Priority (Production Requirements)](#p1-high-priority)
3. [P2 Medium Priority (Enhancements)](#p2-medium-priority)
4. [Implementation Schedule](#implementation-schedule)
5. [Risk Assessment](#risk-assessment)
6. [Testing Strategy](#testing-strategy)

---

## P0 Critical Gaps (Must-Have for Client Demo)

**Total Effort**: 5 days (40 hours)  
**Priority**: CRITICAL - Required for RFP compliance and client acceptance

### Gap 1: OAuth2/OIDC Authentication ⭐ HIGHEST PRIORITY

**RFP Requirement**: SEC-001 (P0 Critical)  
**Current State**: Simple API key authentication only  
**Business Impact**: Cannot demonstrate enterprise-grade security; BLOCKS client demo

#### Implementation Details

**Effort**: 2 days (16 hours)

**Files to Create**:
```
mcp-server/app/core/auth/
├── __init__.py
├── jwt_handler.py          # JWT token validation, refresh
├── oauth2_provider.py      # OAuth2 client credentials & auth code flow
├── identity_providers.py   # Configurable IdP integration (Cognito, Auth0, Azure AD)
└── middleware.py           # FastAPI dependency for auth
```

**Files to Modify**:
```
mcp-server/app/main.py      # Add auth middleware
mcp-server/app/api/mcp.py   # Replace API key with JWT validation
mcp-server/app/api/admin.py # Add auth dependencies
mcp-server/app/api/chat.py  # Add auth dependencies
mcp-server/app/config.py    # Add OAuth2 settings
mcp-server/requirements.txt # Add: python-jose[cryptography], python-multipart
```

**Frontend Changes**:
```
admin-ui/src/contexts/AuthContext.tsx   # NEW: Auth state management
admin-ui/src/components/Login.tsx       # NEW: Login page
admin-ui/src/lib/api.ts                # Modify: Add Bearer token to all requests
admin-ui/src/App.tsx                   # Add: Protected routes
```

#### Implementation Steps

**Day 1: Backend OAuth2 (8 hours)**

1. **Create JWT Handler** (2 hours)
   ```python
   # app/core/auth/jwt_handler.py
   from jose import JWTError, jwt
   from datetime import datetime, timedelta
   
   class JWTHandler:
       def __init__(self, secret_key: str, algorithm: str = "RS256"):
           self.secret_key = secret_key
           self.algorithm = algorithm
       
       def create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
           """Create JWT access token"""
           to_encode = data.copy()
           expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
           to_encode.update({"exp": expire, "iat": datetime.utcnow()})
           return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
       
       def verify_token(self, token: str) -> dict:
           """Verify and decode JWT token"""
           try:
               payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
               return payload
           except JWTError as e:
               raise ValueError(f"Invalid token: {str(e)}")
   ```

2. **Create OAuth2 Provider** (3 hours)
   ```python
   # app/core/auth/oauth2_provider.py
   from fastapi import Depends, HTTPException, status
   from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
   import httpx
   
   security = HTTPBearer()
   
   class OAuth2Provider:
       def __init__(self, token_url: str, client_id: str, client_secret: str):
           self.token_url = token_url
           self.client_id = client_id
           self.client_secret = client_secret
           self.jwt_handler = JWTHandler(settings.JWT_SECRET)
       
       async def get_access_token(self, code: str) -> dict:
           """Exchange authorization code for access token"""
           async with httpx.AsyncClient() as client:
               response = await client.post(
                   self.token_url,
                   data={
                       "grant_type": "authorization_code",
                       "code": code,
                       "client_id": self.client_id,
                       "client_secret": self.client_secret,
                   }
               )
               response.raise_for_status()
               return response.json()
       
       async def validate_token(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
           """Validate JWT token from Authorization header"""
           try:
               payload = self.jwt_handler.verify_token(credentials.credentials)
               return payload
           except ValueError:
               raise HTTPException(
                   status_code=status.HTTP_401_UNAUTHORIZED,
                   detail="Invalid authentication credentials",
                   headers={"WWW-Authenticate": "Bearer"},
               )
   ```

3. **Create Auth Middleware** (2 hours)
   ```python
   # app/core/auth/middleware.py
   from fastapi import Request, HTTPException
   from starlette.middleware.base import BaseHTTPMiddleware
   
   class AuthMiddleware(BaseHTTPMiddleware):
       def __init__(self, app, oauth_provider: OAuth2Provider):
           super().__init__(app)
           self.oauth_provider = oauth_provider
       
       async def dispatch(self, request: Request, call_next):
           # Skip auth for health check and docs
           if request.url.path in ["/health", "/docs", "/openapi.json"]:
               return await call_next(request)
           
           # Extract token
           auth_header = request.headers.get("Authorization")
           if not auth_header or not auth_header.startswith("Bearer "):
               raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
           
           # Validate token
           token = auth_header.split(" ")[1]
           try:
               payload = self.oauth_provider.jwt_handler.verify_token(token)
               request.state.user = payload
           except ValueError as e:
               raise HTTPException(status_code=401, detail=str(e))
           
           return await call_next(request)
   ```

4. **Update Config** (1 hour)
   ```python
   # app/config.py - Add OAuth2 settings
   OAUTH2_ENABLED: bool = Field(default=True, env="OAUTH2_ENABLED")
   OAUTH2_PROVIDER: str = Field(default="auth0", env="OAUTH2_PROVIDER")
   OAUTH2_TOKEN_URL: str = Field(default="", env="OAUTH2_TOKEN_URL")
   OAUTH2_CLIENT_ID: str = Field(default="", env="OAUTH2_CLIENT_ID")
   OAUTH2_CLIENT_SECRET: str = Field(default="", env="OAUTH2_CLIENT_SECRET")
   JWT_SECRET: str = Field(default="", env="JWT_SECRET")
   JWT_ALGORITHM: str = Field(default="RS256", env="JWT_ALGORITHM")
   JWT_EXPIRY_MINUTES: int = Field(default=60, env="JWT_EXPIRY_MINUTES")
   ```

**Day 2: Frontend OAuth2 + Integration (8 hours)**

5. **Create Auth Context** (2 hours)
   ```typescript
   // admin-ui/src/contexts/AuthContext.tsx
   import { createContext, useContext, useState, useEffect } from 'react'
   
   interface AuthContextType {
     user: User | null
     token: string | null
     login: (email: string, password: string) => Promise<void>
     logout: () => void
     isAuthenticated: boolean
   }
   
   const AuthContext = createContext<AuthContextType | undefined>(undefined)
   
   export function AuthProvider({ children }: { children: React.ReactNode }) {
     const [user, setUser] = useState<User | null>(null)
     const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
     
     const login = async (email: string, password: string) => {
       const response = await fetch('/api/auth/login', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ email, password })
       })
       const data = await response.json()
       setToken(data.access_token)
       setUser(data.user)
       localStorage.setItem('token', data.access_token)
     }
     
     const logout = () => {
       setToken(null)
       setUser(null)
       localStorage.removeItem('token')
     }
     
     return (
       <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!token }}>
         {children}
       </AuthContext.Provider>
     )
   }
   
   export const useAuth = () => {
     const context = useContext(AuthContext)
     if (!context) throw new Error('useAuth must be used within AuthProvider')
     return context
   }
   ```

6. **Create Login Page** (2 hours)
7. **Update API Client** (1 hour)
8. **Integration Testing** (3 hours)

#### Acceptance Criteria
- [ ] JWT token generation and validation working
- [ ] OAuth2 authorization code flow functional
- [ ] Token refresh mechanism implemented
- [ ] Admin UI login page operational
- [ ] All API endpoints require valid JWT
- [ ] Token expiry handled gracefully
- [ ] Test with at least one IdP (Auth0 or Cognito)

---

### Gap 2: Policy Engine (OPA) with RBAC ⭐ HIGHEST PRIORITY

**RFP Requirement**: SEC-002, SEC-003 (P0 Critical)  
**Current State**: No policy enforcement, no RBAC  
**Business Impact**: Cannot demonstrate security guardrails; FAILS RFP compliance

#### Implementation Details

**Effort**: 1 day (8 hours)

**Files to Create**:
```
mcp-server/app/core/policy/
├── __init__.py
├── engine.py              # OPA client and policy evaluation
├── models.py              # PolicyDecision, PolicyRule models
└── rego/
    ├── authz.rego        # RBAC policies
    ├── tools.rego        # Tool-level policies
    └── rate_limit.rego   # Rate limiting rules

infrastructure/local/docker-compose.infra.yml  # Add OPA container
```

**Files to Modify**:
```
mcp-server/app/api/mcp.py      # Add policy checks before tool execution
mcp-server/app/api/admin.py    # Add policy checks for admin operations
mcp-server/app/config.py       # Add OPA_URL setting
```

#### Implementation Steps

**Hour 1-2: OPA Setup**
```yaml
# docker-compose.infra.yml - Add OPA service
  opa:
    image: openpolicyagent/opa:latest-rootless
    container_name: msil-mcp-opa
    ports:
      - "8181:8181"
    command:
      - "run"
      - "--server"
      - "--addr=0.0.0.0:8181"
      - "/policies"
    volumes:
      - ./mcp-server/app/core/policy/rego:/policies
    networks:
      - mcp-network
```

**Hour 3-4: Policy Engine Implementation**
```python
# app/core/policy/engine.py
import httpx
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    policies_evaluated: List[str]

class PolicyEngine:
    def __init__(self, opa_url: str = "http://localhost:8181"):
        self.opa_url = opa_url
        self.client = httpx.AsyncClient()
    
    async def evaluate(
        self,
        action: str,
        resource: str,
        context: Dict[str, Any]
    ) -> PolicyDecision:
        """Evaluate policy for an action on a resource"""
        input_data = {
            "input": {
                "action": action,
                "resource": resource,
                "user": context.get("user"),
                "roles": context.get("roles", []),
                "timestamp": context.get("timestamp")
            }
        }
        
        response = await self.client.post(
            f"{self.opa_url}/v1/data/msil/authz/allow",
            json=input_data
        )
        result = response.json()
        
        return PolicyDecision(
            allowed=result.get("result", False),
            reason=result.get("reason", "Policy denied"),
            policies_evaluated=result.get("policies", [])
        )
    
    async def check_tool_access(self, user_roles: List[str], tool_name: str) -> bool:
        """Check if user roles have access to tool"""
        decision = await self.evaluate(
            action="invoke",
            resource=tool_name,
            context={"roles": user_roles}
        )
        return decision.allowed
```

**Hour 5-6: RBAC Policies (Rego)**
```rego
# app/core/policy/rego/authz.rego
package msil.authz

default allow = false

# Admin can do everything
allow {
    input.roles[_] == "admin"
}

# Developers can read and write tools
allow {
    input.action in ["read", "write"]
    input.roles[_] == "developer"
    startswith(input.resource, "tool_")
}

# Operators can read tools and execute them
allow {
    input.action in ["read", "invoke"]
    input.roles[_] == "operator"
}

# Users can only execute allowed tools
allow {
    input.action == "invoke"
    input.roles[_] == "user"
    tool_allowed[input.resource]
}

# Tool allow list per role
tool_allowed[tool] {
    role := input.roles[_]
    allowed_tools := data.role_tools[role]
    tool := allowed_tools[_]
}

# Rate limit check
allow {
    input.action == "invoke"
    not rate_limited
}

rate_limited {
    count := data.rate_limits[input.user][input.resource]
    count > 100  # 100 requests per minute
}
```

**Hour 7-8: Integration & Testing**

#### Acceptance Criteria
- [ ] OPA container running and accessible
- [ ] RBAC policies loaded and functional
- [ ] Admin, Developer, Operator, User roles defined
- [ ] Tool access checked before execution
- [ ] Policy decisions logged in audit trail
- [ ] Rate limiting policies enforced

---

### Gap 3: Audit Service with Tamper-Evident Trails ⭐ CRITICAL

**RFP Requirement**: FR-ADMIN-006, OBS-AUDIT-001, OBS-AUDIT-002 (P0 Critical)  
**Current State**: No audit logging  
**Business Impact**: FAILS compliance requirement (12-month retention, tamper-evident)

#### Implementation Details

**Effort**: 1 day (8 hours)

**Files to Create**:
```
mcp-server/app/core/audit/
├── __init__.py
├── service.py            # AuditService class
├── models.py             # AuditEvent dataclass
└── s3_writer.py          # S3 WORM storage writer

mcp-server/app/db/migrations/
└── 003_create_audit_tables.sql
```

**Files to Modify**:
```
mcp-server/app/core/tools/executor.py  # Add audit logging
mcp-server/app/api/mcp.py             # Log all MCP calls
mcp-server/app/api/admin.py           # Add audit log viewer endpoint
```

#### Implementation Steps

**Hour 1-2: Database Schema**
```sql
-- 003_create_audit_tables.sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id VARCHAR(100) NOT NULL UNIQUE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    correlation_id VARCHAR(100),
    user_id VARCHAR(100),
    tool_name VARCHAR(100),
    action VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    latency_ms DECIMAL(10, 2),
    request_size INTEGER,
    response_size INTEGER,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_tool ON audit_logs(tool_name);
CREATE INDEX idx_audit_status ON audit_logs(status);
```

**Hour 3-5: Audit Service Implementation**
```python
# app/core/audit/service.py
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, Optional
import json
import uuid

@dataclass
class AuditEvent:
    event_id: str
    timestamp: datetime
    event_type: str  # tool_call, policy_decision, auth_event, config_change
    correlation_id: str
    user_id: Optional[str]
    tool_name: Optional[str]
    action: str
    status: str  # success, failure, denied
    latency_ms: Optional[float]
    request_size: Optional[int]
    response_size: Optional[int]
    error_message: Optional[str]
    metadata: Dict[str, Any]

class AuditService:
    """Audit logging for compliance with 12-month retention"""
    
    def __init__(self, db, s3_client=None):
        self.db = db
        self.s3 = s3_client
    
    async def log_event(self, event: AuditEvent):
        """Log audit event to PostgreSQL and optionally S3"""
        # Store in PostgreSQL
        query = """
            INSERT INTO audit_logs (
                event_id, timestamp, event_type, correlation_id,
                user_id, tool_name, action, status, latency_ms,
                request_size, response_size, error_message, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """
        await self.db.execute(
            query,
            event.event_id, event.timestamp, event.event_type,
            event.correlation_id, self._mask_pii(event.user_id),
            event.tool_name, event.action, event.status, event.latency_ms,
            event.request_size, event.response_size, event.error_message,
            json.dumps(event.metadata)
        )
        
        # Async write to S3 for immutable storage (future: S3 Object Lock)
        if self.s3:
            await self._write_to_s3(event)
    
    async def log_tool_call(
        self,
        tool_name: str,
        params: Dict,
        result: Any,
        latency: float,
        correlation_id: str,
        user_id: str,
        status: str = "success",
        error: str = None
    ):
        """Log tool execution"""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            event_type="tool_call",
            correlation_id=correlation_id,
            user_id=user_id,
            tool_name=tool_name,
            action="invoke",
            status=status,
            latency_ms=latency * 1000,
            request_size=len(json.dumps(params)),
            response_size=len(json.dumps(result)),
            error_message=error,
            metadata={"params": params, "result": result}
        )
        await self.log_event(event)
    
    async def log_policy_decision(
        self,
        decision: PolicyDecision,
        context: Dict,
        correlation_id: str
    ):
        """Log policy decision"""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            event_type="policy_decision",
            correlation_id=correlation_id,
            user_id=context.get("user_id"),
            tool_name=context.get("tool_name"),
            action=context.get("action"),
            status="allowed" if decision.allowed else "denied",
            latency_ms=None,
            request_size=None,
            response_size=None,
            error_message=decision.reason if not decision.allowed else None,
            metadata={"policies": decision.policies_evaluated}
        )
        await self.log_event(event)
    
    def _mask_pii(self, value: str) -> str:
        """Mask PII for logging"""
        if not value or len(value) <= 4:
            return "***"
        return f"{value[:2]}***{value[-2:]}"
    
    async def _write_to_s3(self, event: AuditEvent):
        """Write audit event to S3 for long-term storage"""
        # Future: Implement S3 Object Lock for WORM compliance
        pass

# Singleton instance
audit_service = AuditService(db=None, s3_client=None)
```

**Hour 6-7: Integration**
**Hour 8: Audit Log Viewer API**

#### Acceptance Criteria
- [ ] All tool executions logged to audit_logs table
- [ ] Policy decisions logged
- [ ] PII masked in logs (phone, email)
- [ ] Correlation IDs tracked across requests
- [ ] Audit log viewer API endpoint working
- [ ] Database indexes created for fast queries
- [ ] S3 storage structure documented (for future implementation)

---

### Gap 4: Policy Configuration UI

**RFP Requirement**: FR-ADMIN-004 (P0 Critical)  
**Current State**: No policy management UI  
**Business Impact**: Cannot demonstrate policy configuration

#### Implementation Details

**Effort**: 6 hours

**Files to Create**:
```
admin-ui/src/pages/Policies.tsx
admin-ui/src/components/policies/
├── PolicyList.tsx
├── PolicyEditor.tsx
├── RolePermissions.tsx
└── ToolAccessControl.tsx
```

**Files to Modify**:
```
admin-ui/src/App.tsx      # Add /policies route
admin-ui/src/components/layout/Sidebar.tsx  # Add policies nav item
mcp-server/app/api/admin.py  # Add policy CRUD endpoints
```

#### Implementation Steps

**Hour 1-2: Backend Policy API**
```python
# app/api/admin.py - Add policy endpoints
@router.get("/policies")
async def list_policies():
    """List all policies"""
    # Query from OPA or database
    pass

@router.post("/policies")
async def create_policy(policy: PolicyCreate):
    """Create new policy"""
    pass

@router.put("/policies/{policy_id}")
async def update_policy(policy_id: str, policy: PolicyUpdate):
    """Update policy"""
    pass

@router.delete("/policies/{policy_id}")
async def delete_policy(policy_id: str):
    """Delete policy"""
    pass

@router.get("/roles")
async def list_roles():
    """List all roles"""
    return {
        "roles": ["admin", "developer", "operator", "user"]
    }

@router.get("/roles/{role}/permissions")
async def get_role_permissions(role: str):
    """Get permissions for a role"""
    pass

@router.put("/roles/{role}/permissions")
async def update_role_permissions(role: str, permissions: List[str]):
    """Update role permissions"""
    pass
```

**Hour 3-4: Frontend Policy List**
**Hour 5-6: Frontend Policy Editor**

#### Acceptance Criteria
- [ ] Policy list page showing all policies
- [ ] Create/edit/delete policy functionality
- [ ] Role permissions editor
- [ ] Tool access control per role
- [ ] Allow/deny list configuration
- [ ] Rate limit configuration per tool

---

### Gap 5: Audit Log Viewer UI

**RFP Requirement**: FR-ADMIN-006 (P0 Critical)  
**Current State**: No audit log viewing capability  
**Business Impact**: Cannot demonstrate compliance review

#### Implementation Details

**Effort**: 4 hours

**Files to Create**:
```
admin-ui/src/pages/AuditLogs.tsx
admin-ui/src/components/audit/
├── AuditLogTable.tsx
├── AuditLogFilters.tsx
├── AuditLogDetail.tsx
└── ExportButton.tsx
```

#### Implementation Steps

**Hour 1-2: Backend Audit Query API**
```python
# app/api/admin.py - Add audit log endpoints
@router.get("/audit-logs")
async def get_audit_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    tool_name: Optional[str] = None,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get audit logs with filters"""
    query = "SELECT * FROM audit_logs WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND timestamp >= $1"
        params.append(start_date)
    if end_date:
        query += " AND timestamp <= $2"
        params.append(end_date)
    if tool_name:
        query += " AND tool_name = $3"
        params.append(tool_name)
    # ... more filters
    
    query += f" ORDER BY timestamp DESC LIMIT {limit} OFFSET {offset}"
    
    logs = await db.fetch(query, *params)
    return {"logs": logs, "total": len(logs)}

@router.get("/audit-logs/{event_id}")
async def get_audit_log_detail(event_id: str):
    """Get detailed audit log entry"""
    pass

@router.get("/audit-logs/export")
async def export_audit_logs(format: str = "csv"):
    """Export audit logs to CSV/JSON"""
    pass
```

**Hour 3-4: Frontend Audit Viewer**

#### Acceptance Criteria
- [ ] Audit log table with pagination
- [ ] Filters: date range, tool, user, status
- [ ] Search functionality
- [ ] Detailed log view in modal
- [ ] Export to CSV/JSON
- [ ] Highlight policy violations

---

## P1 High Priority (Production Requirements)

**Total Effort**: 3 days (24 hours)  
**Priority**: HIGH - Required for production deployment

### Gap 6: Circuit Breaker & Retry Logic

**RFP Requirement**: Design doc Section 3.3, "Circuit Breaker, Retry Logic"  
**Current State**: Single attempt with timeout  
**Business Impact**: No resilience to transient failures

#### Implementation Details

**Effort**: 4 hours

**Files to Modify**:
```
mcp-server/app/core/tools/executor.py
mcp-server/requirements.txt  # Add: tenacity, circuitbreaker
```

#### Implementation Steps

**Hour 1-2: Add Circuit Breaker**
```python
# app/core/tools/executor.py
from circuitbreaker import circuit
from tenacity import retry, stop_after_attempt, wait_exponential

class ToolExecutor:
    # ... existing code ...
    
    @circuit(failure_threshold=5, recovery_timeout=60, expected_exception=httpx.HTTPError)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def _execute_with_retry(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        headers: Dict,
        json_data: Dict
    ) -> httpx.Response:
        """Execute HTTP request with retry and circuit breaker"""
        if method == "GET":
            response = await client.get(url, headers=headers, params=json_data)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=json_data)
        elif method == "PUT":
            response = await client.put(url, headers=headers, json=json_data)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response
```

**Hour 3-4: Testing & Metrics**

#### Acceptance Criteria
- [ ] Circuit breaker opens after 5 failures
- [ ] Circuit breaker recovers after 60 seconds
- [ ] Retry logic: 3 attempts with exponential backoff
- [ ] Circuit state logged and monitored
- [ ] Metrics track retry attempts and circuit state

---

### Gap 7: Response Shaping (Token Optimization)

**RFP Requirement**: FR-MCP-007 (P1 High), "Compact payloads, selective fields"  
**Current State**: Returns full API responses  
**Business Impact**: High token costs, slow responses

#### Implementation Details

**Effort**: 6 hours

**Files to Create**:
```
mcp-server/app/core/response/
├── __init__.py
├── shaper.py           # Response shaping logic
└── field_selector.py   # Field inclusion/exclusion
```

**Files to Modify**:
```
mcp-server/app/core/tools/executor.py  # Apply response shaping
mcp-server/app/db/models.py           # Add response_shape to Tool model
```

#### Implementation Steps

**Hour 1-3: Response Shaper**
```python
# app/core/response/shaper.py
from typing import Any, Dict, List, Optional

class ResponseShaper:
    """Shape API responses for token efficiency"""
    
    def shape(
        self,
        response: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply response shaping rules"""
        if not config:
            return response
        
        shaped = {}
        
        # Include only specified fields
        if "include_fields" in config:
            shaped = self._include_fields(response, config["include_fields"])
        else:
            shaped = response
        
        # Exclude specified fields
        if "exclude_fields" in config:
            shaped = self._exclude_fields(shaped, config["exclude_fields"])
        
        # Limit array sizes
        if "max_array_size" in config:
            shaped = self._limit_arrays(shaped, config["max_array_size"])
        
        # Compact nested objects
        if config.get("compact", False):
            shaped = self._compact(shaped)
        
        return shaped
    
    def _include_fields(self, data: Any, fields: List[str]) -> Any:
        """Include only specified fields"""
        if isinstance(data, dict):
            return {k: data[k] for k in fields if k in data}
        return data
    
    def _exclude_fields(self, data: Any, fields: List[str]) -> Any:
        """Exclude specified fields"""
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if k not in fields}
        return data
    
    def _limit_arrays(self, data: Any, max_size: int) -> Any:
        """Limit array sizes"""
        if isinstance(data, list):
            return data[:max_size]
        elif isinstance(data, dict):
            return {k: self._limit_arrays(v, max_size) for k, v in data.items()}
        return data
    
    def _compact(self, data: Any) -> Any:
        """Remove null values and empty objects"""
        if isinstance(data, dict):
            return {
                k: self._compact(v)
                for k, v in data.items()
                if v is not None and v != {} and v != []
            }
        elif isinstance(data, list):
            return [self._compact(item) for item in data]
        return data
```

**Hour 4-6: Integration & Tool Config**

#### Acceptance Criteria
- [ ] Response shaping config per tool
- [ ] Field selection (include/exclude) working
- [ ] Array size limiting functional
- [ ] Null/empty value removal
- [ ] Response size metrics tracked
- [ ] Token count estimation

---

### Gap 8: PII Masking in Logs

**RFP Requirement**: SEC-007, "Mask PII in logs (phone, emails)"  
**Current State**: No PII redaction  
**Business Impact**: Privacy violation, non-compliant

#### Implementation Details

**Effort**: 2 hours

**Files to Create**:
```
mcp-server/app/core/utils/
├── __init__.py
└── pii_masker.py
```

**Files to Modify**:
```
mcp-server/app/core/audit/service.py  # Use PII masker
All logging statements in app/
```

#### Implementation Steps

**Hour 1: PII Masker**
```python
# app/core/utils/pii_masker.py
import re
from typing import Any, Dict

class PIIMasker:
    """Mask PII in logs and audit trails"""
    
    PHONE_PATTERN = re.compile(r'\b\d{10}\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    def mask_phone(self, text: str) -> str:
        """Mask phone numbers"""
        return self.PHONE_PATTERN.sub(lambda m: f"{m.group()[:2]}******{m.group()[-2:]}", text)
    
    def mask_email(self, text: str) -> str:
        """Mask email addresses"""
        return self.EMAIL_PATTERN.sub(lambda m: f"{m.group()[:2]}***@{m.group().split('@')[1]}", text)
    
    def mask_dict(self, data: Dict) -> Dict:
        """Recursively mask PII in dictionary"""
        masked = {}
        for key, value in data.items():
            if isinstance(value, str):
                value = self.mask_phone(value)
                value = self.mask_email(value)
            elif isinstance(value, dict):
                value = self.mask_dict(value)
            elif isinstance(value, list):
                value = [self.mask_dict(item) if isinstance(item, dict) else item for item in value]
            masked[key] = value
        return masked

pii_masker = PIIMasker()
```

**Hour 2: Apply Across Codebase**

#### Acceptance Criteria
- [ ] Phone numbers masked: `98******10`
- [ ] Emails masked: `us***@example.com`
- [ ] Applied to all log statements
- [ ] Applied to audit trail
- [ ] Configurable masking rules

---

### Gap 9: Cache Service (Redis)

**RFP Requirement**: Design doc Section 3.5 - Redis cache  
**Current State**: No caching  
**Business Impact**: Poor performance, no rate limiting storage

#### Implementation Details

**Effort**: 4 hours

**Files to Create**:
```
mcp-server/app/core/cache/
├── __init__.py
├── service.py
└── rate_limiter.py
```

**Files to Modify**:
```
mcp-server/app/main.py      # Initialize cache on startup
mcp-server/app/config.py    # Add Redis settings
```

#### Implementation Steps

**Hour 1-2: Cache Service**
```python
# app/core/cache/service.py
import redis.asyncio as redis
from typing import Any, Optional
import json

class CacheService:
    """Redis cache service"""
    
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL"""
        await self.redis.setex(key, ttl, json.dumps(value))
    
    async def delete(self, key: str):
        """Delete key from cache"""
        await self.redis.delete(key)
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        return await self.redis.incr(key, amount)
    
    async def expire(self, key: str, ttl: int):
        """Set expiration on key"""
        await self.redis.expire(key, ttl)

cache_service = CacheService(settings.REDIS_URL)
```

**Hour 3: Rate Limiter**
```python
# app/core/cache/rate_limiter.py
from datetime import datetime

class RateLimiter:
    """Rate limiting using Redis"""
    
    def __init__(self, cache: CacheService):
        self.cache = cache
    
    async def check_limit(
        self,
        key: str,
        limit: int,
        window: int = 60
    ) -> bool:
        """Check if rate limit exceeded"""
        current = await self.cache.increment(f"rate:{key}")
        
        if current == 1:
            await self.cache.expire(f"rate:{key}", window)
        
        return current <= limit
    
    async def get_remaining(self, key: str, limit: int) -> int:
        """Get remaining requests"""
        current = await self.cache.get(f"rate:{key}") or 0
        return max(0, limit - current)
```

**Hour 4: Integration & Testing**

#### Acceptance Criteria
- [ ] Redis connection working
- [ ] Response caching functional
- [ ] Cache hit/miss metrics tracked
- [ ] Rate limiting via Redis
- [ ] Configurable TTL per resource type

---

### Gap 10: Tool Enable/Disable Toggle

**RFP Requirement**: FR-ADMIN-002 "Enable/disable tools"  
**Current State**: No UI toggle  
**Business Impact**: Cannot manage tool lifecycle from UI

#### Implementation Details

**Effort**: 4 hours

**Files to Modify**:
```
admin-ui/src/pages/Tools.tsx
admin-ui/src/components/tools/ToolCard.tsx
mcp-server/app/api/admin.py  # Add toggle endpoint
```

#### Implementation Steps

**Hour 1: Backend Toggle API**
```python
# app/api/admin.py
@router.patch("/tools/{tool_name}/toggle")
async def toggle_tool(tool_name: str):
    """Enable/disable a tool"""
    tool = await tool_registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    tool.is_active = not tool.is_active
    await tool_registry.update_tool(tool)
    
    # Log to audit
    await audit_service.log_event(AuditEvent(
        event_type="config_change",
        action="toggle_tool",
        tool_name=tool_name,
        status="success",
        metadata={"is_active": tool.is_active}
    ))
    
    return {"tool_name": tool_name, "is_active": tool.is_active}
```

**Hour 2-3: Frontend Toggle**
**Hour 4: Testing**

#### Acceptance Criteria
- [ ] Toggle switch in Tools page
- [ ] Real-time update on toggle
- [ ] Disabled tools hidden from tools/list
- [ ] Audit log records toggle events
- [ ] Confirmation modal before disabling

---

## P2 Medium Priority (Enhancements)

**Total Effort**: 2 days (16 hours)  
**Priority**: MEDIUM - Improves user experience

### Gap 11: Structured JSON Logging

**Effort**: 2 hours  
**Impact**: Better log analysis and monitoring

### Gap 12: Service Booking Wizard UI

**Effort**: 6 hours  
**Impact**: Better demo experience

### Gap 13: SSE Streaming Support

**Effort**: 4 hours  
**Impact**: Real-time updates for long-running tools

### Gap 14: Tool Versioning

**Effort**: 4 hours  
**Impact**: Support multiple API versions

---

## Implementation Schedule

### Week 1 (5 days - P0 Critical)

**Day 1: OAuth2 Backend**
- 08:00-10:00: JWT Handler
- 10:00-13:00: OAuth2 Provider
- 14:00-16:00: Auth Middleware
- 16:00-17:00: Config updates

**Day 2: OAuth2 Frontend + Integration**
- 08:00-10:00: Auth Context
- 10:00-12:00: Login Page
- 13:00-14:00: API Client updates
- 14:00-17:00: Integration testing

**Day 3: Policy Engine**
- 08:00-10:00: OPA setup
- 10:00-12:00: Policy Engine implementation
- 13:00-15:00: RBAC policies (Rego)
- 15:00-17:00: Integration & testing

**Day 4: Audit Service**
- 08:00-10:00: Database schema
- 10:00-13:00: AuditService implementation
- 14:00-15:00: Integration
- 15:00-17:00: Audit log viewer API

**Day 5: Policy & Audit UIs**
- 08:00-11:00: Policy Configuration UI (6h from Gap 4)
- 11:00-12:00: Break
- 13:00-17:00: Audit Log Viewer UI (4h from Gap 5)

### Week 2 (3 days - P1 High)

**Day 6: Resilience**
- 08:00-12:00: Circuit Breaker & Retry Logic (4h)
- 13:00-17:00: Response Shaping (4h of 6h)

**Day 7: Response Shaping + PII + Cache**
- 08:00-10:00: Response Shaping completion (2h)
- 10:00-12:00: PII Masking (2h)
- 13:00-17:00: Cache Service (4h)

**Day 8: Tool Toggle + Testing**
- 08:00-12:00: Tool Enable/Disable Toggle (4h)
- 13:00-17:00: Integration testing, bug fixes

### Optional Week 3 (P2 - If time permits)

**Day 9-10: Enhancements**
- Structured logging
- Service booking wizard
- SSE streaming
- Tool versioning

---

## Risk Assessment

### High Risk

1. **OAuth2 Integration Complexity** ⚠️
   - Risk: Multiple IdP support may be complex
   - Mitigation: Start with one IdP (Auth0 or Cognito), document interfaces
   - Contingency: Use JWT validation only, defer full OAuth2

2. **OPA Policy Learning Curve** ⚠️
   - Risk: Team unfamiliar with Rego language
   - Mitigation: Use simple RBAC policies first, reference OPA docs
   - Contingency: Implement basic RBAC in Python, migrate to OPA later

3. **Audit Trail Performance** ⚠️
   - Risk: High volume logging may impact performance
   - Mitigation: Async logging, database indexes, partitioning
   - Contingency: Reduce log detail level, increase retention window

### Medium Risk

4. **Circuit Breaker False Positives** ⚠️
   - Risk: Circuit breaker may open unnecessarily
   - Mitigation: Tune thresholds based on testing
   - Contingency: Add manual circuit reset endpoint

5. **Cache Invalidation** ⚠️
   - Risk: Stale data in cache
   - Mitigation: Conservative TTLs, cache versioning
   - Contingency: Cache disable flag for debugging

---

## Testing Strategy

### P0 Critical Testing

**OAuth2 Authentication**
- [ ] Unit tests: JWT encode/decode
- [ ] Integration tests: Login flow
- [ ] E2E tests: Protected endpoint access
- [ ] Security tests: Token expiry, invalid tokens

**Policy Engine**
- [ ] Unit tests: Policy evaluation logic
- [ ] Integration tests: OPA communication
- [ ] E2E tests: Tool access denial/approval
- [ ] Load tests: Policy decision latency

**Audit Service**
- [ ] Unit tests: Event logging
- [ ] Integration tests: Database writes
- [ ] E2E tests: Audit trail completeness
- [ ] Performance tests: High volume logging

### P1 High Testing

**Circuit Breaker**
- [ ] Unit tests: Threshold detection
- [ ] Integration tests: Recovery timeout
- [ ] Chaos tests: Simulate failures

**Response Shaping**
- [ ] Unit tests: Field selection
- [ ] Integration tests: Token reduction
- [ ] Performance tests: Shaping overhead

**Cache Service**
- [ ] Unit tests: Get/set operations
- [ ] Integration tests: Redis connectivity
- [ ] Load tests: Cache hit rate

---

## Success Metrics

### P0 Critical Completion
- [ ] All P0 gaps closed
- [ ] OAuth2 login working in Admin UI
- [ ] Policy decisions logged in audit trail
- [ ] Audit log viewer displaying data
- [ ] Client demo script updated

### P1 High Completion
- [ ] Circuit breaker preventing cascading failures
- [ ] Response sizes reduced by 50%+
- [ ] PII masked in all logs
- [ ] Cache hit rate > 40%
- [ ] Tool lifecycle management functional

### Overall Success
- [ ] All acceptance criteria met
- [ ] Documentation updated
- [ ] E2E demo script rehearsed
- [ ] Client presentation ready
- [ ] Production deployment plan documented

---

## Conclusion

This implementation plan addresses all gaps between the Phase 6 implementation and RFP requirements. By following this plan:

1. **Week 1**: Delivers P0 critical security and compliance features
2. **Week 2**: Adds P1 production resilience and performance
3. **Week 3** (optional): Enhances user experience with P2 features

**Recommendation**: Execute P0 critical items immediately to achieve **CLIENT ACCEPTANCE**. P1 and P2 can be phased in during production hardening.

---

**Next Steps**:
1. Review and approve this plan
2. Set up development environment for Week 1
3. Create feature branches for each gap
4. Begin Day 1: OAuth2 Backend implementation

---

**Document Control**:
- Created: January 31, 2026
- Author: Development Team
- Approver: [Pending]
- Version: 1.0
