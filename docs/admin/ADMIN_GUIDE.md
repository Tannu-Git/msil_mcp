# MSIL MCP Platform — Admin Guide

**Version**: 1.1  
**Date**: February 2, 2026  
**Audience**: Platform Admins, Security Team, DevSecOps

**Phase 3 Addition**: See [Exposure Governance Admin User Guide](../ADMIN_USER_GUIDE_EXPOSURE_GOVERNANCE.md) for detailed exposure management instructions.

---

## Guide Structure

This guide covers platform-wide administration. For specific features:
- **Exposure Governance** (tool visibility management): See [ADMIN_USER_GUIDE_EXPOSURE_GOVERNANCE.md](../ADMIN_USER_GUIDE_EXPOSURE_GOVERNANCE.md)
- **General Platform Setup**: Continue reading below

---

## 1) Register the MCP Platform in the MSIL IdP

### 1.1 Create the Application
- **Application type**: Web/API (OIDC)
- **Redirect URIs**:
  - Admin UI: `https://<admin-ui-host>/auth/callback`
  - Host/Agent App: `https://<host-app>/auth/callback`
- **Allowed grant types**: Authorization Code + PKCE
- **Token types**: JWT access token + ID token

### 1.2 Create Roles / Groups in IdP
Create these roles (or groups mapped to roles):
- `admin`
- `developer`
- `operator`
- `viewer`

These appear in the JWT as `roles` or `groups`. Example claims:

```json
{
  "roles": ["operator", "viewer"],
  "departments": ["dealer-operations"],
  "pim_elevation": false,
  "scope": "mcp:tools:read mcp:tools:write"
}
```

### 1.3 Configure Token Claims
**Required claims**:
- `iss` (Issuer)
- `aud` (Audience)
- `exp` (Expiration)
- `iat` (Issued At)
- `sub` (User ID)
- `roles` (RBAC)
- `departments` (Business scope)
- `scope` (Fine-grained scopes)
- `pim_elevation` (Privileged access)

**Optional claims**:
- `pim_elevation_expires`
- `tenant_id`
- `employee_id`

### 1.4 Export OIDC Configuration
You will need:
- **Issuer URL**: `OIDC_ISSUER`
- **Audience**: `OIDC_AUDIENCE`
- **JWKS URL**: `OIDC_JWKS_URL`

---

## 2) Configure MCP Server Authentication

Update environment variables in the server runtime:

```
OAUTH2_ENABLED=true
OIDC_ENABLED=true
OIDC_ISSUER=https://<msil-idp>/
OIDC_AUDIENCE=msil-mcp-server
OIDC_JWKS_URL=https://<msil-idp>/.well-known/jwks.json
OIDC_REQUIRED_SCOPES=openid,profile,email
TOKEN_VALIDATE_ISSUER=true
TOKEN_VALIDATE_AUDIENCE=true
```

> **Note**: `JWT_SECRET` is only used for local/non-OIDC mode.

---

## 3) Configure Tool Management

Tools can be managed in three ways:

1) **Admin UI (recommended)**
- Use the Tools page to **create**, **edit**, and **deactivate** tools.
- Update API endpoint, HTTP method, schemas, and risk level.

2) **OpenAPI Import**
- Upload OpenAPI spec via Admin UI Import page.
- Review generated tools and approve for registration.

3) **Database Seed**
- Update `infrastructure/local/init-scripts/01-init.sql` for initial tool population.

### 3.1 Tool Fields to Configure
- `name`, `display_name`, `description`
- `category`
- `api_endpoint`, `http_method`
- `input_schema`, `output_schema`
- `auth_type`, `headers`
- `risk_level` (read/write/privileged)
- `requires_elevation`, `requires_confirmation`
- `rate_limit_tier` (permissive/standard/strict)

---

## 4) Configure OPA Policy Engine

OPA evaluates **fine-grained** authorization rules beyond RBAC.

### 4.1 Location of Rego Policies
- `mcp-server/app/core/policy/rego/`

### 4.2 Enable OPA
```
OPA_ENABLED=true
OPA_URL=http://<opa-service>:8181
```

### 4.3 Example Policy Logic
Typical OPA rules enforce:
- Tool access by role
- Department-based scope
- Time-of-day restrictions
- Dealer ownership or assignment
- Privileged access with elevation

### 4.4 Policy Lifecycle
1. Edit Rego rules
2. Deploy to OPA (Kubernetes ConfigMap or mounted volume)
3. MCP Server calls OPA for every tool execution

---

## 5) Configure RBAC (Fallback Policy Engine)

If OPA is down, MCP falls back to internal RBAC policies.

You can manage these in Admin UI under **Policy Configuration**.

> **Note**: UI changes affect runtime memory only. For persistent policy, update OPA policies or store RBAC in DB.

---

## 6) Configure PIM / PAM (Privileged Access)

Set PIM settings:
```
PIM_ENABLED=true
PIM_PROVIDER=msil-idp
ELEVATION_DURATION_SECONDS=3600
ELEVATION_REQUIRE_REASON=true
```

**Expected IdP Claims**:
- `pim_elevation`: true/false
- `pim_elevation_expires`: timestamp

Privileged tools require:
- `risk_level=privileged`
- `requires_elevation=true`
- user token with `pim_elevation=true`

---

## 7) Admin UI — Policy & Tool Management

### 7.1 Tools Page
- **Add Tool** → creates new tool definition
- **Edit** → updates schemas, endpoints, and security flags
- **Deactivate** → sets `is_active=false`

### 7.2 Policy Configuration Page
- **Create Role** (e.g., `operator`)
- **Add/Remove Permissions**
- **Delete Role**

> These are **runtime RBAC** policies. For production, OPA policies are authoritative.

---

## 8) Expected IdP Claims Mapping

| Claim | Purpose | Example |
|------|---------|---------|
| `roles` | RBAC | `['operator','viewer']` |
| `departments` | Business scope | `['dealer-operations']` |
| `scope` | OAuth scopes | `mcp:tools:read mcp:tools:write` |
| `pim_elevation` | Privileged access | `true` |
| `aud` | Audience | `msil-mcp-server` |
| `iss` | Issuer | `https://msil-idp.example.com` |

---

## 9) Verification Checklist

- [ ] MCP app registered in IdP
- [ ] Roles created and users assigned
- [ ] OIDC configuration in MCP server
- [ ] OPA running and reachable
- [ ] Tool catalog populated
- [ ] Admin UI access verified
- [ ] Audit logs enabled and retention set

---

*Last updated: February 2, 2026*
