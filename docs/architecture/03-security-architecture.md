# Security Architecture

**Document Version**: 2.1  
**Last Updated**: February 1, 2026  
**Classification**: Confidential

---

## 1. Security Architecture Overview

This document describes the comprehensive security architecture covering IAM/RBAC, OAuth2/OIDC integration, PIM/PAM workflows, prompt injection guardrails, and data protection compliance.

**Important**: The MCP Server integrates with **MSIL IdP** (OIDC-compliant identity provider) for authentication. All vendor-specific references (e.g., Azure AD) are placeholders—the actual IdP is configurable and determined by MSIL's infrastructure team.

---

## 2. Defense-in-Depth Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              DEFENSE-IN-DEPTH SECURITY LAYERS                            │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │ LAYER 1: PERIMETER SECURITY                                                     │   │
│   │                                                                                 │   │
│   │   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐               │   │
│   │   │    AWS    │   │   Network │   │   TLS     │   │   DDoS    │               │   │
│   │   │    WAF    │   │   ACLs    │   │  1.2/1.3  │   │  Shield   │               │   │
│   │   │           │   │           │   │           │   │           │               │   │
│   │   │ • OWASP   │   │ • VPC     │   │ • mTLS    │   │ • Rate    │               │   │
│   │   │   Rules   │   │ • Subnets │   │   for API │   │   Limiting│               │   │
│   │   │ • Custom  │   │ • NACLs   │   │ • Cert    │   │ • AWS     │               │   │
│   │   │   Rules   │   │ • SecGrp  │   │   Pinning │   │   Shield  │               │   │
│   │   └───────────┘   └───────────┘   └───────────┘   └───────────┘               │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │ LAYER 2: IDENTITY & ACCESS                                                      │   │
│   │                                                                                 │   │
│   │   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐               │   │
│   │   │   OAuth   │   │   JWKS    │   │   RBAC    │   │  PIM/PAM  │               │   │
│   │   │   2.0     │   │   Verify  │   │   (OPA)   │   │  Elevate  │               │   │
│   │   │           │   │           │   │           │   │           │               │   │
│   │   │ • OIDC    │   │ • Remote  │   │ • Role    │   │ • JIT     │               │   │
│   │   │   Flow    │   │   JWKS    │   │   Policies│   │   Access  │               │   │
│   │   │ • Token   │   │ • Key     │   │ • Custom  │   │ • Time    │               │   │
│   │   │   Refresh │   │   Rotation│   │   Rules   │   │   Bound   │               │   │
│   │   └───────────┘   └───────────┘   └───────────┘   └───────────┘               │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │ LAYER 3: APPLICATION SECURITY                                                   │   │
│   │                                                                                 │   │
│   │   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐               │   │
│   │   │  Input    │   │  Prompt   │   │   Tool    │   │   Audit   │               │   │
│   │   │ Validate  │   │  Guards   │   │   Risk    │   │  Logging  │               │   │
│   │   │           │   │           │   │  Tagging  │   │           │               │   │
│   │   │ • Schema  │   │ • Pattern │   │ • read    │   │ • S3 WORM │               │   │
│   │   │ • Inject  │   │   Detect  │   │ • write   │   │ • Checksum│               │   │
│   │   │   Detect  │   │ • Block   │   │ • priv    │   │ • Tamper  │               │   │
│   │   │ • Allowli │   │   Malici  │   │           │   │   Proof   │               │   │
│   │   └───────────┘   └───────────┘   └───────────┘   └───────────┘               │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │ LAYER 4: DATA SECURITY                                                          │   │
│   │                                                                                 │   │
│   │   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐               │   │
│   │   │Encryption │   │   PII     │   │   Data    │   │   Backup  │               │   │
│   │   │  at Rest  │   │  Masking  │   │ Classifi- │   │   Encrypt │               │   │
│   │   │           │   │           │   │  cation   │   │           │               │   │
│   │   │ • AES-256 │   │ • Dyna-   │   │ • Public  │   │ • KMS     │               │   │
│   │   │ • KMS     │   │   mic     │   │ • Internal│   │   Keys    │               │   │
│   │   │   Managed │   │ • Role    │   │ • Conf    │   │ • Cross   │               │   │
│   │   │           │   │   Based   │   │ • Secret  │   │   Region  │               │   │
│   │   └───────────┘   └───────────┘   └───────────┘   └───────────┘               │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Authentication Architecture

### 3.1 OAuth2/OIDC Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              OAUTH2/OIDC AUTHENTICATION FLOW                             │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐                   │
│   │   User   │      │  Client  │      │ MCP Auth │      │  MSIL    │                   │
│   │ Browser  │      │   App    │      │  Server  │      │   IdP    │                   │
│   └────┬─────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘                   │
│        │                 │                 │                 │                          │
│        │  1. Login       │                 │                 │                          │
│        │────────────────▶│                 │                 │                          │
│        │                 │                 │                 │                          │
│        │                 │ 2. Auth Request │                 │                          │
│        │                 │ (PKCE + state)  │                 │                          │
│        │                 │────────────────▶│                 │                          │
│        │                 │                 │                 │                          │
│        │                 │                 │ 3. Redirect to  │                          │
│        │◀────────────────┼─────────────────│    /authorize   │                          │
│        │                 │                 │────────────────▶│                          │
│        │                 │                 │                 │                          │
│        │                 │                 │                 │                          │
│        │       4. User authenticates with MSIL IdP           │                          │
│        │─────────────────────────────────────────────────────▶                          │
│        │                 │                 │                 │                          │
│        │◀────────────────────────────────────────────────────│                          │
│        │       5. Auth code + state        │                 │                          │
│        │                 │                 │                 │                          │
│        │────────────────▶│                 │                 │                          │
│        │ 6. Code to app  │                 │                 │                          │
│        │                 │ 7. Exchange code│                 │                          │
│        │                 │────────────────▶│                 │                          │
│        │                 │                 │                 │                          │
│        │                 │                 │ 8. Token request│                          │
│        │                 │                 │    + PKCE verif │                          │
│        │                 │                 │────────────────▶│                          │
│        │                 │                 │                 │                          │
│        │                 │                 │◀────────────────│                          │
│        │                 │                 │ 9. Access token │                          │
│        │                 │                 │    + ID token   │                          │
│        │                 │                 │    + Refresh    │                          │
│        │                 │                 │                 │                          │
│        │                 │ 10. JWKS Verify │                 │                          │
│        │                 │    (Remote)     │                 │                          │
│        │                 │                 │────────────────▶│                          │
│        │                 │                 │◀────────────────│                          │
│        │                 │                 │    Public Keys  │                          │
│        │                 │                 │                 │                          │
│        │                 │◀────────────────│                 │                          │
│        │                 │ 11. Session +   │                 │                          │
│        │                 │     App token   │                 │                          │
│        │                 │                 │                 │                          │
│        │◀────────────────│                 │                 │                          │
│        │ 12. Authenticated                 │                 │                          │
│        │     session                       │                 │                          │
│        │                 │                 │                 │                          │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 JWKS Validation

```python
# JWKS Client Configuration (configurable for MSIL IdP)
class JWKSConfig:
    jwks_uri: str = "<MSIL_IDP_JWKS_ENDPOINT>"  # e.g., "https://idp.msil.com/.well-known/jwks.json"
    cache_ttl: int = 3600  # 1 hour
    expected_issuer: str = "<MSIL_IDP_ISSUER>"  # e.g., "https://idp.msil.com"
    expected_audience: str = "<MSIL_MCP_API_AUDIENCE>"  # e.g., "api://msil-mcp-server"
    algorithms: list = ["RS256"]
    
# Token Validation Process
def validate_token(token: str) -> dict:
    # 1. Decode header (no verification)
    header = jwt.get_unverified_header(token)
    kid = header["kid"]
    
    # 2. Fetch JWKS (cached)
    jwks = fetch_jwks_cached()
    
    # 3. Find matching key
    key = find_key_by_kid(jwks, kid)
    
    # 4. Verify signature and claims
    payload = jwt.decode(
        token,
        key=key,
        algorithms=["RS256"],
        audience=expected_audience,
        issuer=expected_issuer,
        options={"require": ["exp", "iat", "sub", "aud", "iss"]}
    )
    
    return payload
```

---

## 4. Authorization Architecture

### 4.1 RBAC with OPA

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              RBAC AUTHORIZATION WITH OPA                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           OPA POLICY ENGINE                                     │   │
│   │                                                                                 │   │
│   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │ Policy Definition (Rego)                                                │   │   │
│   │   │                                                                         │   │   │
│   │   │ package msil.authz                                                      │   │   │
│   │   │                                                                         │   │   │
│   │   │ # Default deny                                                          │   │   │
│   │   │ default allow = false                                                   │   │   │
│   │   │                                                                         │   │   │
│   │   │ # Role-based access                                                     │   │   │
│   │   │ allow {                                                                 │   │   │
│   │   │     user_role := input.user.role                                        │   │   │
│   │   │     tool_name := input.tool.name                                        │   │   │
│   │   │     tool_risk := input.tool.risk_level                                  │   │   │
│   │   │                                                                         │   │   │
│   │   │     role_can_access_risk[user_role][tool_risk]                          │   │   │
│   │   │     tool_allowed_for_role[tool_name][user_role]                         │   │   │
│   │   │ }                                                                       │   │   │
│   │   │                                                                         │   │   │
│   │   │ # Risk-based role permissions                                           │   │   │
│   │   │ role_can_access_risk = {                                                │   │   │
│   │   │     "viewer": {"read": true},                                           │   │   │
│   │   │     "operator": {"read": true, "write": true},                          │   │   │
│   │   │     "admin": {"read": true, "write": true, "privileged": true}          │   │   │
│   │   │ }                                                                       │   │   │
│   │   │                                                                         │   │   │
│   │   └─────────────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                               │
│                                         ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        AUTHORIZATION DECISION FLOW                              │   │
│   │                                                                                 │   │
│   │   Request ──▶ Extract ──▶ Build Input ──▶ Query OPA ──▶ Allow/Deny            │   │
│   │               Token        Document        Policy       Decision               │   │
│   │                                                                                 │   │
│   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │ Input Document Example:                                                 │   │   │
│   │   │                                                                         │   │   │
│   │   │ {                                                                       │   │   │
│   │   │   "user": {                                                             │   │   │
│   │   │     "id": "user@msil.com",                                              │   │   │
│   │   │     "role": "operator",                                                 │   │   │
│   │   │     "groups": ["dealer-ops", "regional-north"],                         │   │   │
│   │   │     "elevated": false                                                   │   │   │
│   │   │   },                                                                    │   │   │
│   │   │   "tool": {                                                             │   │   │
│   │   │     "name": "update_dealer_status",                                     │   │   │
│   │   │     "risk_level": "write",                                              │   │   │
│   │   │     "domain": "dealer",                                                 │   │   │
│   │   │     "requires_elevation": false                                         │   │   │
│   │   │   },                                                                    │   │   │
│   │   │   "context": {                                                          │   │   │
│   │   │     "ip_address": "10.0.1.100",                                         │   │   │
│   │   │     "timestamp": "2026-01-31T10:30:00Z"                                 │   │   │
│   │   │   }                                                                     │   │   │
│   │   │ }                                                                       │   │   │
│   │   │                                                                         │   │   │
│   │   └─────────────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Role Hierarchy

| Role | Read Tools | Write Tools | Privileged Tools | Admin Functions |
|------|-----------|-------------|------------------|-----------------|
| `viewer` | ✅ | ❌ | ❌ | ❌ |
| `operator` | ✅ | ✅ | ❌ | ❌ |
| `admin` | ✅ | ✅ | ✅ (with PIM) | ✅ |
| `superadmin` | ✅ | ✅ | ✅ | ✅ |

---

## 5. PIM/PAM Integration

### 5.1 Just-in-Time Access Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              PIM/PAM JUST-IN-TIME ACCESS                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐                   │
│   │   User   │      │   MCP    │      │   PIM    │      │ Approver │                   │
│   │          │      │  Server  │      │ System   │      │          │                   │
│   └────┬─────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘                   │
│        │                 │                 │                 │                          │
│        │ 1. Request      │                 │                 │                          │
│        │ privileged tool │                 │                 │                          │
│        │────────────────▶│                 │                 │                          │
│        │                 │                 │                 │                          │
│        │                 │ 2. Check role   │                 │                          │
│        │                 │    & elevation  │                 │                          │
│        │                 │────────────────▶│                 │                          │
│        │                 │                 │                 │                          │
│        │                 │◀────────────────│                 │                          │
│        │                 │ 3. Elevation    │                 │                          │
│        │                 │    required     │                 │                          │
│        │                 │                 │                 │                          │
│        │◀────────────────│                 │                 │                          │
│        │ 4. Return       │                 │                 │                          │
│        │ elevation URL   │                 │                 │                          │
│        │                 │                 │                 │                          │
│        │────────────────────────────────────▶                │                          │
│        │ 5. Submit elevation request        │                │                          │
│        │    + justification                 │                │                          │
│        │                 │                 │                 │                          │
│        │                 │                 │─────────────────▶                          │
│        │                 │                 │ 6. Approval     │                          │
│        │                 │                 │    request      │                          │
│        │                 │                 │                 │                          │
│        │                 │                 │◀────────────────│                          │
│        │                 │                 │ 7. Approved     │                          │
│        │                 │                 │    (or auto)    │                          │
│        │                 │                 │                 │                          │
│        │◀───────────────────────────────────│                │                          │
│        │ 8. Elevated token (TTL: 60 min)   │                 │                          │
│        │                 │                 │                 │                          │
│        │ 9. Retry tool   │                 │                 │                          │
│        │ + elevated token│                 │                 │                          │
│        │────────────────▶│                 │                 │                          │
│        │                 │                 │                 │                          │
│        │                 │ 10. Verify      │                 │                          │
│        │                 │     elevation   │                 │                          │
│        │                 │────────────────▶│                 │                          │
│        │                 │                 │                 │                          │
│        │                 │◀────────────────│                 │                          │
│        │                 │ 11. Valid       │                 │                          │
│        │                 │                 │                 │                          │
│        │                 │ 12. Execute     │                 │                          │
│        │◀────────────────│     tool        │                 │                          │
│        │ 13. Result      │                 │                 │                          │
│        │                 │                 │                 │                          │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │ AUDIT LOGGED AT EVERY STEP:                                                     │   │
│   │ • Elevation request submitted (who, what, why, when)                            │   │
│   │ • Approval decision (by whom, time taken)                                       │   │
│   │ • Elevated session created (TTL, scope)                                         │   │
│   │ • Privileged tool executed (correlation ID)                                     │   │
│   │ • Session expiry or revocation                                                  │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Tool Risk Classification

### 6.1 Risk Levels and Controls

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              TOOL RISK CLASSIFICATION                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │ READ (Low Risk)                                                                 │   │
│   │                                                                                 │   │
│   │   Characteristics:                                                              │   │
│   │   • No data modification                                                        │   │
│   │   • Query operations only                                                       │   │
│   │   • No financial impact                                                         │   │
│   │                                                                                 │   │
│   │   Controls:                                                                     │   │
│   │   ✅ Basic authentication                                                       │   │
│   │   ✅ Role-based access (viewer+)                                                │   │
│   │   ✅ Standard rate limiting                                                     │   │
│   │   ✅ Audit logging                                                              │   │
│   │                                                                                 │   │
│   │   Examples:                                                                     │   │
│   │   • get_dealer_enquiries                                                        │   │
│   │   • list_vehicle_inventory                                                      │   │
│   │   • get_customer_profile (masked PII)                                           │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │ WRITE (Medium Risk)                                                             │   │
│   │                                                                                 │   │
│   │   Characteristics:                                                              │   │
│   │   • Creates or modifies data                                                    │   │
│   │   • Status changes                                                              │   │
│   │   • Reversible operations                                                       │   │
│   │                                                                                 │   │
│   │   Controls:                                                                     │   │
│   │   ✅ All READ controls                                                          │   │
│   │   ✅ Operator role required                                                     │   │
│   │   ✅ Idempotency keys enforced                                                  │   │
│   │   ✅ Input validation (strict)                                                  │   │
│   │   ✅ Confirmation prompts (UI)                                                  │   │
│   │                                                                                 │   │
│   │   Examples:                                                                     │   │
│   │   • update_enquiry_status                                                       │   │
│   │   • create_booking                                                              │   │
│   │   • assign_dealer                                                               │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │ PRIVILEGED (High Risk)                                                          │   │
│   │                                                                                 │   │
│   │   Characteristics:                                                              │   │
│   │   • Financial transactions                                                      │   │
│   │   • Irreversible operations                                                     │   │
│   │   • Sensitive data access                                                       │   │
│   │   • Admin functions                                                             │   │
│   │                                                                                 │   │
│   │   Controls:                                                                     │   │
│   │   ✅ All WRITE controls                                                         │   │
│   │   ✅ Admin role required                                                        │   │
│   │   ✅ PIM/PAM elevation mandatory                                                │   │
│   │   ✅ Multi-party approval (optional)                                            │   │
│   │   ✅ Time-bound access (60 min max)                                             │   │
│   │   ✅ Enhanced audit logging                                                     │   │
│   │                                                                                 │   │
│   │   Examples:                                                                     │   │
│   │   • process_refund                                                              │   │
│   │   • delete_customer_data                                                        │   │
│   │   • bulk_price_update                                                           │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Prompt Injection Guardrails

### 7.1 Detection Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              PROMPT INJECTION GUARDRAILS                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        DETECTION PIPELINE                                       │   │
│   │                                                                                 │   │
│   │   User Input                                                                    │   │
│   │       │                                                                         │   │
│   │       ▼                                                                         │   │
│   │   ┌───────────────────────────────────────────────────────────────────────┐     │   │
│   │   │ STAGE 1: Pattern Matching                                             │     │   │
│   │   │                                                                       │     │   │
│   │   │ Regex patterns for known injection attempts:                          │     │   │
│   │   │ • "ignore previous instructions"                                      │     │   │
│   │   │ • "system:", "assistant:", "user:" markers                            │     │   │
│   │   │ • "DAN", "jailbreak", "roleplay as"                                   │     │   │
│   │   │ • Base64/encoding attempts                                            │     │   │
│   │   │ • Unicode homoglyph attacks                                           │     │   │
│   │   │                                                                       │     │   │
│   │   │ Action: Block if match confidence > 80%                               │     │   │
│   │   └───────────────────────────────────────────────────────────────────────┘     │   │
│   │       │                                                                         │   │
│   │       ▼                                                                         │   │
│   │   ┌───────────────────────────────────────────────────────────────────────┐     │   │
│   │   │ STAGE 2: Structural Analysis                                          │     │   │
│   │   │                                                                       │     │   │
│   │   │ Analyze input structure for:                                          │     │   │
│   │   │ • Excessive special characters                                        │     │   │
│   │   │ • Unusual character sequences                                         │     │   │
│   │   │ • Embedded code blocks                                                │     │   │
│   │   │ • Multiple nested instructions                                        │     │   │
│   │   │                                                                       │     │   │
│   │   │ Action: Flag for review if anomaly score > 0.6                        │     │   │
│   │   └───────────────────────────────────────────────────────────────────────┘     │   │
│   │       │                                                                         │   │
│   │       ▼                                                                         │   │
│   │   ┌───────────────────────────────────────────────────────────────────────┐     │   │
│   │   │ STAGE 3: Semantic Analysis (Optional - Azure AI)                      │     │   │
│   │   │                                                                       │     │   │
│   │   │ ML-based classification:                                              │     │   │
│   │   │ • Intent classification                                               │     │   │
│   │   │ • Sentiment analysis                                                  │     │   │
│   │   │ • Toxicity detection                                                  │     │   │
│   │   │                                                                       │     │   │
│   │   │ Action: Block if malicious intent detected                            │     │   │
│   │   └───────────────────────────────────────────────────────────────────────┘     │   │
│   │       │                                                                         │   │
│   │       ▼                                                                         │   │
│   │   Clean Input → Continue Processing                                             │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        MITIGATION STRATEGIES                                    │   │
│   │                                                                                 │   │
│   │   1. Input Sanitization                                                         │   │
│   │      • Strip control characters                                                 │   │
│   │      • Normalize unicode                                                        │   │
│   │      • Length limits (10,000 chars max)                                         │   │
│   │                                                                                 │   │
│   │   2. Context Isolation                                                          │   │
│   │      • Separate user input from system prompts                                  │   │
│   │      • Use delimiters: <user_input>...</user_input>                             │   │
│   │      • Never reflect raw input to LLM                                           │   │
│   │                                                                                 │   │
│   │   3. Output Validation                                                          │   │
│   │      • Verify tool calls match allowed set                                      │   │
│   │      • Check parameters against schema                                          │   │
│   │      • Block unexpected tool sequences                                          │   │
│   │                                                                                 │   │
│   │   4. Monitoring & Response                                                      │   │
│   │      • Log all blocked attempts                                                 │   │
│   │      • Alert on patterns (5+ blocks/user)                                       │   │
│   │      • Temporary ban on repeated violations                                     │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Audit & Compliance

### 8.1 Immutable Audit Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              IMMUTABLE AUDIT ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        S3 WORM (Write Once Read Many)                           │   │
│   │                                                                                 │   │
│   │   ┌───────────────────────────────────────────────────────────────────────┐     │   │
│   │   │                    Audit Event Flow                                   │     │   │
│   │   │                                                                       │     │   │
│   │   │   Event ──▶ Build ──▶ Calculate ──▶ Write to ──▶ Verify              │     │   │
│   │   │   Occurs    Record   Checksum      S3 WORM     Integrity             │     │   │
│   │   │                      (SHA-256)                                        │     │   │
│   │   │                                                                       │     │   │
│   │   └───────────────────────────────────────────────────────────────────────┘     │   │
│   │                                                                                 │   │
│   │   S3 Configuration:                                                             │   │
│   │   • Object Lock Mode: GOVERNANCE                                                │   │
│   │   • Retention Period: 7 years (configurable)                                    │   │
│   │   • Versioning: Enabled                                                         │   │
│   │   • Server-Side Encryption: AES-256 (KMS)                                       │   │
│   │                                                                                 │   │
│   │   Audit Record Structure:                                                       │   │
│   │   ┌───────────────────────────────────────────────────────────────────────┐     │   │
│   │   │ {                                                                     │     │   │
│   │   │   "event_id": "uuid",                                                 │     │   │
│   │   │   "timestamp": "ISO-8601",                                            │     │   │
│   │   │   "correlation_id": "uuid",                                           │     │   │
│   │   │   "actor": {                                                          │     │   │
│   │   │     "user_id": "user@msil.com",                                       │     │   │
│   │   │     "ip_address": "10.0.1.100",                                       │     │   │
│   │   │     "user_agent": "..."                                               │     │   │
│   │   │   },                                                                  │     │   │
│   │   │   "action": "tool_execution",                                         │     │   │
│   │   │   "resource": {                                                       │     │   │
│   │   │     "type": "tool",                                                   │     │   │
│   │   │     "name": "get_dealer_enquiries"                                    │     │   │
│   │   │   },                                                                  │     │   │
│   │   │   "outcome": "success",                                               │     │   │
│   │   │   "metadata": {...},                                                  │     │   │
│   │   │   "checksum": "sha256:abc123..."                                      │     │   │
│   │   │ }                                                                     │     │   │
│   │   └───────────────────────────────────────────────────────────────────────┘     │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        INTEGRITY VERIFICATION                                   │   │
│   │                                                                                 │   │
│   │   Daily Integrity Check:                                                        │   │
│   │   1. List all audit files from past 24 hours                                    │   │
│   │   2. For each file: download and recalculate checksum                           │   │
│   │   3. Compare calculated vs. stored checksum                                     │   │
│   │   4. Alert if any mismatch detected                                             │   │
│   │   5. Generate integrity report                                                  │   │
│   │                                                                                 │   │
│   │   Tamper Detection Alerts:                                                      │   │
│   │   • Immediate PagerDuty alert                                                   │   │
│   │   • Security team notification                                                  │   │
│   │   • Incident ticket auto-created                                                │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Data Protection Compliance

### 9.1 DPDP Act 2023 Compliance

| Requirement | Implementation |
|-------------|----------------|
| Consent Management | Explicit consent captured before data processing |
| Purpose Limitation | Data used only for stated purposes in tool definition |
| Data Minimization | Collect only required fields; mask unnecessary PII |
| Storage Limitation | Configurable retention policies; auto-deletion |
| Data Subject Rights | APIs for access, correction, deletion requests |
| Cross-Border Transfer | Data residency in India (AWS Mumbai region) |
| Breach Notification | 72-hour notification workflow |

### 9.2 PII Handling

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              PII HANDLING ARCHITECTURE                                   │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        DATA CLASSIFICATION                                      │   │
│   │                                                                                 │   │
│   │   Level 1: Public                Level 2: Internal                              │   │
│   │   • Marketing content            • Business reports                             │   │
│   │   • Product catalogs             • Aggregated analytics                         │   │
│   │                                                                                 │   │
│   │   Level 3: Confidential          Level 4: Restricted                            │   │
│   │   • Customer PII                 • Financial data                               │   │
│   │   • Dealer contracts             • Authentication secrets                       │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        PII MASKING RULES                                        │   │
│   │                                                                                 │   │
│   │   Field              Original              Masked                               │   │
│   │   ───────────────    ──────────────        ──────────────                       │   │
│   │   Phone              +91 98765 43210       +91 98***43210                        │   │
│   │   Email              john@example.com      j***@example.com                      │   │
│   │   PAN                ABCDE1234F            ABCD******4F                          │   │
│   │   Aadhaar            1234 5678 9012        XXXX XXXX 9012                        │   │
│   │   Account            1234567890123         XXXXXXXXX0123                         │   │
│   │                                                                                 │   │
│   │   Masking applied based on:                                                     │   │
│   │   • User role (viewer sees masked, admin sees full)                             │   │
│   │   • Context (logs always masked)                                                │   │
│   │   • Explicit tool configuration                                                 │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                    PII PROHIBITION RULES (STRICTLY ENFORCED)                    │   │
│   │                                                                                 │   │
│   │   ❌ PROHIBITED in:                                                             │   │
│   │      • Application logs (stdout/stderr)                                         │   │
│   │      • CloudWatch/X-Ray traces                                                  │   │
│   │      • Dashboard displays                                                       │   │
│   │      • Error messages returned to clients                                       │   │
│   │      • Prometheus metrics labels                                                │   │
│   │                                                                                 │   │
│   │   ✅ ALLOWED in (with masking):                                                 │   │
│   │      • Audit logs (masked in JSONB details)                                     │   │
│   │      • Encrypted database fields                                                │   │
│   │      • API responses (only to authorized users)                                 │   │
│   │                                                                                 │   │
│   │   CI/CD Enforcement:                                                            │   │
│   │      • Automated PII pattern detection in logs                                  │   │
│   │      • Security tests fail build if PII detected                                │   │
│   │      • Pre-commit hooks scan for hardcoded PII                                  │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Security Controls Summary

| Control | Implementation | Compliance |
|---------|----------------|------------|
| Authentication | OAuth2/OIDC with JWKS (MSIL IdP) | ISO 27001, SOC2 |
| Authorization | OPA-based RBAC | ISO 27001 |
| Write Tool Safety | user_confirmed step-up required | OWASP |
| Encryption at Rest | AES-256 (AWS KMS) | DPDP, PCI-DSS |
| Encryption in Transit | TLS 1.2+ / mTLS | PCI-DSS |
| Audit Logging | S3 WORM with checksums (12-mo retention) | SOC2, DPDP |
| PII Protection | Masking + prohibited in logs/traces | DPDP |
| Access Control | PIM/PAM for privileged | ISO 27001 |
| Input Validation | Schema + injection detection | OWASP |
| Rate Limiting | Token bucket with tiers (APIM parity) | Operational |
| Secrets Management | AWS Secrets Manager | ISO 27001 |
| Vulnerability Scanning | Trivy, Grype, Snyk | DevSecOps |

---

*Document Classification: Confidential | Last Review: February 1, 2026*
