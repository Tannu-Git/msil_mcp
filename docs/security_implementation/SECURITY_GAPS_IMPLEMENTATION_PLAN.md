# Security Gaps Implementation Plan

**Document Version**: 1.0  
**Date**: January 31, 2026  
**Status**: Planning  
**Based On**: security_expectations.txt analysis

---

## Executive Summary

This document outlines the implementation plan for closing critical security gaps identified in the current MSIL MCP Server architecture. All gaps are prioritized based on RFP requirements and production security standards.

**Total Effort**: 18 days (144 hours)  
**Critical Path**: P0 items must be completed before production deployment  

---

## Gap Priority Overview

| Priority | Gaps | Effort | Impact |
|----------|------|--------|--------|
| **P0 (Critical)** | 4 gaps | 8 days | BLOCKER for production |
| **P1 (High)** | 4 gaps | 6 days | Required for security compliance |
| **P2 (Medium)** | 4 gaps | 4 days | Production hardening |

---

## P0 Critical Gaps (Production Blockers)

### Gap P0-1: JWKS-Based Token Validation ⭐ HIGHEST PRIORITY

**Current State**: Simple JWT validation with shared secret (HS256)  
**Expected State**: OIDC-compliant JWT validation with JWKS, issuer/audience validation  
**Impact**: Cannot integrate with real IdP (Azure AD, Auth0, Cognito)  
**Effort**: 2 days (16 hours)

#### Implementation Details

**Files to Create**:
```
mcp-server/app/core/auth/
├── jwks_client.py          # JWKS fetching and caching
├── oidc_validator.py       # Full OIDC token validation
└── token_validator.py      # Enhanced token validation with claims
```

**Files to Modify**:
```
mcp-server/app/core/auth/jwt_handler.py    # Add JWKS support
mcp-server/app/core/auth/oauth2_provider.py # Use OIDC validator
mcp-server/app/config.py                   # Add OIDC settings
mcp-server/app/api/admin.py                # Add OIDC settings endpoints
admin-ui/src/pages/Settings.tsx            # Add OIDC config UI
```

#### Implementation Steps

**Hour 1-4: JWKS Client**
```python
# app/core/auth/jwks_client.py
import httpx
import time
from jose import jwk
from typing import Dict, Optional
from functools import lru_cache

class JWKSClient:
    """Client for fetching and caching JWKS from IdP."""
    
    def __init__(self, jwks_url: str, cache_ttl: int = 3600):
        self.jwks_url = jwks_url
        self.cache_ttl = cache_ttl
        self._cache: Optional[Dict] = None
        self._cache_time: float = 0
    
    async def get_signing_key(self, kid: str) -> Dict:
        """Get signing key for given kid (key ID)."""
        if self._is_cache_valid():
            return self._get_key_from_cache(kid)
        
        await self._refresh_cache()
        return self._get_key_from_cache(kid)
    
    async def _refresh_cache(self):
        """Fetch JWKS from IdP."""
        async with httpx.AsyncClient() as client:
            response = await client.get(self.jwks_url, timeout=10.0)
            response.raise_for_status()
            self._cache = response.json()
            self._cache_time = time.time()
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self._cache:
            return False
        return (time.time() - self._cache_time) < self.cache_ttl
    
    def _get_key_from_cache(self, kid: str) -> Dict:
        """Extract key from cached JWKS."""
        for key in self._cache.get("keys", []):
            if key.get("kid") == kid:
                return key
        raise ValueError(f"Key {kid} not found in JWKS")
```

**Hour 5-8: OIDC Token Validator**
```python
# app/core/auth/oidc_validator.py
from jose import jwt, jwk
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class OIDCTokenValidator:
    """Validates JWT tokens according to OIDC spec."""
    
    def __init__(
        self,
        jwks_client: JWKSClient,
        issuer: str,
        audience: str,
        required_scopes: Optional[List[str]] = None
    ):
        self.jwks_client = jwks_client
        self.issuer = issuer
        self.audience = audience
        self.required_scopes = required_scopes or []
    
    async def validate_token(self, token: str) -> Dict:
        """Validate JWT token with full OIDC compliance."""
        # 1. Decode header to get kid
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            raise ValueError("Token missing 'kid' in header")
        
        # 2. Get signing key from JWKS
        signing_key = await self.jwks_client.get_signing_key(kid)
        public_key = jwk.construct(signing_key)
        
        # 3. Verify and decode token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256", "RS384", "RS512"],
            audience=self.audience,
            issuer=self.issuer,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": True,
                "require_exp": True,
                "require_iat": True,
            }
        )
        
        # 4. Validate required scopes
        token_scopes = payload.get("scope", "").split()
        for required_scope in self.required_scopes:
            if required_scope not in token_scopes:
                raise ValueError(f"Missing required scope: {required_scope}")
        
        # 5. Validate nonce if present (anti-replay)
        if "nonce" in payload:
            # Store and check nonce in Redis/cache (implement separately)
            logger.debug(f"Nonce validation: {payload['nonce']}")
        
        logger.info(f"Token validated successfully for subject: {payload.get('sub')}")
        return payload
```

**Hour 9-12: Integration & Configuration**
```python
# app/config.py additions
class Settings(BaseSettings):
    # ... existing settings ...
    
    # OIDC Configuration
    OIDC_ENABLED: bool = False  # Enable OIDC validation
    OIDC_ISSUER: Optional[str] = None  # e.g., "https://login.microsoftonline.com/{tenant-id}/v2.0"
    OIDC_AUDIENCE: Optional[str] = None  # Client ID / API identifier
    OIDC_JWKS_URL: Optional[str] = None  # e.g., "{issuer}/.well-known/jwks.json"
    OIDC_REQUIRED_SCOPES: str = "openid,profile,email"  # Comma-separated
    OIDC_JWKS_CACHE_TTL: int = 3600  # 1 hour
    
    # Token validation
    TOKEN_VALIDATE_ISSUER: bool = True
    TOKEN_VALIDATE_AUDIENCE: bool = True
    TOKEN_VALIDATE_NONCE: bool = True
```

**Hour 13-16: Admin Portal Settings**
Add to Settings.tsx:
```typescript
// New category: OIDC Authentication
{
  title: "🔐 OIDC Authentication",
  settings: [
    {
      key: "authentication.oidc_enabled",
      label: "OIDC Enabled",
      value: settings.authentication?.oidc_enabled ?? false,
      type: "boolean",
      description: "Enable OpenID Connect authentication"
    },
    {
      key: "authentication.oidc_issuer",
      label: "OIDC Issuer URL",
      value: settings.authentication?.oidc_issuer ?? "",
      type: "text",
      description: "Identity Provider issuer URL"
    },
    {
      key: "authentication.oidc_audience",
      label: "OIDC Audience",
      value: settings.authentication?.oidc_audience ?? "",
      type: "text",
      description: "Expected audience (client ID)"
    },
    {
      key: "authentication.oidc_jwks_url",
      label: "JWKS URL",
      value: settings.authentication?.oidc_jwks_url ?? "",
      type: "text",
      description: "JSON Web Key Set endpoint"
    },
    {
      key: "authentication.oidc_required_scopes",
      label: "Required Scopes",
      value: settings.authentication?.oidc_required_scopes ?? "openid,profile",
      type: "text",
      description: "Comma-separated list of required scopes"
    }
  ]
}
```

#### Testing Requirements
- [ ] Test with Azure AD tokens
- [ ] Test with Auth0 tokens
- [ ] Test with expired tokens
- [ ] Test with invalid issuer
- [ ] Test with invalid audience
- [ ] Test with missing kid
- [ ] Test JWKS caching and refresh

#### Success Criteria
- ✅ Validates tokens from real OIDC provider
- ✅ Rejects tokens with invalid issuer/audience
- ✅ JWKS caching works (no fetch on every request)
- ✅ Settings configurable via Admin Portal

---

### Gap P0-2: Idempotency Keys for Write Operations ⭐ CRITICAL

**Current State**: No idempotency protection  
**Expected State**: Idempotency keys required for all write operations  
**Impact**: Risk of duplicate bookings, double charges  
**Effort**: 1 day (8 hours)

#### Implementation Details

**Files to Create**:
```
mcp-server/app/core/idempotency/
├── __init__.py
├── store.py                # Idempotency key storage (Redis)
└── middleware.py           # Idempotency middleware
```

**Files to Modify**:
```
mcp-server/app/core/tools/executor.py     # Add idempotency checks
mcp-server/app/api/mcp.py                 # Require idempotency header
mcp-server/app/config.py                  # Add idempotency settings
```

#### Implementation Steps

**Hour 1-4: Idempotency Store**
```python
# app/core/idempotency/store.py
import redis
import json
import hashlib
from typing import Optional, Dict, Any
from datetime import timedelta

class IdempotencyStore:
    """Store for idempotency keys with Redis backend."""
    
    def __init__(self, redis_client: redis.Redis, ttl_seconds: int = 86400):
        self.redis = redis_client
        self.ttl = ttl_seconds
    
    def _make_key(self, idempotency_key: str, user_id: str) -> str:
        """Create namespaced key."""
        return f"idempotency:{user_id}:{idempotency_key}"
    
    async def get_response(
        self,
        idempotency_key: str,
        user_id: str
    ) -> Optional[Dict[Any, Any]]:
        """Get cached response for idempotency key."""
        key = self._make_key(idempotency_key, user_id)
        data = self.redis.get(key)
        
        if data:
            return json.loads(data)
        return None
    
    async def store_response(
        self,
        idempotency_key: str,
        user_id: str,
        response: Dict[Any, Any]
    ):
        """Store response with idempotency key."""
        key = self._make_key(idempotency_key, user_id)
        self.redis.setex(
            key,
            self.ttl,
            json.dumps(response)
        )
    
    def generate_key(self, request_data: Dict) -> str:
        """Generate idempotency key from request data."""
        # Hash request payload for automatic key generation
        data_str = json.dumps(request_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
```

**Hour 5-8: Integration with Tool Executor**
```python
# app/core/tools/executor.py modifications
class ToolExecutor:
    def __init__(self, idempotency_store: Optional[IdempotencyStore] = None):
        # ... existing init ...
        self.idempotency_store = idempotency_store
    
    async def execute_with_idempotency(
        self,
        tool: Tool,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str],
        user_id: str,
        correlation_id: Optional[str] = None
    ) -> ToolExecutionResult:
        """Execute tool with idempotency protection."""
        
        # Check if this is a write operation
        is_write_operation = tool.http_method in ["POST", "PUT", "DELETE", "PATCH"]
        
        if is_write_operation:
            # Require idempotency key for writes
            if not idempotency_key:
                if settings.IDEMPOTENCY_REQUIRED:
                    raise ValueError("Idempotency-Key header required for write operations")
                # Generate key automatically if not required
                idempotency_key = self.idempotency_store.generate_key({
                    "tool": tool.name,
                    "params": parameters,
                    "user": user_id
                })
            
            # Check if we've seen this key before
            cached_response = await self.idempotency_store.get_response(
                idempotency_key,
                user_id
            )
            
            if cached_response:
                logger.info(f"Returning cached response for idempotency key: {idempotency_key}")
                return ToolExecutionResult(**cached_response)
        
        # Execute tool normally
        result = await self.execute(tool, parameters, correlation_id)
        
        # Cache result for write operations
        if is_write_operation and idempotency_key:
            await self.idempotency_store.store_response(
                idempotency_key,
                user_id,
                result.dict()
            )
        
        return result
```

#### Configuration Settings
```python
# app/config.py additions
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Idempotency
    IDEMPOTENCY_ENABLED: bool = True
    IDEMPOTENCY_REQUIRED: bool = True  # Require explicit keys vs auto-generate
    IDEMPOTENCY_TTL_SECONDS: int = 86400  # 24 hours
    IDEMPOTENCY_STORE_TYPE: str = "redis"  # redis or memory
```

#### Admin Portal Settings
```typescript
{
  title: "🔄 Idempotency Protection",
  settings: [
    {
      key: "transaction_safety.idempotency_enabled",
      label: "Idempotency Enabled",
      value: settings.transaction_safety?.idempotency_enabled ?? true,
      type: "boolean"
    },
    {
      key: "transaction_safety.idempotency_required",
      label: "Require Explicit Keys",
      value: settings.transaction_safety?.idempotency_required ?? false,
      type: "boolean",
      description: "Require clients to provide Idempotency-Key header"
    },
    {
      key: "transaction_safety.idempotency_ttl_seconds",
      label: "Cache TTL (seconds)",
      value: settings.transaction_safety?.idempotency_ttl_seconds ?? 86400,
      type: "number"
    }
  ]
}
```

#### Testing Requirements
- [ ] Test duplicate booking prevention
- [ ] Test idempotency key reuse within TTL
- [ ] Test idempotency key expiration
- [ ] Test auto-generation mode
- [ ] Test per-user key isolation

---

### Gap P0-3: PIM/PAM Integration for Privileged Operations ⭐ CRITICAL

**Current State**: No privileged access management  
**Expected State**: Step-up authentication for high-risk tools  
**Impact**: Unauthorized privileged operations possible  
**Effort**: 3 days (24 hours)

#### Implementation Details

**Files to Create**:
```
mcp-server/app/core/pim/
├── __init__.py
├── elevation_checker.py    # Check if user is elevated
├── approval_service.py     # Integration with PAM systems
└── models.py               # PIM/PAM data models
```

**Files to Modify**:
```
mcp-server/app/core/tools/registry.py     # Add requires_elevation flag
mcp-server/app/core/policy/engine.py      # Check elevation in policy
mcp-server/app/api/mcp.py                 # Add elevation endpoints
```

#### Implementation Steps

**Hour 1-8: Elevation Checker**
```python
# app/core/pim/elevation_checker.py
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx

class ElevationChecker:
    """Check if user has elevated privileges."""
    
    def __init__(
        self,
        pam_endpoint: Optional[str] = None,
        elevation_duration: int = 3600  # 1 hour default
    ):
        self.pam_endpoint = pam_endpoint
        self.elevation_duration = elevation_duration
        self._cache: Dict[str, datetime] = {}
    
    async def is_user_elevated(
        self,
        user_id: str,
        tool_name: str,
        token_claims: Dict[str, Any]
    ) -> bool:
        """Check if user has current elevation."""
        
        # Method 1: Check JWT claims for elevation
        elevation_claim = token_claims.get("elevation_status")
        if elevation_claim:
            return self._validate_elevation_claim(elevation_claim)
        
        # Method 2: Check with external PAM system
        if self.pam_endpoint:
            return await self._check_pam_elevation(user_id, tool_name)
        
        # Method 3: Check local cache (for demo mode)
        return self._check_cache_elevation(user_id)
    
    def _validate_elevation_claim(self, claim: Dict) -> bool:
        """Validate elevation from JWT claim."""
        elevated_at = claim.get("elevated_at")
        if not elevated_at:
            return False
        
        # Check if elevation is still valid
        elevated_time = datetime.fromisoformat(elevated_at)
        expiry = elevated_time + timedelta(seconds=self.elevation_duration)
        return datetime.utcnow() < expiry
    
    async def _check_pam_elevation(
        self,
        user_id: str,
        tool_name: str
    ) -> bool:
        """Check elevation with PAM system."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.pam_endpoint}/check-elevation",
                    json={
                        "user_id": user_id,
                        "resource": tool_name,
                        "action": "execute"
                    },
                    timeout=5.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("elevated", False)
        except Exception as e:
            logger.error(f"PAM elevation check failed: {e}")
            return False
    
    async def request_elevation(
        self,
        user_id: str,
        tool_name: str,
        reason: str
    ) -> Dict[str, Any]:
        """Request elevation (just-in-time access)."""
        # This would integrate with PAM system's approval workflow
        # For demo, return mock approval URL
        return {
            "approval_required": True,
            "approval_url": f"{self.pam_endpoint}/approve/{user_id}",
            "status": "pending"
        }
```

**Hour 9-16: Tool Risk Tagging**
```python
# app/core/tools/registry.py modifications
@dataclass
class Tool:
    # ... existing fields ...
    
    # Risk & elevation
    risk_level: str = "read"  # read, write, privileged
    requires_elevation: bool = False
    requires_approval: bool = False
    max_concurrent_executions: int = 10
    rate_limit_tier: str = "standard"  # standard, strict, permissive
```

**Hour 17-24: Policy Integration**
```python
# app/core/policy/engine.py modifications
async def evaluate(
    self,
    action: str,
    resource: str,
    context: Dict[str, Any]
) -> PolicyDecision:
    """Evaluate policy with elevation check."""
    
    # Get tool metadata
    tool = context.get("tool")
    
    # Check if elevation required
    if tool and tool.requires_elevation:
        user_id = context.get("user_id")
        token_claims = context.get("token_claims", {})
        
        is_elevated = await self.elevation_checker.is_user_elevated(
            user_id,
            tool.name,
            token_claims
        )
        
        if not is_elevated:
            return PolicyDecision(
                allowed=False,
                reason=f"Tool '{tool.name}' requires elevation. Use step-up authentication.",
                policies_evaluated=["elevation_required"],
                metadata={
                    "elevation_required": True,
                    "elevation_url": "/api/auth/elevate"
                }
            )
    
    # Continue with normal policy evaluation
    # ...
```

#### Configuration Settings
```python
# app/config.py additions
class Settings(BaseSettings):
    # ... existing settings ...
    
    # PIM/PAM Configuration
    PIM_ENABLED: bool = False
    PIM_PROVIDER: str = "local"  # local, azure_pim, cyberark
    PAM_ENDPOINT: Optional[str] = None
    ELEVATION_DURATION_SECONDS: int = 3600  # 1 hour
    ELEVATION_REQUIRE_REASON: bool = True
    ELEVATION_REQUIRE_APPROVAL: bool = False  # Require manager approval
```

#### Admin Portal Settings
```typescript
{
  title: "🔐 Privileged Access Management",
  settings: [
    {
      key: "pim.enabled",
      label: "PIM/PAM Enabled",
      value: settings.pim?.enabled ?? false,
      type: "boolean"
    },
    {
      key: "pim.provider",
      label: "PIM Provider",
      value: settings.pim?.provider ?? "local",
      type: "select",
      options: ["local", "azure_pim", "cyberark", "okta"]
    },
    {
      key: "pim.pam_endpoint",
      label: "PAM API Endpoint",
      value: settings.pim?.pam_endpoint ?? "",
      type: "text"
    },
    {
      key: "pim.elevation_duration_seconds",
      label: "Elevation Duration (seconds)",
      value: settings.pim?.elevation_duration_seconds ?? 3600,
      type: "number"
    },
    {
      key: "pim.require_approval",
      label: "Require Manager Approval",
      value: settings.pim?.require_approval ?? false,
      type: "boolean"
    }
  ]
}
```

#### Testing Requirements
- [ ] Test elevation check with valid elevation
- [ ] Test elevation denial for non-elevated users
- [ ] Test elevation expiration
- [ ] Test elevation request workflow
- [ ] Test privileged tool execution

---

### Gap P0-4: WORM Audit Storage (S3 Object Lock) ⭐ CRITICAL

**Current State**: Audit logs in mutable PostgreSQL  
**Expected State**: Immutable audit logs in S3 with Object Lock  
**Impact**: Audit logs can be tampered, non-compliant  
**Effort**: 2 days (16 hours)

#### Implementation Details

**Files to Create**:
```
mcp-server/app/core/audit/
└── s3_store.py             # S3 WORM storage implementation
```

**Files to Modify**:
```
mcp-server/app/core/audit/service.py      # Add S3 backend
mcp-server/app/config.py                  # Add S3 WORM settings
infrastructure/aws/terraform/main.tf      # Add S3 bucket with Object Lock
```

#### Implementation Steps

**Hour 1-8: S3 WORM Store**
```python
# app/core/audit/s3_store.py
import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import hashlib

class S3WORMStore:
    """Write-Once-Read-Many audit log storage using S3 Object Lock."""
    
    def __init__(
        self,
        bucket_name: str,
        region: str = "ap-south-1",
        retention_days: int = 365
    ):
        self.bucket_name = bucket_name
        self.retention_days = retention_days
        self.s3_client = boto3.client('s3', region_name=region)
    
    async def write_audit_event(self, event: AuditEvent) -> str:
        """Write audit event to S3 with Object Lock."""
        
        # Create immutable object key with date partitioning
        key = self._generate_key(event)
        
        # Serialize event
        event_data = self._serialize_event(event)
        
        # Calculate retention until date
        retention_until = datetime.utcnow() + timedelta(days=self.retention_days)
        
        # Write to S3 with Object Lock
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=event_data,
            ContentType='application/json',
            ObjectLockMode='GOVERNANCE',  # or COMPLIANCE for stricter control
            ObjectLockRetainUntilDate=retention_until,
            Metadata={
                'event_id': event.event_id,
                'event_type': event.event_type,
                'checksum': self._calculate_checksum(event_data)
            }
        )
        
        return key
    
    def _generate_key(self, event: AuditEvent) -> str:
        """Generate S3 key with date partitioning."""
        timestamp = event.timestamp
        return (
            f"audit-logs/"
            f"year={timestamp.year}/"
            f"month={timestamp.month:02d}/"
            f"day={timestamp.day:02d}/"
            f"{event.event_id}.json"
        )
    
    def _serialize_event(self, event: AuditEvent) -> str:
        """Serialize event to JSON."""
        return json.dumps({
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type,
            "correlation_id": event.correlation_id,
            "user_id": event.user_id,
            "tool_name": event.tool_name,
            "action": event.action,
            "status": event.status,
            "metadata": event.metadata
        }, indent=2)
    
    def _calculate_checksum(self, data: str) -> str:
        """Calculate SHA-256 checksum for integrity."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def verify_integrity(self, key: str) -> bool:
        """Verify audit log hasn't been tampered."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            data = response['Body'].read().decode()
            expected_checksum = response['Metadata'].get('checksum')
            actual_checksum = self._calculate_checksum(data)
            
            return expected_checksum == actual_checksum
        except Exception as e:
            logger.error(f"Integrity check failed: {e}")
            return False
```

**Hour 9-12: Terraform Configuration**
```hcl
# infrastructure/aws/terraform/modules/s3-audit/main.tf
resource "aws_s3_bucket" "audit_logs" {
  bucket = "${var.project_name}-${var.environment}-audit-logs"
  
  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-audit-logs"
      Compliance = "SOC2-Type2"
    }
  )
}

# Enable versioning (required for Object Lock)
resource "aws_s3_bucket_versioning" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# Enable Object Lock
resource "aws_s3_bucket_object_lock_configuration" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id
  
  rule {
    default_retention {
      mode = "GOVERNANCE"  # or COMPLIANCE
      days = var.retention_days
    }
  }
}

# Enable encryption at rest
resource "aws_s3_bucket_server_side_encryption_configuration" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.audit_logs.arn
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy
resource "aws_s3_bucket_lifecycle_configuration" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id
  
  rule {
    id     = "transition-to-glacier"
    status = "Enabled"
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    
    expiration {
      days = 730  # 2 years total retention
    }
  }
}
```

**Hour 13-16: Integration & Configuration**
```python
# app/config.py additions
class Settings(BaseSettings):
    # ... existing settings ...
    
    # S3 WORM Audit Storage
    AUDIT_S3_ENABLED: bool = False
    AUDIT_S3_BUCKET: Optional[str] = None
    AUDIT_S3_REGION: str = "ap-south-1"
    AUDIT_S3_OBJECT_LOCK_MODE: str = "GOVERNANCE"  # GOVERNANCE or COMPLIANCE
    AUDIT_S3_RETENTION_DAYS: int = 365
    AUDIT_DUAL_WRITE: bool = True  # Write to both DB and S3
```

#### Admin Portal Settings
```typescript
{
  title: "📦 Audit Storage (WORM)",
  settings: [
    {
      key: "audit.s3_enabled",
      label: "S3 WORM Storage Enabled",
      value: settings.audit?.s3_enabled ?? false,
      type: "boolean",
      description: "Enable immutable audit log storage in S3"
    },
    {
      key: "audit.s3_bucket",
      label: "S3 Bucket Name",
      value: settings.audit?.s3_bucket ?? "",
      type: "text"
    },
    {
      key: "audit.s3_object_lock_mode",
      label: "Object Lock Mode",
      value: settings.audit?.s3_object_lock_mode ?? "GOVERNANCE",
      type: "select",
      options: ["GOVERNANCE", "COMPLIANCE"]
    },
    {
      key: "audit.dual_write",
      label: "Dual Write (DB + S3)",
      value: settings.audit?.dual_write ?? true,
      type: "boolean"
    }
  ]
}
```

#### Testing Requirements
- [ ] Test S3 write with Object Lock
- [ ] Test deletion prevention (WORM)
- [ ] Test retention until date enforcement
- [ ] Test integrity verification
- [ ] Test lifecycle policy

---

## P1 High Priority Gaps

### Gap P1-1: WAF Configuration with OWASP Rules

**Effort**: 1 day (8 hours)  
**Impact**: Protection against L7 attacks

#### Implementation Plan
```hcl
# infrastructure/aws/terraform/modules/waf/main.tf
resource "aws_wafv2_web_acl" "mcp_waf" {
  name  = "${var.project_name}-${var.environment}-waf"
  scope = "REGIONAL"
  
  default_action {
    allow {}
  }
  
  # Rule 1: Rate limiting
  rule {
    name     = "rate-limit"
    priority = 1
    
    action {
      block {}
    }
    
    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name               = "RateLimitRule"
      sampled_requests_enabled  = true
    }
  }
  
  # Rule 2: AWS Managed Rules - Core Rule Set
  rule {
    name     = "aws-managed-rules-common"
    priority = 2
    
    override_action {
      none {}
    }
    
    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesCommonRuleSet"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name               = "AWSManagedRulesCommon"
      sampled_requests_enabled  = true
    }
  }
  
  # Rule 3: Known Bad Inputs
  rule {
    name     = "aws-managed-rules-known-bad-inputs"
    priority = 3
    
    override_action {
      none {}
    }
    
    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name               = "AWSManagedRulesKnownBadInputs"
      sampled_requests_enabled  = true
    }
  }
  
  # Rule 4: SQL Injection Protection
  rule {
    name     = "aws-managed-rules-sql-injection"
    priority = 4
    
    override_action {
      none {}
    }
    
    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesSQLiRuleSet"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name               = "AWSManagedRulesSQLi"
      sampled_requests_enabled  = true
    }
  }
  
  # Rule 5: IP Allowlist (Optional)
  dynamic "rule" {
    for_each = var.ip_allowlist_enabled ? [1] : []
    
    content {
      name     = "ip-allowlist"
      priority = 5
      
      action {
        allow {}
      }
      
      statement {
        ip_set_reference_statement {
          arn = aws_wafv2_ip_set.allowlist[0].arn
        }
      }
      
      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name               = "IPAllowlist"
        sampled_requests_enabled  = true
      }
    }
  }
}

# IP Set for allowlist
resource "aws_wafv2_ip_set" "allowlist" {
  count = var.ip_allowlist_enabled ? 1 : 0
  
  name               = "${var.project_name}-ip-allowlist"
  scope              = "REGIONAL"
  ip_address_version = "IPV4"
  addresses          = var.allowed_ips
}
```

#### Settings
```python
# config.py
WAF_ENABLED: bool = False
WAF_RATE_LIMIT: int = 2000
WAF_IP_ALLOWLIST_ENABLED: bool = False
WAF_ALLOWED_IPS: str = ""  # Comma-separated
```

---

### Gap P1-2: mTLS Between Services

**Effort**: 2 days (16 hours)  
**Impact**: Secure service-to-service communication

#### Implementation Plan
```python
# app/core/mtls/certificate_manager.py
import ssl
from pathlib import Path

class MTLSConfig:
    """Mutual TLS configuration."""
    
    def __init__(
        self,
        ca_cert_path: str,
        client_cert_path: str,
        client_key_path: str,
        verify_mode: int = ssl.CERT_REQUIRED
    ):
        self.ca_cert = Path(ca_cert_path)
        self.client_cert = Path(client_cert_path)
        self.client_key = Path(client_key_path)
        self.verify_mode = verify_mode
    
    def create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for mTLS."""
        context = ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH,
            cafile=str(self.ca_cert)
        )
        context.load_cert_chain(
            certfile=str(self.client_cert),
            keyfile=str(self.client_key)
        )
        context.verify_mode = self.verify_mode
        context.check_hostname = True
        return context
```

#### Settings
```python
MTLS_ENABLED: bool = False
MTLS_CA_CERT_PATH: str = "/certs/ca.crt"
MTLS_CLIENT_CERT_PATH: str = "/certs/client.crt"
MTLS_CLIENT_KEY_PATH: str = "/certs/client.key"
```

---

### Gap P1-3: Tool Risk Tagging & Differentiated Enforcement

**Effort**: 1 day (8 hours)

Already partially covered in Gap P0-3. Additional implementation:

```python
# Enhanced Tool model with risk attributes
@dataclass
class Tool:
    # ... existing fields ...
    risk_level: str = "read"  # read, write, privileged
    rate_limit_tier: str = "standard"  # permissive, standard, strict
    pii_policy: str = "mask"  # none, mask, redact, block
    max_concurrency: int = 10
    timeout_seconds: int = 30
```

---

### Gap P1-4: Dedicated APIM Subscription

**Effort**: 1 day (8 hours)

Configuration and documentation for setting up separate APIM subscription:

```python
# config.py
APIM_MCP_SUBSCRIPTION_KEY: Optional[str] = None
APIM_MCP_SUBSCRIPTION_NAME: str = "mcp-channel"
APIM_PROPAGATE_USER_CONTEXT: bool = True
APIM_USER_CONTEXT_HEADER: str = "X-User-Context"
```

---

## P2 Medium Priority Gaps

### Gap P2-1: Container Hardening

**Effort**: 3 days (24 hours)

Update Dockerfiles:
```dockerfile
# Use non-root user
USER 1000:1000

# Read-only root filesystem
RUN mkdir -p /tmp && chmod 1777 /tmp
VOLUME /tmp

# Drop capabilities
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE
```

---

### Gap P2-2: Security Test Suite

**Effort**: 3 days (24 hours)

Create comprehensive security tests:
```python
# tests/security/test_unauthorized_access.py
# tests/security/test_schema_fuzzing.py
# tests/security/test_prompt_injection.py
# tests/security/test_rate_limiting.py
```

---

## Admin Portal Settings Summary

### New Settings Categories

```typescript
// Total new settings to add to Admin Portal:

1. OIDC Authentication (5 settings)
2. Idempotency Protection (3 settings)
3. PIM/PAM (5 settings)
4. S3 WORM Audit Storage (4 settings)
5. WAF Configuration (3 settings)
6. mTLS Configuration (4 settings)
7. Tool Risk Management (4 settings)
8. APIM Integration (3 settings)

Total: 31 new security settings
```

---

## Implementation Timeline

### Week 1: P0 Critical Gaps
- **Days 1-2**: JWKS Token Validation
- **Day 3**: Idempotency Keys
- **Days 4-6**: PIM/PAM Integration
- **Days 7-8**: WORM Audit Storage

### Week 2: P1 High Priority
- **Day 9**: WAF Configuration
- **Days 10-11**: mTLS Between Services
- **Day 12**: Tool Risk Tagging
- **Day 13**: APIM Subscription Setup
- **Day 14**: Testing & Integration

### Week 3-4: P2 Medium Priority
- Container hardening
- Security test suite
- Network policies
- Documentation

---

## Success Metrics

### Security Posture
- [ ] 100% of JWT tokens validated with JWKS
- [ ] 0 duplicate transactions (idempotency working)
- [ ] 100% of privileged operations require elevation
- [ ] 100% of audit logs in immutable storage
- [ ] WAF blocking >99% of malicious requests

### Compliance
- [ ] SOC2 Type 2 ready
- [ ] GDPR compliant (PII protection)
- [ ] Audit trail tamper-evident
- [ ] 12-month retention enforced

### Admin Portal
- [ ] All 31 security settings configurable
- [ ] Settings validated before apply
- [ ] Settings audit trail maintained
- [ ] Settings export/import capability

---

## Dependencies & Prerequisites

### Infrastructure
- AWS account with appropriate permissions
- S3 bucket with Object Lock capability
- Redis for idempotency store
- Certificate authority for mTLS

### Third-Party Services
- OIDC provider (Azure AD, Auth0, Cognito)
- Optional: PAM system (CyberArk, Okta)
- Optional: WAF service

### Team Skills
- AWS services (S3, WAF, KMS)
- OAuth2/OIDC protocols
- Certificate management
- Terraform infrastructure as code

---

## Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| OIDC provider integration complexity | High | Start with one provider, expand later |
| S3 Object Lock cost | Medium | Use lifecycle policies, archive old logs |
| PIM/PAM system availability | Medium | Implement local fallback mode |
| Certificate management overhead | Low | Use AWS Certificate Manager |

---

## Conclusion

This implementation plan addresses all critical security gaps identified in the security_expectations.txt analysis. Priority is given to production-blocking items (P0), followed by compliance requirements (P1), and hardening measures (P2).

**Total Effort**: 18 days for full implementation  
**Critical Path**: P0 items (8 days) must complete before production  
**Admin Portal**: 31 new settings to expose all security configurations

All settings will be configurable via the Admin Portal, maintaining the principle of centralized configuration management established in the current system.
