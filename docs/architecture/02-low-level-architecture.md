# Low-Level Technical Architecture

**Document Version**: 2.1  
**Last Updated**: February 1, 2026  
**Classification**: Internal

---

## 1. Overview

This document provides detailed component-level design including the tool-definition layer, routing engine, validation modules, caching strategies, and observability stack.

**Important**: The MCP Server communicates with **Host/Agent applications** (which embed an MCP Client). The **LLM only decides which tool to call**—it does not speak MCP protocol directly. Security responsibility lies with the Host and MCP Server.

---

## 2. Component Architecture

### 2.1 MCP Server Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         MCP SERVER COMPONENT ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              API LAYER (FastAPI)                                 │   │
│  │                                                                                  │   │
│  │   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │   │
│  │   │   /api/mcp    │  │  /api/admin   │  │  /api/chat    │  │  /api/auth    │   │   │
│  │   │               │  │               │  │               │  │               │   │   │
│  │   │ • /tools      │  │ • /settings   │  │ • /messages   │  │ • /login      │   │   │
│  │   │ • /execute    │  │ • /users      │  │ • /sessions   │  │ • /refresh    │   │   │
│  │   │ • /batch      │  │ • /audit      │  │ • /analytics  │  │ • /logout     │   │   │
│  │   │ • /discover   │  │ • /tools      │  │               │  │ • /elevate    │   │   │
│  │   └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘   │   │
│  │                                                                                  │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                               │
│  ┌──────────────────────────────────────┼───────────────────────────────────────────┐   │
│  │                              MIDDLEWARE LAYER                                     │   │
│  │                                      │                                            │   │
│  │   ┌───────────────┐  ┌───────────────┼───────────┐  ┌───────────────┐            │   │
│  │   │   CORS        │  │   Auth        ▼           │  │   Request     │            │   │
│  │   │   Handler     │──│   Middleware              │──│   Logger      │            │   │
│  │   │               │  │   (JWT/API Key)           │  │               │            │   │
│  │   └───────────────┘  └───────────────────────────┘  └───────────────┘            │   │
│  │                                                                                   │   │
│  │   ┌───────────────┐  ┌───────────────────────────┐  ┌───────────────┐            │   │
│  │   │   Rate        │  │   Correlation ID          │  │   Error       │            │   │
│  │   │   Limiter     │──│   Propagation             │──│   Handler     │            │   │
│  │   │               │  │                           │  │               │            │   │
│  │   └───────────────┘  └───────────────────────────┘  └───────────────┘            │   │
│  │                                                                                   │   │
│  └───────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                               │
│  ┌──────────────────────────────────────┼───────────────────────────────────────────┐   │
│  │                              CORE SERVICES LAYER                                  │   │
│  │                                      │                                            │   │
│  │   ┌──────────────────────────────────▼─────────────────────────────────────┐     │   │
│  │   │                         TOOL ENGINE                                     │     │   │
│  │   │                                                                         │     │   │
│  │   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │     │   │
│  │   │   │   Tool      │  │   Tool      │  │   Tool      │  │   Batch     │   │     │   │
│  │   │   │  Registry   │  │   Router    │  │  Executor   │  │  Executor   │   │     │   │
│  │   │   │             │  │             │  │             │  │             │   │     │   │
│  │   │   │ • Store     │  │ • Match     │  │ • Validate  │  │ • Parallel  │   │     │   │
│  │   │   │ • Search    │  │ • Route     │  │ • Execute   │  │ • Aggregate │   │     │   │
│  │   │   │ • Filter    │  │ • Transform │  │ • Transform │  │ • Rollback  │   │     │   │
│  │   │   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │     │   │
│  │   │                                                                         │     │   │
│  │   └─────────────────────────────────────────────────────────────────────────┘     │   │
│  │                                                                                   │   │
│  │   ┌───────────────────────────┐      ┌───────────────────────────┐               │   │
│  │   │      AUTH ENGINE          │      │      POLICY ENGINE        │               │   │
│  │   │                           │      │                           │               │   │
│  │   │   ┌─────────┐ ┌────────┐  │      │   ┌─────────┐ ┌────────┐  │               │   │
│  │   │   │  JWKS   │ │  JWT   │  │      │   │  OPA    │ │  Risk  │  │               │   │
│  │   │   │  Client │ │Handler │  │      │   │ Client  │ │ Policy │  │               │   │
│  │   │   └─────────┘ └────────┘  │      │   └─────────┘ └────────┘  │               │   │
│  │   │                           │      │                           │               │   │
│  │   │   ┌─────────┐ ┌────────┐  │      │   ┌─────────┐ ┌────────┐  │               │   │
│  │   │   │  OIDC   │ │  PIM   │  │      │   │  RBAC   │ │ Schema │  │               │   │
│  │   │   │Validator│ │Checker │  │      │   │ Engine  │ │Validate│  │               │   │
│  │   │   └─────────┘ └────────┘  │      │   └─────────┘ └────────┘  │               │   │
│  │   │                           │      │                           │               │   │
│  │   └───────────────────────────┘      └───────────────────────────┘               │   │
│  │                                                                                   │   │
│  │   ┌───────────────────────────┐      ┌───────────────────────────┐               │   │
│  │   │      AUDIT ENGINE         │      │      CACHE ENGINE         │               │   │
│  │   │                           │      │                           │               │   │
│  │   │   ┌─────────┐ ┌────────┐  │      │   ┌─────────┐ ┌────────┐  │               │   │
│  │   │   │  Audit  │ │  S3    │  │      │   │  Redis  │ │  Tool  │  │               │   │
│  │   │   │ Service │ │  WORM  │  │      │   │  Client │ │  Cache │  │               │   │
│  │   │   └─────────┘ └────────┘  │      │   └─────────┘ └────────┘  │               │   │
│  │   │                           │      │                           │               │   │
│  │   │   ┌─────────┐ ┌────────┐  │      │   ┌─────────┐ ┌────────┐  │               │   │
│  │   │   │  Event  │ │Checksum│  │      │   │Idempote-│ │  Rate  │  │               │   │
│  │   │   │ Builder │ │ Verify │  │      │   │  ncy    │ │ Limit  │  │               │   │
│  │   │   └─────────┘ └────────┘  │      │   └─────────┘ └────────┘  │               │   │
│  │   │                           │      │                           │               │   │
│  │   └───────────────────────────┘      └───────────────────────────┘               │   │
│  │                                                                                   │   │
│  └───────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                               │
│  ┌──────────────────────────────────────┼───────────────────────────────────────────┐   │
│  │                              INTEGRATION LAYER                                    │   │
│  │                                      │                                            │   │
│  │   ┌───────────────┐  ┌───────────────▼───────────┐  ┌───────────────┐            │   │
│  │   │   Database    │  │   API Gateway             │  │   External    │            │   │
│  │   │   Repository  │  │   Client (mTLS)           │  │   Services    │            │   │
│  │   │               │  │                           │  │               │            │   │
│  │   │ • Async SQLAl │  │ • Circuit Breaker         │  │ • OPA Server  │            │   │
│  │   │ • Connection  │  │ • Retry w/ Backoff        │  │ • Redis       │            │   │
│  │   │   Pool        │  │ • Timeout Handling        │  │ • S3          │            │   │
│  │   └───────────────┘  └───────────────────────────┘  └───────────────┘            │   │
│  │                                                                                   │   │
│  └───────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Tool Definition Layer

### 3.1 Tool Model Schema

```python
# Tool Definition Model
class Tool:
    # Core Fields
    id: UUID
    name: str                    # Unique identifier: "get_dealer_enquiries"
    description: str             # Human-readable description
    version: str                 # Semantic version: "1.0.0"
    
    # Input/Output Schema
    input_schema: dict           # JSON Schema for parameters
    output_schema: dict          # JSON Schema for response
    
    # API Mapping
    api_endpoint: str            # Backend API path
    http_method: str             # GET, POST, PUT, DELETE
    path_params: list[str]       # URL path parameters
    query_params: list[str]      # URL query parameters
    
    # Security & Governance
    risk_level: str              # read, write, privileged
    requires_elevation: bool     # PIM/PAM required
    requires_confirmation: bool  # Step-up: user_confirmed=true required
    allowed_roles: list[str]     # RBAC roles
    rate_limit_tier: str         # permissive, standard, strict
    
    # Validation
    parameter_validations: dict  # Custom validation rules
    allowlist: list[str]         # Allowed parameter values
    denylist: list[str]          # Blocked parameter values
    
    # Examples
    positive_examples: list      # Valid usage examples
    negative_examples: list      # Invalid usage examples
    error_models: dict           # Error response definitions
    
    # Metadata
    source_spec: str             # OpenAPI spec reference
    domain: str                  # Business domain
    journey: str                 # Customer journey
    created_at: datetime
    updated_at: datetime
    is_active: bool
```

### 3.1.1 Step-Up Confirmation for Write Tools

For write-level and privileged tools, the input schema **must** include `user_confirmed`:

```python
# Automatically injected for write/privileged tools:
if tool.risk_level in ["write", "privileged"]:
    tool.input_schema["properties"]["user_confirmed"] = {
        "type": "boolean",
        "description": "User explicitly confirmed this action",
        "default": False
    }
    tool.input_schema["required"].append("user_confirmed")
```

### 3.2 Tool Registry Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              TOOL REGISTRY ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           OPENAPI IMPORTER                                      │   │
│   │                                                                                 │   │
│   │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │   │
│   │   │   Swagger   │    │   Schema    │    │    Tool     │    │  Validation │    │   │
│   │   │   Parser    │───▶│  Extractor  │───▶│  Generator  │───▶│   Engine    │    │   │
│   │   │             │    │             │    │             │    │             │    │   │
│   │   │ • YAML/JSON │    │ • Paths     │    │ • Name Gen  │    │ • Schema    │    │   │
│   │   │ • URL/File  │    │ • Schemas   │    │ • Map Params│    │ • Examples  │    │   │
│   │   │ • Validate  │    │ • Security  │    │ • Build Def │    │ • Rules     │    │   │
│   │   └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    │   │
│   │                                                                                 │   │
│   │   Input: OpenAPI 3.0 Spec ──────▶ Output: MCP Tool Definitions                 │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                               │
│                                         ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           TOOL REGISTRY                                         │   │
│   │                                                                                 │   │
│   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │                        PostgreSQL                                       │   │   │
│   │   │                                                                         │   │   │
│   │   │   tools                    tool_versions            tool_metrics        │   │   │
│   │   │   ├── id (PK)              ├── id (PK)              ├── tool_id (FK)    │   │   │
│   │   │   ├── name (UNIQUE)        ├── tool_id (FK)         ├── invocations     │   │   │
│   │   │   ├── description          ├── version              ├── errors          │   │   │
│   │   │   ├── input_schema         ├── changes              ├── latency_p99     │   │   │
│   │   │   ├── output_schema        ├── created_at           ├── last_used       │   │   │
│   │   │   ├── api_config           └──────────────          └────────────       │   │   │
│   │   │   ├── security_config                                                    │   │   │
│   │   │   ├── is_active                                                          │   │   │
│   │   │   └── created_at                                                         │   │   │
│   │   │                                                                         │   │   │
│   │   └─────────────────────────────────────────────────────────────────────────┘   │   │
│   │                                         │                                       │   │
│   │   ┌─────────────────────────────────────▼─────────────────────────────────┐     │   │
│   │   │                        Redis Cache                                    │     │   │
│   │   │                                                                       │     │   │
│   │   │   tool:{name}:definition ──▶ Full tool JSON (TTL: 5 min)             │     │   │
│   │   │   tool:catalog:hash      ──▶ Catalog checksum for invalidation       │     │   │
│   │   │   tool:{name}:schema     ──▶ Compiled JSON schema (TTL: 1 hour)      │     │   │
│   │   │                                                                       │     │   │
│   │   └───────────────────────────────────────────────────────────────────────┘     │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Routing Engine

### 4.1 Request Routing Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              ROUTING ENGINE ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   Incoming Request                                                                      │
│        │                                                                                │
│        ▼                                                                                │
│   ┌────────────────────────────────────────────────────────────────────────────────┐    │
│   │ 1. TOOL RESOLUTION                                                             │    │
│   │                                                                                │    │
│   │    Request: { "tool_name": "get_dealer_enquiries", "parameters": {...} }       │    │
│   │                          │                                                     │    │
│   │                          ▼                                                     │    │
│   │    ┌─────────────────────────────────────────────────────────────────────┐     │    │
│   │    │  Registry Lookup (Cache → DB)                                       │     │    │
│   │    │  ────────────────────────────                                       │     │    │
│   │    │  1. Check Redis: tool:{name}:definition                             │     │    │
│   │    │  2. If miss → Query PostgreSQL → Populate cache                     │     │    │
│   │    │  3. Return Tool definition or 404                                   │     │    │
│   │    └─────────────────────────────────────────────────────────────────────┘     │    │
│   │                                                                                │    │
│   └────────────────────────────────────────────────────────────────────────────────┘    │
│                          │                                                              │
│                          ▼                                                              │
│   ┌────────────────────────────────────────────────────────────────────────────────┐    │
│   │ 2. PARAMETER MAPPING                                                           │    │
│   │                                                                                │    │
│   │    MCP Parameters ──▶ API Request                                              │    │
│   │                                                                                │    │
│   │    ┌─────────────────────────────────────────────────────────────────────┐     │    │
│   │    │  Input:  { "dealer_id": "DL001", "status": "pending" }              │     │    │
│   │    │                          │                                          │     │    │
│   │    │  Mapping Rules:          ▼                                          │     │    │
│   │    │  ┌──────────────────────────────────────────────────────────┐       │     │    │
│   │    │  │ Path:    /api/v1/dealers/{dealer_id}/enquiries           │       │     │    │
│   │    │  │ Query:   ?status=pending                                 │       │     │    │
│   │    │  │ Headers: Authorization: Bearer {token}                   │       │     │    │
│   │    │  │          X-Subscription-Key: {apim_key}                  │       │     │    │
│   │    │  │          X-Correlation-ID: {correlation_id}              │       │     │    │
│   │    │  └──────────────────────────────────────────────────────────┘       │     │    │
│   │    │                                                                     │     │    │
│   │    └─────────────────────────────────────────────────────────────────────┘     │    │
│   │                                                                                │    │
│   └────────────────────────────────────────────────────────────────────────────────┘    │
│                          │                                                              │
│                          ▼                                                              │
│   ┌────────────────────────────────────────────────────────────────────────────────┐    │
│   │ 3. BACKEND DISPATCH                                                            │    │
│   │                                                                                │    │
│   │    ┌─────────────────────────────────────────────────────────────────────┐     │    │
│   │    │                   API Gateway Client                                │     │    │
│   │    │                                                                     │     │    │
│   │    │   ┌──────────────┐                                                  │     │    │
│   │    │   │ Mock Gateway │ ◀── API_GATEWAY_MODE=mock                        │     │    │
│   │    │   │ (Testing)    │                                                  │     │    │
│   │    │   └──────────────┘                                                  │     │    │
│   │    │          OR                                                         │     │    │
│   │    │   ┌──────────────┐                                                  │     │    │
│   │    │   │ MSIL APIM    │ ◀── API_GATEWAY_MODE=msil_apim                   │     │    │
│   │    │   │ (Production) │                                                  │     │    │
│   │    │   └──────────────┘                                                  │     │    │
│   │    │                                                                     │     │    │
│   │    │   Features:                                                         │     │    │
│   │    │   • mTLS authentication                                             │     │    │
│   │    │   • Circuit breaker (5 failures → open)                             │     │    │
│   │    │   • Retry with exponential backoff (max 3)                          │     │    │
│   │    │   • Request timeout (30s)                                           │     │    │
│   │    │                                                                     │     │    │
│   │    └─────────────────────────────────────────────────────────────────────┘     │    │
│   │                                                                                │    │
│   └────────────────────────────────────────────────────────────────────────────────┘    │
│                          │                                                              │
│                          ▼                                                              │
│   ┌────────────────────────────────────────────────────────────────────────────────┐    │
│   │ 4. RESPONSE TRANSFORMATION                                                     │    │
│   │                                                                                │    │
│   │    API Response ──▶ MCP Response                                               │    │
│   │                                                                                │    │
│   │    ┌─────────────────────────────────────────────────────────────────────┐     │    │
│   │    │  • Schema validation against output_schema                          │     │    │
│   │    │  • PII masking (if configured)                                      │     │    │
│   │    │  • Error normalization to MCP error format                          │     │    │
│   │    │  • Metadata enrichment (latency, source)                            │     │    │
│   │    └─────────────────────────────────────────────────────────────────────┘     │    │
│   │                                                                                │    │
│   └────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Validation Modules

### 5.1 Validation Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              VALIDATION PIPELINE                                         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   Input Request                                                                         │
│        │                                                                                │
│        ▼                                                                                │
│   ┌────────────────────────────────────────────────────────────────────────────────┐    │
│   │ STAGE 1: SCHEMA VALIDATION                                                     │    │
│   │                                                                                │    │
│   │   ┌──────────────────────────────────────────────────────────────────────┐     │    │
│   │   │ JSON Schema Validator                                                │     │    │
│   │   │                                                                      │     │    │
│   │   │ • Type checking (string, number, array, object)                      │     │    │
│   │   │ • Required field validation                                          │     │    │
│   │   │ • Format validation (email, date, uri)                               │     │    │
│   │   │ • Pattern matching (regex)                                           │     │    │
│   │   │ • Enum constraints                                                   │     │    │
│   │   │ • Min/max value bounds                                               │     │    │
│   │   └──────────────────────────────────────────────────────────────────────┘     │    │
│   │                                                                                │    │
│   │   Error: 422 Unprocessable Entity                                              │    │
│   └────────────────────────────────────────────────────────────────────────────────┘    │
│        │ PASS                                                                           │
│        ▼                                                                                │
│   ┌────────────────────────────────────────────────────────────────────────────────┐    │
│   │ STAGE 2: BUSINESS RULE VALIDATION                                              │    │
│   │                                                                                │    │
│   │   ┌──────────────────────────────────────────────────────────────────────┐     │    │
│   │   │ Custom Validators                                                    │     │    │
│   │   │                                                                      │     │    │
│   │   │ • Allowlist check: Is value in allowed set?                          │     │    │
│   │   │ • Denylist check: Is value in blocked set?                           │     │    │
│   │   │ • Cross-field validation: Does A + B make sense?                     │     │    │
│   │   │ • Date range validation: Is date_from < date_to?                     │     │    │
│   │   │ • Reference validation: Does dealer_id exist?                        │     │    │
│   │   └──────────────────────────────────────────────────────────────────────┘     │    │
│   │                                                                                │    │
│   │   Error: 400 Bad Request                                                       │    │
│   └────────────────────────────────────────────────────────────────────────────────┘    │
│        │ PASS                                                                           │
│        ▼                                                                                │
│   ┌────────────────────────────────────────────────────────────────────────────────┐    │
│   │ STAGE 3: SECURITY VALIDATION                                                   │    │
│   │                                                                                │    │
│   │   ┌──────────────────────────────────────────────────────────────────────┐     │    │
│   │   │ Injection Detection                                                  │     │    │
│   │   │                                                                      │     │    │
│   │   │ • SQL injection patterns: '; DROP TABLE; --                          │     │    │
│   │   │ • XSS patterns: <script>, javascript:                                │     │    │
│   │   │ • Command injection: $(cmd), `cmd`, | cmd                            │     │    │
│   │   │ • Path traversal: ../, ..\                                           │     │    │
│   │   │ • Prompt injection: "ignore previous", "system:"                     │     │    │
│   │   └──────────────────────────────────────────────────────────────────────┘     │    │
│   │                                                                                │    │
│   │   Error: 400 Bad Request (logged as security event)                            │    │
│   └────────────────────────────────────────────────────────────────────────────────┘    │
│        │ PASS                                                                           │
│        ▼                                                                                │
│   ┌────────────────────────────────────────────────────────────────────────────────┐    │
│   │ STAGE 4: SIZE/LIMIT VALIDATION                                                 │    │
│   │                                                                                │    │
│   │   ┌──────────────────────────────────────────────────────────────────────┐     │    │
│   │   │ Resource Limits                                                      │     │    │
│   │   │                                                                      │     │    │
│   │   │ • Max request body: 1MB                                              │     │    │
│   │   │ • Max string length: 10,000 chars                                    │     │    │
│   │   │ • Max array items: 1,000                                             │     │    │
│   │   │ • Max nesting depth: 10                                              │     │    │
│   │   │ • Max batch size: 20 tools                                           │     │    │
│   │   └──────────────────────────────────────────────────────────────────────┘     │    │
│   │                                                                                │    │
│   │   Error: 413 Payload Too Large                                                 │    │
│   └────────────────────────────────────────────────────────────────────────────────┘    │
│        │ PASS                                                                           │
│        ▼                                                                                │
│   Validation Complete ✓                                                                 │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Caching Strategies

### 6.1 Multi-Tier Cache Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              CACHING ARCHITECTURE                                        │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           CACHE LAYERS                                          │   │
│   │                                                                                 │   │
│   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │ L1: IN-MEMORY CACHE (Application)                                       │   │   │
│   │   │                                                                         │   │   │
│   │   │ • LRU Cache (functools.lru_cache)                                       │   │   │
│   │   │ • Settings configuration (hot data)                                     │   │   │
│   │   │ • JSON Schema compilations                                              │   │   │
│   │   │ • TTL: Process lifetime / explicit invalidation                         │   │   │
│   │   │ • Size: ~100MB per instance                                             │   │   │
│   │   │                                                                         │   │   │
│   │   └─────────────────────────────────────────────────────────────────────────┘   │   │
│   │                                     │                                           │   │
│   │                                     ▼ Miss                                      │   │
│   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │ L2: DISTRIBUTED CACHE (Redis)                                           │   │   │
│   │   │                                                                         │   │   │
│   │   │ • Tool definitions: TTL 5 min                                           │   │   │
│   │   │ • User sessions: TTL 60 min                                             │   │   │
│   │   │ • JWKS public keys: TTL 1 hour                                          │   │   │
│   │   │ • API responses: TTL 30 sec (selective)                                 │   │   │
│   │   │ • Rate limit counters: TTL 1 min                                        │   │   │
│   │   │ • Idempotency keys: TTL 24 hours                                        │   │   │
│   │   │                                                                         │   │   │
│   │   └─────────────────────────────────────────────────────────────────────────┘   │   │
│   │                                     │                                           │   │
│   │                                     ▼ Miss                                      │   │
│   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │ L3: PERSISTENT STORE (PostgreSQL)                                       │   │   │
│   │   │                                                                         │   │   │
│   │   │ • Source of truth for all data                                          │   │   │
│   │   │ • Tools, users, policies, audit logs                                    │   │   │
│   │   │ • Connection pooling: 5-15 connections                                  │   │   │
│   │   │                                                                         │   │   │
│   │   └─────────────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        CACHE INVALIDATION                                       │   │
│   │                                                                                 │   │
│   │   ┌──────────────────┐                                                         │   │
│   │   │ Invalidation     │                                                         │   │
│   │   │ Triggers         │                                                         │   │
│   │   │                  │                                                         │   │
│   │   │ • Tool update    │───▶ Delete tool:{name}:* from Redis                     │   │
│   │   │ • Settings change│───▶ Publish settings:invalidate event                   │   │
│   │   │ • User logout    │───▶ Delete session:{user_id}:*                          │   │
│   │   │ • TTL expiry     │───▶ Automatic Redis eviction                            │   │
│   │   │                  │                                                         │   │
│   │   └──────────────────┘                                                         │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Redis Key Structure

| Key Pattern | Purpose | TTL |
|-------------|---------|-----|
| `tool:{name}:definition` | Full tool JSON | 5 min |
| `tool:catalog:hash` | Catalog checksum | 5 min |
| `session:{user_id}:{session_id}` | User session data | 60 min |
| `ratelimit:{user_id}:{endpoint}` | Rate limit counter | 1 min |
| `idempotency:{key_hash}` | Idempotent response | 24 hours |
| `jwks:{issuer}:keys` | OIDC public keys | 1 hour |
| `policy:{role}:{resource}` | Cached policy decision | 5 min |

---

## 7. Observability Stack

### 7.1 Observability Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              OBSERVABILITY ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           DATA COLLECTION                                       │   │
│   │                                                                                 │   │
│   │   ┌────────────────┐   ┌────────────────┐   ┌────────────────┐                 │   │
│   │   │    LOGS        │   │    METRICS     │   │    TRACES      │                 │   │
│   │   │                │   │                │   │                │                 │   │
│   │   │ • Structured   │   │ • Prometheus   │   │ • OpenTelemetry│                 │   │
│   │   │   JSON format  │   │   exporters    │   │   SDK          │                 │   │
│   │   │ • Log levels   │   │ • Custom       │   │ • Span context │                 │   │
│   │   │ • Correlation  │   │   business     │   │ • Propagation  │                 │   │
│   │   │   ID in every  │   │   metrics      │   │   headers      │                 │   │
│   │   │   log line     │   │                │   │                │                 │   │
│   │   └────────────────┘   └────────────────┘   └────────────────┘                 │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                               │
│                                         ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           AWS OBSERVABILITY SERVICES                            │   │
│   │                                                                                 │   │
│   │   ┌────────────────┐   ┌────────────────┐   ┌────────────────┐                 │   │
│   │   │  CloudWatch    │   │  CloudWatch    │   │    AWS         │                 │   │
│   │   │    Logs        │   │   Metrics      │   │   X-Ray        │                 │   │
│   │   │                │   │                │   │                │                 │   │
│   │   │ • Log Groups   │   │ • Custom       │   │ • Service Map  │                 │   │
│   │   │ • Log Streams  │   │   Namespaces   │   │ • Trace        │                 │   │
│   │   │ • Insights     │   │ • Alarms       │   │   Analysis     │                 │   │
│   │   │   Queries      │   │ • Dashboards   │   │ • Latency      │                 │   │
│   │   │                │   │                │   │   Histograms   │                 │   │
│   │   └────────────────┘   └────────────────┘   └────────────────┘                 │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                               │
│                                         ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           DASHBOARDS & ALERTING                                 │   │
│   │                                                                                 │   │
│   │   ┌────────────────────────────────────────────────────────────────────────┐    │   │
│   │   │ CloudWatch Dashboards                                                  │    │   │
│   │   │                                                                        │    │   │
│   │   │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │    │   │
│   │   │  │ API Performance │  │ Tool Execution  │  │ Security Events │        │    │   │
│   │   │  │                 │  │                 │  │                 │        │    │   │
│   │   │  │ • Request rate  │  │ • Invocations   │  │ • Auth failures │        │    │   │
│   │   │  │ • Latency p50,  │  │ • Success rate  │  │ • Policy denials│        │    │   │
│   │   │  │   p95, p99      │  │ • Errors by     │  │ • Rate limit    │        │    │   │
│   │   │  │ • Error rate    │  │   tool          │  │   violations    │        │    │   │
│   │   │  │ • Throughput    │  │ • Latency dist  │  │ • Elevation     │        │    │   │
│   │   │  │                 │  │                 │  │   requests      │        │    │   │
│   │   │  └─────────────────┘  └─────────────────┘  └─────────────────┘        │    │   │
│   │   │                                                                        │    │   │
│   │   └────────────────────────────────────────────────────────────────────────┘    │   │
│   │                                                                                 │   │
│   │   ┌────────────────────────────────────────────────────────────────────────┐    │   │
│   │   │ CloudWatch Alarms                                                      │    │   │
│   │   │                                                                        │    │   │
│   │   │  • Error rate > 5% for 5 minutes ──▶ SNS ──▶ PagerDuty               │    │   │
│   │   │  • Latency p99 > 1s for 10 minutes ──▶ SNS ──▶ Slack                  │    │   │
│   │   │  • Auth failures > 100/min ──▶ SNS ──▶ Security Team                  │    │   │
│   │   │  • Circuit breaker open ──▶ SNS ──▶ On-Call                          │    │   │
│   │   │                                                                        │    │   │
│   │   └────────────────────────────────────────────────────────────────────────┘    │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Log Format

```json
{
  "timestamp": "2026-01-31T10:30:00.000Z",
  "level": "INFO",
  "service": "mcp-server",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "trace_id": "1234567890abcdef",
  "span_id": "abcdef123456",
  "user_id": "user@msil.com",
  "event": "tool_execution",
  "tool_name": "get_dealer_enquiries",
  "duration_ms": 156,
  "status": "success",
  "metadata": {
    "dealer_id": "DL001",
    "result_count": 42
  }
}
```

### 7.3 Key Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `mcp_requests_total` | Counter | Total API requests |
| `mcp_request_duration_seconds` | Histogram | Request latency |
| `mcp_tool_executions_total` | Counter | Tool invocations by name |
| `mcp_tool_errors_total` | Counter | Tool execution errors |
| `mcp_auth_failures_total` | Counter | Authentication failures |
| `mcp_policy_decisions_total` | Counter | Policy allow/deny |
| `mcp_circuit_breaker_state` | Gauge | CB state (0=closed, 1=open) |
| `mcp_cache_hits_total` | Counter | Cache hit rate |
| `mcp_active_connections` | Gauge | Current DB connections |

---

## 8. Database Schema

### 8.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE SCHEMA                                             │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐              │
│   │     users       │       │      tools      │       │  audit_events   │              │
│   ├─────────────────┤       ├─────────────────┤       ├─────────────────┤              │
│   │ id (PK)         │       │ id (PK)         │       │ id (PK)         │              │
│   │ username        │       │ name (UNIQUE)   │       │ event_id        │              │
│   │ email           │       │ description     │       │ timestamp       │              │
│   │ hashed_password │       │ version         │       │ correlation_id  │              │
│   │ role            │◀──────│ input_schema    │       │ user_id (FK)    │──────▶       │
│   │ is_active       │       │ output_schema   │       │ event_type      │              │
│   │ created_at      │       │ api_endpoint    │       │ tool_name       │              │
│   │ updated_at      │       │ http_method     │       │ action          │              │
│   └────────┬────────┘       │ risk_level      │       │ status          │              │
│            │                │ allowed_roles   │       │ metadata        │              │
│            │                │ domain          │       │ checksum        │              │
│            │                │ is_active       │       └─────────────────┘              │
│            │                │ created_at      │                                        │
│            │                └────────┬────────┘                                        │
│            │                         │                                                 │
│            │                         │                                                 │
│            ▼                         ▼                                                 │
│   ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐              │
│   │  user_sessions  │       │ tool_executions │       │    policies     │              │
│   ├─────────────────┤       ├─────────────────┤       ├─────────────────┤              │
│   │ id (PK)         │       │ id (PK)         │       │ id (PK)         │              │
│   │ user_id (FK)    │       │ tool_id (FK)    │       │ name (UNIQUE)   │              │
│   │ token_hash      │       │ user_id (FK)    │       │ role            │              │
│   │ created_at      │       │ correlation_id  │       │ resource        │              │
│   │ expires_at      │       │ parameters      │       │ action          │              │
│   │ is_revoked      │       │ status          │       │ effect          │              │
│   └─────────────────┘       │ latency_ms      │       │ conditions      │              │
│                             │ error_message   │       │ is_active       │              │
│                             │ created_at      │       └─────────────────┘              │
│                             └─────────────────┘                                        │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Error Handling

### 9.1 Error Response Format

```json
{
  "error": {
    "code": "TOOL_EXECUTION_FAILED",
    "message": "Failed to execute tool: get_dealer_enquiries",
    "details": {
      "reason": "Backend service unavailable",
      "retry_after": 30
    },
    "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "timestamp": "2026-01-31T10:30:00.000Z"
  }
}
```

### 9.2 Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_FAILED` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Access denied by policy |
| `TOOL_NOT_FOUND` | 404 | Tool does not exist |
| `RATE_LIMITED` | 429 | Rate limit exceeded |
| `TOOL_EXECUTION_FAILED` | 500 | Backend execution error |
| `SERVICE_UNAVAILABLE` | 503 | Circuit breaker open |

---

*Document Classification: Internal | Last Review: January 31, 2026*
