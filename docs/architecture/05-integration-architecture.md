# Integration Architecture

**Document Version**: 2.1  
**Last Updated**: February 1, 2026  
**Classification**: Internal

---

## 1. Overview

This document describes how the MCP Server integrates with MSIL's API Manager, backend services, authentication providers, and observability infrastructure.

**Important Notes**:
- All external integrations (IdP, APIM) are **configurable** and not vendor-locked
- "MSIL IdP" refers to MSIL's OIDC-compliant identity provider (specific implementation TBD by MSIL)
- "MSIL APIM" refers to MSIL's API Management platform (specific implementation TBD by MSIL)
- The LLM **decides which tool to call**—the Host/Agent application (with MCP Client) communicates with MCP Server

---

## 2. Integration Landscape

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              INTEGRATION LANDSCAPE                                       │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           EXTERNAL INTEGRATIONS                                 │   │
│   │                                                                                 │   │
│   │   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐                   │   │
│   │   │   MSIL IdP    │   │   MSIL APIM   │   │  Host/Agent   │                   │   │
│   │   │  (Identity)   │   │   (Gateway)   │   │  Application  │                   │   │
│   │   │               │   │               │   │               │                   │   │
│   │   │ • OAuth2/OIDC │   │ • API Routing │   │ • MCP Client  │                   │   │
│   │   │ • JWKS        │   │ • Rate Limit  │   │ • LLM decides │                   │   │
│   │   │ • PIM/PAM     │   │ • Subscript.  │   │   tool calls  │                   │   │
│   │   └───────┬───────┘   └───────┬───────┘   └───────┬───────┘                   │   │
│   │           │                   │                   │                            │   │
│   └───────────┼───────────────────┼───────────────────┼────────────────────────────┘   │
│               │                   │                   │                                │
│               ▼                   ▼                   ▼                                │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                                 │   │
│   │                              MCP SERVER                                         │   │
│   │                                                                                 │   │
│   │   ┌───────────────────────────────────────────────────────────────────────┐     │   │
│   │   │                    INTEGRATION ADAPTERS                               │     │   │
│   │   │                                                                       │     │   │
│   │   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │     │   │
│   │   │   │   OAuth     │  │   APIM      │  │    OPA      │  │    Audit    │ │     │   │
│   │   │   │   Client    │  │   Client    │  │   Client    │  │   Client    │ │     │   │
│   │   │   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │     │   │
│   │   │                                                                       │     │   │
│   │   └───────────────────────────────────────────────────────────────────────┘     │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│               │                   │                   │                                │
│               ▼                   ▼                   ▼                                │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           INTERNAL INTEGRATIONS                                 │   │
│   │                                                                                 │   │
│   │   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐                   │   │
│   │   │  PostgreSQL   │   │    Redis      │   │     S3        │                   │   │
│   │   │   (Data)      │   │   (Cache)     │   │   (Audit)     │                   │   │
│   │   │               │   │               │   │               │                   │   │
│   │   │ • Tools       │   │ • Sessions    │   │ • WORM logs   │                   │   │
│   │   │ • Users       │   │ • Tool cache  │   │ • Checksums   │                   │   │
│   │   │ • Audit       │   │ • Rate limit  │   │               │                   │   │
│   │   └───────────────┘   └───────────────┘   └───────────────┘                   │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. MSIL APIM Integration

### 3.1 API Manager Connectivity

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              MSIL APIM INTEGRATION                                       │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        MCP SERVER → APIM FLOW                                   │   │
│   │                                                                                 │   │
│   │   ┌─────────────┐                                           ┌─────────────┐    │   │
│   │   │  MCP Tool   │                                           │   Backend   │    │   │
│   │   │  Executor   │                                           │   Service   │    │   │
│   │   └──────┬──────┘                                           └──────▲──────┘    │   │
│   │          │                                                         │            │   │
│   │          │ 1. Tool execution request                               │            │   │
│   │          ▼                                                         │            │   │
│   │   ┌─────────────────────────────────────────────────────────────┐  │            │   │
│   │   │                    APIM Client                              │  │            │   │
│   │   │                                                             │  │            │   │
│   │   │  ┌────────────────────────────────────────────────────────┐ │  │            │   │
│   │   │  │ 2. Build Request                                       │ │  │            │   │
│   │   │  │                                                        │ │  │            │   │
│   │   │  │ Headers:                                               │ │  │            │   │
│   │   │  │   Authorization: Bearer {user_jwt_token}               │ │  │            │   │
│   │   │  │   Ocp-Apim-Subscription-Key: {subscription_key}        │ │  │            │   │
│   │   │  │   X-Correlation-ID: {correlation_id}                   │ │  │            │   │
│   │   │  │   X-MCP-Tool-Name: {tool_name}                         │ │  │            │   │
│   │   │  │   X-MCP-Risk-Level: {risk_level}                       │ │  │            │   │
│   │   │  │                                                        │ │  │            │   │
│   │   │  │ mTLS Client Certificate: {client_cert.pem}             │ │  │            │   │
│   │   │  │                                                        │ │  │            │   │
│   │   │  └────────────────────────────────────────────────────────┘ │  │            │   │
│   │   │                                                             │  │            │   │
│   │   │  ┌────────────────────────────────────────────────────────┐ │  │            │   │
│   │   │  │ 3. Resilience Patterns                                 │ │  │            │   │
│   │   │  │                                                        │ │  │            │   │
│   │   │  │ Circuit Breaker:                                       │ │  │            │   │
│   │   │  │   • Threshold: 5 failures in 60s                       │ │  │            │   │
│   │   │  │   • Reset: 30s                                         │ │  │            │   │
│   │   │  │   • Half-open: 1 test request                          │ │  │            │   │
│   │   │  │                                                        │ │  │            │   │
│   │   │  │ Retry Policy:                                          │ │  │            │   │
│   │   │  │   • Max attempts: 3                                    │ │  │            │   │
│   │   │  │   • Backoff: exponential (1s, 2s, 4s)                  │ │  │            │   │
│   │   │  │   • Retry on: 5xx, timeout, connection error           │ │  │            │   │
│   │   │  │                                                        │ │  │            │   │
│   │   │  │ Timeout:                                               │ │  │            │   │
│   │   │  │   • Connect: 5s                                        │ │  │            │   │
│   │   │  │   • Read: 30s                                          │ │  │            │   │
│   │   │  │                                                        │ │  │            │   │
│   │   │  └────────────────────────────────────────────────────────┘ │  │            │   │
│   │   │                                                             │  │            │   │
│   │   └────────────────────────────────────────────┬────────────────┘  │            │   │
│   │                                                │                   │            │   │
│   │                                                ▼                   │            │   │
│   │                                         ┌─────────────┐            │            │   │
│   │                                         │  MSIL APIM  │────────────┘            │   │
│   │                                         │             │                         │   │
│   │                                         │ 4. Validate │                         │   │
│   │                                         │    Route    │                         │   │
│   │                                         │    Log      │                         │   │
│   │                                         └─────────────┘                         │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 APIM Configuration

```python
# APIM Client Configuration
class APIMConfig:
    base_url: str = "https://apim.msil.com"
    subscription_key: str = "${APIM_SUBSCRIPTION_KEY}"
    
    # mTLS Configuration
    client_cert_path: str = "/etc/secrets/mtls/client.pem"
    client_key_path: str = "/etc/secrets/mtls/client.key"
    ca_cert_path: str = "/etc/secrets/mtls/ca.pem"
    
    # Circuit Breaker
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 30
    
    # Retry Policy
    retry_max_attempts: int = 3
    retry_backoff_base: float = 1.0
    retry_backoff_max: float = 10.0
    
    # Timeouts
    connect_timeout: int = 5
    read_timeout: int = 30
```

### 3.3 API Mapping Table

| MCP Tool | APIM Endpoint | Backend Service | Method |
|----------|---------------|-----------------|--------|
| `get_dealer_enquiries` | `/v1/dealers/{id}/enquiries` | Dealer Service | GET |
| `create_booking` | `/v1/bookings` | Booking Service | POST |
| `get_vehicle_inventory` | `/v1/inventory` | Inventory Service | GET |
| `update_enquiry_status` | `/v1/enquiries/{id}/status` | Enquiry Service | PUT |
| `process_payment` | `/v1/payments` | Payment Gateway | POST |

---

## 4. Authentication Integration

### 4.1 Azure AD Integration

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              AZURE AD INTEGRATION                                        │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        TOKEN VALIDATION FLOW                                    │   │
│   │                                                                                 │   │
│   │   Request with JWT                                                              │   │
│   │        │                                                                        │   │
│   │        ▼                                                                        │   │
│   │   ┌───────────────────────────────────────────────────────────────────────┐     │   │
│   │   │ 1. Extract Token                                                      │     │   │
│   │   │    Authorization: Bearer eyJhbGciOiJSUzI1NiIs...                      │     │   │
│   │   └───────────────────────────────────────────────────────────────────────┘     │   │
│   │        │                                                                        │   │
│   │        ▼                                                                        │   │
│   │   ┌───────────────────────────────────────────────────────────────────────┐     │   │
│   │   │ 2. Check Cache                                                        │     │   │
│   │   │    Redis: jwks:{issuer}:keys                                          │     │   │
│   │   │                                                                       │     │   │
│   │   │    ┌─────────────────────────────────────────────────────────────┐    │     │   │
│   │   │    │ Cache Hit → Use cached keys                                 │    │     │   │
│   │   │    │ Cache Miss → Fetch from Azure AD JWKS endpoint              │    │     │   │
│   │   │    └─────────────────────────────────────────────────────────────┘    │     │   │
│   │   │                                                                       │     │   │
│   │   └───────────────────────────────────────────────────────────────────────┘     │   │
│   │        │                                                                        │   │
│   │        ▼                                                                        │   │
│   │   ┌───────────────────────────────────────────────────────────────────────┐     │   │
│   │   │ 3. Validate Token                                                     │     │   │
│   │   │                                                                       │     │   │
│   │   │    Validations:                                                       │     │   │
│   │   │    ✓ Signature (RS256 with public key)                                │     │   │
│   │   │    ✓ Issuer: https://login.microsoftonline.com/{tenant}/v2.0          │     │   │
│   │   │    ✓ Audience: api://msil-mcp-server                                  │     │   │
│   │   │    ✓ Expiration: exp > now                                            │     │   │
│   │   │    ✓ Not Before: nbf < now                                            │     │   │
│   │   │    ✓ Required claims: sub, oid, preferred_username                    │     │   │
│   │   │                                                                       │     │   │
│   │   └───────────────────────────────────────────────────────────────────────┘     │   │
│   │        │                                                                        │   │
│   │        ▼                                                                        │   │
│   │   ┌───────────────────────────────────────────────────────────────────────┐     │   │
│   │   │ 4. Extract User Context                                               │     │   │
│   │   │                                                                       │     │   │
│   │   │    {                                                                  │     │   │
│   │   │      "user_id": "user@msil.com",                                      │     │   │
│   │   │      "oid": "12345-67890-abcdef",                                     │     │   │
│   │   │      "roles": ["operator"],                                           │     │   │
│   │   │      "groups": ["dealer-ops", "regional-north"]                       │     │   │
│   │   │    }                                                                  │     │   │
│   │   │                                                                       │     │   │
│   │   └───────────────────────────────────────────────────────────────────────┘     │   │
│   │        │                                                                        │   │
│   │        ▼                                                                        │   │
│   │   Request proceeds with authenticated user context                              │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 PIM/PAM Integration

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              PIM/PAM INTEGRATION                                         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        ELEVATION REQUEST FLOW                                   │   │
│   │                                                                                 │   │
│   │   User requests privileged tool                                                 │   │
│   │        │                                                                        │   │
│   │        ▼                                                                        │   │
│   │   ┌───────────────────────────────────────────────────────────────────────┐     │   │
│   │   │ MCP Server checks tool risk level                                     │     │   │
│   │   │                                                                       │     │   │
│   │   │ Tool: delete_customer_data                                            │     │   │
│   │   │ Risk: privileged                                                      │     │   │
│   │   │ Requires elevation: true                                              │     │   │
│   │   └───────────────────────────────────────────────────────────────────────┘     │   │
│   │        │                                                                        │   │
│   │        ▼                                                                        │   │
│   │   ┌───────────────────────────────────────────────────────────────────────┐     │   │
│   │   │ Check for existing elevation                                          │     │   │
│   │   │                                                                       │     │   │
│   │   │ POST /api/pim/check-elevation                                         │     │   │
│   │   │ {                                                                     │     │   │
│   │   │   "user_id": "user@msil.com",                                         │     │   │
│   │   │   "role": "admin",                                                    │     │   │
│   │   │   "scope": "delete_customer_data"                                     │     │   │
│   │   │ }                                                                     │     │   │
│   │   └───────────────────────────────────────────────────────────────────────┘     │   │
│   │        │                                                                        │   │
│   │        ├─────────────────────────────────────────────────────┐                  │   │
│   │        │                                                     │                  │   │
│   │        ▼ (Elevated)                                          ▼ (Not Elevated)   │   │
│   │   ┌─────────────────────────┐                    ┌─────────────────────────┐    │   │
│   │   │ Proceed with execution  │                    │ Return elevation URL    │    │   │
│   │   │                         │                    │                         │    │   │
│   │   │ Verify:                 │                    │ {                       │    │   │
│   │   │ • elevation_expires_at  │                    │   "requires_elevation": │    │   │
│   │   │   > now                 │                    │     true,               │    │   │
│   │   │ • scope matches tool    │                    │   "elevation_url":      │    │   │
│   │   │                         │                    │     "https://pim..."    │    │   │
│   │   └─────────────────────────┘                    │ }                       │    │   │
│   │                                                  └─────────────────────────┘    │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        ELEVATION GRANT STORAGE                                  │   │
│   │                                                                                 │   │
│   │   Redis Key: elevation:{user_id}:{scope}                                        │   │
│   │   Value: {                                                                      │   │
│   │     "granted_at": "2026-01-31T10:00:00Z",                                       │   │
│   │     "expires_at": "2026-01-31T11:00:00Z",                                       │   │
│   │     "scope": "delete_customer_data",                                            │   │
│   │     "approval_reference": "PIM-2026-001234"                                     │   │
│   │   }                                                                             │   │
│   │   TTL: 3600 seconds (1 hour)                                                    │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Tool Registry Integration

### 5.1 OpenAPI Import Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              OPENAPI IMPORT FLOW                                         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                                 │   │
│   │   ┌─────────────────┐                                                           │   │
│   │   │   OpenAPI Spec  │                                                           │   │
│   │   │   (YAML/JSON)   │                                                           │   │
│   │   │                 │                                                           │   │
│   │   │ /v1/dealers:    │                                                           │   │
│   │   │   get:          │                                                           │   │
│   │   │     operationId:│                                                           │   │
│   │   │       getDealers│                                                           │   │
│   │   │     parameters: │                                                           │   │
│   │   │       - name:   │                                                           │   │
│   │   │         region  │                                                           │   │
│   │   │         in: query│                                                          │   │
│   │   │         schema: │                                                           │   │
│   │   │           type: │                                                           │   │
│   │   │             string│                                                         │   │
│   │   │                 │                                                           │   │
│   │   └────────┬────────┘                                                           │   │
│   │            │                                                                    │   │
│   │            ▼                                                                    │   │
│   │   ┌────────────────────────────────────────────────────────────────────────┐    │   │
│   │   │ IMPORT PIPELINE                                                        │    │   │
│   │   │                                                                        │    │   │
│   │   │   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌───────────┐ │    │   │
│   │   │   │   Parse     │   │   Validate  │   │   Generate  │   │   Store   │ │    │   │
│   │   │   │   Spec      │──▶│   Schema    │──▶│   Tools     │──▶│   Tools   │ │    │   │
│   │   │   │             │   │             │   │             │   │           │ │    │   │
│   │   │   │ • Parse     │   │ • Required  │   │ • Name from │   │ • Postgres│ │    │   │
│   │   │   │   YAML/JSON │   │   fields    │   │   operationId│   │ • Version │ │    │   │
│   │   │   │ • Resolve   │   │ • Types     │   │ • Input from│   │ • Cache   │ │    │   │
│   │   │   │   $ref      │   │ • Security  │   │   parameters│   │   invalid.│ │    │   │
│   │   │   │             │   │             │   │ • Output    │   │           │ │    │   │
│   │   │   │             │   │             │   │   from resp │   │           │ │    │   │
│   │   │   └─────────────┘   └─────────────┘   └─────────────┘   └───────────┘ │    │   │
│   │   │                                                                        │    │   │
│   │   └────────────────────────────────────────────────────────────────────────┘    │   │
│   │            │                                                                    │   │
│   │            ▼                                                                    │   │
│   │   ┌────────────────────────────────────────────────────────────────────────┐    │   │
│   │   │ GENERATED TOOL                                                         │    │   │
│   │   │                                                                        │    │   │
│   │   │ {                                                                      │    │   │
│   │   │   "name": "get_dealers",                                               │    │   │
│   │   │   "description": "Get list of dealers with optional filters",          │    │   │
│   │   │   "version": "1.0.0",                                                  │    │   │
│   │   │   "input_schema": {                                                    │    │   │
│   │   │     "type": "object",                                                  │    │   │
│   │   │     "properties": {                                                    │    │   │
│   │   │       "region": {"type": "string", "description": "Filter by region"}  │    │   │
│   │   │     }                                                                  │    │   │
│   │   │   },                                                                   │    │   │
│   │   │   "api_endpoint": "/v1/dealers",                                       │    │   │
│   │   │   "http_method": "GET",                                                │    │   │
│   │   │   "query_params": ["region"],                                          │    │   │
│   │   │   "risk_level": "read",                                                │    │   │
│   │   │   "source_spec": "dealer-service-v1.yaml"                              │    │   │
│   │   │ }                                                                      │    │   │
│   │   │                                                                        │    │   │
│   │   └────────────────────────────────────────────────────────────────────────┘    │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Tool Discovery API

```http
GET /api/mcp/tools
Authorization: Bearer {token}

Response:
{
  "tools": [
    {
      "name": "get_dealer_enquiries",
      "description": "Retrieve enquiries for a specific dealer",
      "version": "1.0.0",
      "risk_level": "read",
      "input_schema": {
        "type": "object",
        "properties": {
          "dealer_id": {
            "type": "string",
            "description": "Unique dealer identifier"
          },
          "status": {
            "type": "string",
            "enum": ["pending", "contacted", "converted", "lost"]
          }
        },
        "required": ["dealer_id"]
      },
      "positive_examples": [
        {
          "input": {"dealer_id": "DL001"},
          "output": {"enquiries": [...]}
        }
      ]
    }
  ],
  "total": 42,
  "domains": ["dealer", "inventory", "booking", "customer"]
}
```

---

## 6. Policy Engine Integration (OPA)

### 6.1 OPA Sidecar Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              OPA SIDECAR INTEGRATION                                     │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              Kubernetes Pod                                     │   │
│   │                                                                                 │   │
│   │   ┌───────────────────────────────────┐   ┌───────────────────────────────┐    │   │
│   │   │         mcp-server                │   │         opa-sidecar           │    │   │
│   │   │                                   │   │                               │    │   │
│   │   │   ┌───────────────────────────┐   │   │   ┌───────────────────────┐   │    │   │
│   │   │   │                           │   │   │   │                       │   │    │   │
│   │   │   │   Authorization Request   │   │   │   │   Policy Evaluation   │   │    │   │
│   │   │   │                           │◀──┼───┼──▶│                       │   │    │   │
│   │   │   │   POST localhost:8181     │   │   │   │   • Load policies     │   │    │   │
│   │   │   │   /v1/data/msil/authz     │   │   │   │   • Evaluate input    │   │    │   │
│   │   │   │                           │   │   │   │   • Return decision   │   │    │   │
│   │   │   │                           │   │   │   │                       │   │    │   │
│   │   │   └───────────────────────────┘   │   │   └───────────────────────┘   │    │   │
│   │   │                                   │   │                               │    │   │
│   │   └───────────────────────────────────┘   └───────────────────────────────┘    │   │
│   │                                                           │                    │   │
│   │                                                           │                    │   │
│   └───────────────────────────────────────────────────────────┼────────────────────┘   │
│                                                               │                        │
│                                                               ▼                        │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           ConfigMap: opa-policies                               │   │
│   │                                                                                 │   │
│   │   policies/                                                                     │   │
│   │   ├── authz.rego          # Main authorization policy                           │   │
│   │   ├── rbac.rego           # Role-based access rules                             │   │
│   │   ├── tool_access.rego    # Tool-specific access rules                          │   │
│   │   └── data.json           # Static data (roles, tool mappings)                  │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           POLICY DECISION FLOW                                  │   │
│   │                                                                                 │   │
│   │   Request:                                                                      │   │
│   │   {                                                                             │   │
│   │     "input": {                                                                  │   │
│   │       "user": {"id": "user@msil.com", "role": "operator"},                      │   │
│   │       "tool": {"name": "update_dealer", "risk_level": "write"},                 │   │
│   │       "action": "execute"                                                       │   │
│   │     }                                                                           │   │
│   │   }                                                                             │   │
│   │                                                                                 │   │
│   │   Response:                                                                     │   │
│   │   {                                                                             │   │
│   │     "result": {                                                                 │   │
│   │       "allow": true,                                                            │   │
│   │       "reason": "operator can execute write tools"                              │   │
│   │     }                                                                           │   │
│   │   }                                                                             │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Observability Integration

### 7.1 AWS CloudWatch Integration

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              CLOUDWATCH INTEGRATION                                      │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              DATA FLOW                                          │   │
│   │                                                                                 │   │
│   │   ┌───────────────┐                                                            │   │
│   │   │   mcp-server  │                                                            │   │
│   │   │   (Python)    │                                                            │   │
│   │   │               │                                                            │   │
│   │   │   Structured  │───┐                                                        │   │
│   │   │   JSON Logs   │   │                                                        │   │
│   │   │               │   │                                                        │   │
│   │   └───────────────┘   │    ┌───────────────┐    ┌───────────────────────────┐  │   │
│   │                       ├───▶│   Fluent Bit  │───▶│   CloudWatch Logs         │  │   │
│   │   ┌───────────────┐   │    │   (DaemonSet) │    │                           │  │   │
│   │   │   admin-ui    │───┤    │               │    │   Log Groups:             │  │   │
│   │   │   (Nginx)     │   │    │ • Parse JSON  │    │   /mcp/server             │  │   │
│   │   └───────────────┘   │    │ • Add K8s     │    │   /mcp/admin-ui           │  │   │
│   │                       │    │   metadata    │    │   /mcp/chat-ui            │  │   │
│   │   ┌───────────────┐   │    │ • Batch send  │    │                           │  │   │
│   │   │   chat-ui     │───┘    │               │    │                           │  │   │
│   │   │   (Nginx)     │        └───────────────┘    └───────────────────────────┘  │   │
│   │   └───────────────┘                                                            │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              METRICS PIPELINE                                   │   │
│   │                                                                                 │   │
│   │   ┌───────────────┐    ┌───────────────┐    ┌───────────────────────────────┐   │   │
│   │   │   mcp-server  │    │  CloudWatch   │    │   CloudWatch Metrics          │   │   │
│   │   │               │───▶│    Agent      │───▶│                               │   │   │
│   │   │   /metrics    │    │  (DaemonSet)  │    │   Namespace: MCP/Production   │   │   │
│   │   │   endpoint    │    │               │    │                               │   │   │
│   │   │               │    │ • Scrape      │    │   Metrics:                    │   │   │
│   │   │ Prometheus    │    │   Prometheus  │    │   • request_count             │   │   │
│   │   │ format        │    │   format      │    │   • request_latency           │   │   │
│   │   │               │    │ • Convert to  │    │   • tool_executions           │   │   │
│   │   └───────────────┘    │   CW metrics  │    │   • error_rate                │   │   │
│   │                        │               │    │   • auth_failures             │   │   │
│   │                        └───────────────┘    │                               │   │   │
│   │                                             └───────────────────────────────┘   │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              DISTRIBUTED TRACING                                │   │
│   │                                                                                 │   │
│   │   ┌───────────────┐    ┌───────────────┐    ┌───────────────────────────────┐   │   │
│   │   │   mcp-server  │    │ OpenTelemetry │    │       AWS X-Ray               │   │   │
│   │   │               │───▶│    SDK        │───▶│                               │   │   │
│   │   │   @trace      │    │               │    │   • Service Map               │   │   │
│   │   │   decorator   │    │ • Span create │    │   • Trace Timeline            │   │   │
│   │   │               │    │ • Context     │    │   • Error Analysis            │   │   │
│   │   │               │    │   propagate   │    │   • Latency Histograms        │   │   │
│   │   └───────────────┘    │ • Export      │    │                               │   │   │
│   │                        │   to X-Ray    │    │                               │   │   │
│   │                        └───────────────┘    └───────────────────────────────┘   │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Database Integration

### 8.1 Connection Management

```python
# Database Configuration
class DatabaseConfig:
    # Connection
    host: str = "${DB_HOST}"
    port: int = 5432
    database: str = "mcp"
    username: str = "${DB_USERNAME}"  # From Secrets Manager
    password: str = "${DB_PASSWORD}"  # From Secrets Manager
    
    # SSL/TLS
    ssl_mode: str = "require"
    ssl_cert: str = "/etc/secrets/rds/ca-bundle.pem"
    
    # Connection Pool
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800  # 30 minutes
    
    # Query Settings
    statement_timeout: int = 30000  # 30 seconds
    lock_timeout: int = 5000  # 5 seconds

# Async SQLAlchemy Engine
engine = create_async_engine(
    f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}",
    pool_size=pool_size,
    max_overflow=max_overflow,
    pool_timeout=pool_timeout,
    pool_recycle=pool_recycle,
    connect_args={
        "ssl": ssl_context,
        "command_timeout": statement_timeout
    }
)
```

### 8.2 Redis Integration

```python
# Redis Configuration
class RedisConfig:
    # Connection
    host: str = "${REDIS_HOST}"
    port: int = 6379
    password: str = "${REDIS_PASSWORD}"
    
    # TLS
    ssl: bool = True
    ssl_cert_reqs: str = "required"
    ssl_ca_certs: str = "/etc/secrets/redis/ca.pem"
    
    # Connection Pool
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    
    # Cluster Mode
    cluster_mode: bool = True
    read_from_replicas: bool = True

# Redis Client
redis_client = redis.Redis(
    host=host,
    port=port,
    password=password,
    ssl=True,
    ssl_ca_certs=ssl_ca_certs,
    decode_responses=True
)
```

---

## 9. Integration Security Summary

| Integration | Authentication | Encryption | Authorization |
|-------------|----------------|------------|---------------|
| MSIL APIM | mTLS + Subscription Key | TLS 1.2+ | APIM policies |
| Azure AD | OIDC | TLS 1.2+ | Token validation |
| PostgreSQL | Username/Password | TLS 1.2+ | Database roles |
| Redis | Password | TLS 1.2+ | ACL |
| S3 | IAM Role | SSE-KMS | Bucket policies |
| OPA | N/A (localhost) | N/A | Rego policies |
| CloudWatch | IAM Role | TLS 1.2+ | IAM policies |

---

*Document Classification: Internal | Last Review: January 31, 2026*
