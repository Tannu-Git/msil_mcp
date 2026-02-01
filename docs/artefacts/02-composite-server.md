# Composite MCP Server Artefacts

**Document Version**: 2.1  
**Last Updated**: February 1, 2026  
**Classification**: Internal

---

## 1. Overview

This document describes the Composite MCP Server architecture, which aggregates tools from multiple backend services into a unified MCP interface for Host/Agent application consumption.

> **📋 MCP Protocol Note**: The Host/Agent application (not the LLM directly) communicates with the MCP Server. The LLM generates tool call intents, and the Host application's MCP Client handles the actual protocol communication including `initialize`, `tools/list`, and `tools/call` operations.

---

## 2. Composite Server Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              COMPOSITE MCP SERVER ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                         HOST / AGENT APPLICATION                                │   │
│   │                     (Contains LLM + MCP Client)                                 │   │
│   └────────────────────────────────────┬────────────────────────────────────────────┘   │
│                                        │                                                │
│                                        │ MCP Protocol (JSON-RPC 2.0)                    │
│                                        │ (initialize, tools/list, tools/call)          │
│                                        ▼                                                │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                         COMPOSITE MCP SERVER                                    │   │
│   │                                                                                 │   │
│   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │                     TOOL AGGREGATION LAYER                              │   │   │
│   │   │                                                                         │   │   │
│   │   │   ┌─────────────────────────────────────────────────────────────────┐   │   │   │
│   │   │   │                   Unified Tool Catalog                          │   │   │   │
│   │   │   │                                                                 │   │   │   │
│   │   │   │   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │   │   │   │
│   │   │   │   │ Dealer  │ │Inventory│ │ Booking │ │Customer │ │ Payment │ │   │   │   │
│   │   │   │   │ Tools   │ │ Tools   │ │ Tools   │ │ Tools   │ │ Tools   │ │   │   │   │
│   │   │   │   │  (12)   │ │   (8)   │ │  (10)   │ │   (6)   │ │   (4)   │ │   │   │   │
│   │   │   │   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ │   │   │   │
│   │   │   │                                                                 │   │   │   │
│   │   │   │   Total: 40 Tools │ Active: 38 │ Deprecated: 2                 │   │   │   │
│   │   │   │                                                                 │   │   │   │
│   │   │   └─────────────────────────────────────────────────────────────────┘   │   │   │
│   │   │                                                                         │   │   │
│   │   └─────────────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                                 │   │
│   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │                     ROUTING & DISPATCH LAYER                            │   │   │
│   │   │                                                                         │   │   │
│   │   │   Tool Request ──▶ Lookup ──▶ Authorize ──▶ Route ──▶ Execute          │   │   │
│   │   │                                                                         │   │   │
│   │   │   ┌───────────────────────────────────────────────────────────────────┐ │   │   │
│   │   │   │ Router Logic                                                      │ │   │   │
│   │   │   │                                                                   │ │   │   │
│   │   │   │ tool_name         ──▶  Backend Service                            │ │   │   │
│   │   │   │ ─────────               ───────────────                           │ │   │   │
│   │   │   │ get_dealer_*      ──▶  APIM → Dealer Service                      │ │   │   │
│   │   │   │ get_vehicle_*     ──▶  APIM → Inventory Service                   │ │   │   │
│   │   │   │ create_booking    ──▶  APIM → Booking Service                     │ │   │   │
│   │   │   │ get_customer_*    ──▶  APIM → Customer Service                    │ │   │   │
│   │   │   │ process_payment   ──▶  APIM → Payment Gateway                     │ │   │   │
│   │   │   │                                                                   │ │   │   │
│   │   │   └───────────────────────────────────────────────────────────────────┘ │   │   │
│   │   │                                                                         │   │   │
│   │   └─────────────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                                 │   │
│   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │                     CROSS-CUTTING CONCERNS                              │   │   │
│   │   │                                                                         │   │   │
│   │   │   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │   │   │
│   │   │   │  Auth   │ │ Policy  │ │  Audit  │ │  Cache  │ │ Metrics │          │   │   │
│   │   │   │         │ │  (OPA)  │ │  (S3)   │ │ (Redis) │ │ (CW)    │          │   │   │
│   │   │   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘          │   │   │
│   │   │                                                                         │   │   │
│   │   └─────────────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                                │
│                                        ▼                                                │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              MSIL APIM                                          │   │
│   │                                                                                 │   │
│   │   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐          │   │
│   │   │ Dealer  │   │Inventory│   │ Booking │   │Customer │   │ Payment │          │   │
│   │   │ API     │   │   API   │   │   API   │   │   API   │   │   API   │          │   │
│   │   └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘          │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Server Configuration

### 3.1 Main Configuration

```yaml
# config/mcp-server.yaml

server:
  name: "msil-mcp-composite"
  version: "2.0.0"
  environment: "${ENVIRONMENT:production}"
  
  # Network
  host: "0.0.0.0"
  port: 8000
  workers: 4
  
  # Timeouts
  request_timeout: 30
  shutdown_timeout: 30

# Tool Sources Configuration
tool_sources:
  - name: "dealer-service"
    type: "openapi"
    spec_url: "https://apim.msil.com/dealer/v1/openapi.yaml"
    refresh_interval: 3600  # 1 hour
    enabled: true
    options:
      default_risk_level: "read"
      path_prefix: "/v1/dealers"
  
  - name: "inventory-service"
    type: "openapi"
    spec_url: "https://apim.msil.com/inventory/v1/openapi.yaml"
    refresh_interval: 3600
    enabled: true
  
  - name: "booking-service"
    type: "openapi"
    spec_url: "https://apim.msil.com/booking/v1/openapi.yaml"
    refresh_interval: 3600
    enabled: true
  
  - name: "custom-tools"
    type: "directory"
    path: "/app/tools/custom"
    watch: true

# API Gateway
api_gateway:
  mode: "${API_GATEWAY_MODE:msil_apim}"
  base_url: "${APIM_BASE_URL}"
  subscription_key: "${APIM_SUBSCRIPTION_KEY}"
  
  # mTLS
  mtls:
    enabled: true
    client_cert: "/etc/secrets/mtls/client.pem"
    client_key: "/etc/secrets/mtls/client.key"
    ca_cert: "/etc/secrets/mtls/ca.pem"
  
  # Resilience
  circuit_breaker:
    threshold: 5
    timeout: 30
  retry:
    max_attempts: 3
    backoff_base: 1.0

# Authentication
auth:
  provider: "azure_ad"
  jwks_uri: "https://login.microsoftonline.com/${TENANT_ID}/discovery/v2.0/keys"
  issuer: "https://login.microsoftonline.com/${TENANT_ID}/v2.0"
  audience: "api://msil-mcp-server"
  
  # PIM Integration
  pim:
    enabled: true
    check_endpoint: "${PIM_ENDPOINT}/api/pim/check-elevation"
    elevation_url: "${PIM_PORTAL_URL}"

# Authorization
authorization:
  provider: "opa"
  endpoint: "http://localhost:8181"
  policy_path: "/v1/data/msil/authz"
  
  # Role Hierarchy
  roles:
    viewer:
      inherits: []
      risk_levels: ["read"]
    operator:
      inherits: ["viewer"]
      risk_levels: ["read", "write"]
    admin:
      inherits: ["operator"]
      risk_levels: ["read", "write", "privileged"]

# Database
database:
  url: "postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:5432/${DB_NAME}"
  pool_size: 5
  max_overflow: 10
  ssl: true

# Cache
cache:
  provider: "redis"
  url: "rediss://:${REDIS_PASSWORD}@${REDIS_HOST}:6379"
  default_ttl: 300

# Audit
audit:
  provider: "s3_worm"
  bucket: "${AUDIT_BUCKET}"
  retention_days: 2555  # 7 years
```

### 3.2 Tool Registry Configuration

```yaml
# config/tool-registry.yaml

registry:
  # Storage
  storage:
    type: "postgresql"
    table_name: "tools"
    version_table: "tool_versions"
  
  # Caching
  cache:
    enabled: true
    ttl: 300  # 5 minutes
    prefix: "tool:"
  
  # Validation
  validation:
    strict_mode: true
    require_examples: true
    require_description_min_length: 20

# Auto-import settings
auto_import:
  enabled: true
  schedule: "0 */6 * * *"  # Every 6 hours
  on_startup: true
  
  # Defaults for imported tools
  defaults:
    risk_level: "read"
    rate_limit_tier: "standard"
    audit_level: "basic"
  
  # Mapping rules
  risk_mapping:
    http_method:
      GET: "read"
      POST: "write"
      PUT: "write"
      PATCH: "write"
      DELETE: "privileged"
    scope_pattern:
      "*.read": "read"
      "*.write": "write"
      "*.admin": "privileged"
      "*.delete": "privileged"

# Discovery settings
discovery:
  # What to expose in tool catalog
  include_deprecated: false
  include_inactive: false
  
  # Filtering
  filters:
    by_domain: true
    by_risk_level: true
    by_role: true
```

---

## 4. Server Components

### 4.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              SERVER COMPONENTS                                           │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              app/                                               │   │
│   │                                                                                 │   │
│   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │ main.py                                                                 │   │   │
│   │   │                                                                         │   │   │
│   │   │ • FastAPI application factory                                           │   │   │
│   │   │ • Middleware registration                                               │   │   │
│   │   │ • Router mounting                                                       │   │   │
│   │   │ • Lifespan management (startup/shutdown)                                │   │   │
│   │   │                                                                         │   │   │
│   │   └─────────────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                                 │   │
│   │   ┌───────────────────────────┐   ┌───────────────────────────┐                │   │
│   │   │ api/                      │   │ core/                     │                │   │
│   │   │                           │   │                           │                │   │
│   │   │ ├── mcp/                  │   │ ├── auth.py               │                │   │
│   │   │ │   ├── router.py         │   │ │   └── JWT validation    │                │   │
│   │   │ │   ├── tools.py          │   │ │   └── JWKS client       │                │   │
│   │   │ │   └── execute.py        │   │ │                         │                │   │
│   │   │ │                         │   │ ├── policy.py             │                │   │
│   │   │ ├── admin/                │   │ │   └── OPA client        │                │   │
│   │   │ │   ├── router.py         │   │ │   └── RBAC engine       │                │   │
│   │   │ │   ├── tools.py          │   │ │                         │                │   │
│   │   │ │   └── users.py          │   │ ├── audit.py              │                │   │
│   │   │ │                         │   │ │   └── Event builder     │                │   │
│   │   │ └── chat/                 │   │ │   └── S3 WORM client    │                │   │
│   │   │     └── router.py         │   │ │                         │                │   │
│   │   │                           │   │ └── cache.py              │                │   │
│   │   └───────────────────────────┘   │     └── Redis client      │                │   │
│   │                                   └───────────────────────────┘                │   │
│   │                                                                                 │   │
│   │   ┌───────────────────────────┐   ┌───────────────────────────┐                │   │
│   │   │ services/                 │   │ models/                   │                │   │
│   │   │                           │   │                           │                │   │
│   │   │ ├── tool_registry.py      │   │ ├── tool.py               │                │   │
│   │   │ │   └── CRUD operations   │   │ │   └── Tool model        │                │   │
│   │   │ │   └── Import/export     │   │ │                         │                │   │
│   │   │ │                         │   │ ├── user.py               │                │   │
│   │   │ ├── tool_executor.py      │   │ │   └── User model        │                │   │
│   │   │ │   └── Execute single    │   │ │                         │                │   │
│   │   │ │   └── Execute batch     │   │ ├── audit_event.py        │                │   │
│   │   │ │                         │   │ │   └── Event model       │                │   │
│   │   │ ├── openapi_importer.py   │   │ │                         │                │   │
│   │   │ │   └── Parse specs       │   │ └── schemas.py            │                │   │
│   │   │ │   └── Generate tools    │   │     └── Pydantic models   │                │   │
│   │   │ │                         │   │                           │                │   │
│   │   │ └── api_gateway.py        │   └───────────────────────────┘                │   │
│   │   │     └── APIM client       │                                                │   │
│   │   │     └── Mock gateway      │                                                │   │
│   │   │                           │                                                │   │
│   │   └───────────────────────────┘                                                │   │
│   │                                                                                 │   │
│   │   ┌───────────────────────────┐   ┌───────────────────────────┐                │   │
│   │   │ middleware/               │   │ utils/                    │                │   │
│   │   │                           │   │                           │                │   │
│   │   │ ├── auth.py               │   │ ├── validation.py         │                │   │
│   │   │ ├── correlation.py        │   │ ├── security.py           │                │   │
│   │   │ ├── rate_limit.py         │   │ ├── logging.py            │                │   │
│   │   │ ├── logging.py            │   │ └── helpers.py            │                │   │
│   │   │ └── error_handler.py      │   │                           │                │   │
│   │   │                           │   │                           │                │   │
│   │   └───────────────────────────┘   └───────────────────────────┘                │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. MCP Protocol Implementation

### 5.1 Protocol Endpoints

```python
# MCP Protocol Endpoints

# 1. Tool Discovery
@router.get("/api/mcp/tools")
async def list_tools(
    domain: Optional[str] = None,
    risk_level: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> ToolCatalog:
    """
    Returns list of available tools filtered by user's role.
    """
    pass

# 2. Tool Schema
@router.get("/api/mcp/tools/{tool_name}/schema")
async def get_tool_schema(
    tool_name: str,
    current_user: User = Depends(get_current_user)
) -> ToolSchema:
    """
    Returns detailed schema for a specific tool.
    """
    pass

# 3. Tool Execution
@router.post("/api/mcp/execute")
async def execute_tool(
    request: ToolExecutionRequest,
    idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    current_user: User = Depends(get_current_user)
) -> ToolExecutionResponse:
    """
    Execute a single tool with provided parameters.
    """
    pass

# 4. Batch Execution
@router.post("/api/mcp/batch")
async def execute_batch(
    request: BatchExecutionRequest,
    current_user: User = Depends(get_current_user)
) -> BatchExecutionResponse:
    """
    Execute multiple tools in a single request.
    Supports parallel and sequential execution modes.
    """
    pass
```

### 5.2 Request/Response Formats

```json
// Tool Execution Request
{
  "tool_name": "get_dealer_enquiries",
  "parameters": {
    "dealer_id": "DL123456",
    "status": "pending",
    "limit": 10
  },
  "context": {
    "conversation_id": "conv-123",
    "request_id": "req-456"
  }
}

// Tool Execution Response
{
  "success": true,
  "tool_name": "get_dealer_enquiries",
  "result": {
    "enquiries": [
      {
        "enquiry_id": "ENQ001",
        "customer_name": "John Doe",
        "vehicle_model": "Swift",
        "status": "pending"
      }
    ],
    "total_count": 1
  },
  "metadata": {
    "execution_time_ms": 156,
    "correlation_id": "a1b2c3d4-e5f6-7890",
    "cached": false
  }
}

// Batch Execution Request
{
  "execution_mode": "parallel",  // or "sequential"
  "tools": [
    {
      "tool_name": "get_dealer_profile",
      "parameters": {"dealer_id": "DL123456"}
    },
    {
      "tool_name": "get_dealer_enquiries",
      "parameters": {"dealer_id": "DL123456", "limit": 5}
    }
  ],
  "stop_on_error": false
}

// Batch Execution Response
{
  "success": true,
  "results": [
    {
      "tool_name": "get_dealer_profile",
      "success": true,
      "result": {...}
    },
    {
      "tool_name": "get_dealer_enquiries",
      "success": true,
      "result": {...}
    }
  ],
  "metadata": {
    "total_execution_time_ms": 234,
    "correlation_id": "a1b2c3d4-e5f6-7890"
  }
}
```

---

## 6. Deployment Artefacts

### 6.1 Docker Image

```dockerfile
# Dockerfile.hardened
FROM python:3.13-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.13-slim

# Security: Non-root user
RUN groupadd -r mcp && useradd -r -g mcp mcp

WORKDIR /app

# Copy wheels and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application
COPY --chown=mcp:mcp app/ ./app/
COPY --chown=mcp:mcp config/ ./config/

# Security hardening
USER mcp
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6.2 Kubernetes Manifests

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
  namespace: mcp-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      serviceAccountName: mcp-server-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
        - name: mcp-server
          image: mcp-server:2.0.0
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: mcp-config
            - secretRef:
                name: mcp-secrets
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "1000m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
```

---

## 7. Health & Readiness

### 7.1 Health Check Endpoints

```python
@router.get("/health")
async def health_check() -> dict:
    """
    Liveness probe - is the server running?
    """
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> dict:
    """
    Readiness probe - is the server ready to accept traffic?
    """
    checks = {
        "database": await check_database(db),
        "redis": await check_redis(redis),
        "tool_registry": await check_tool_registry()
    }
    
    all_healthy = all(c["healthy"] for c in checks.values())
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks
    }
```

---

*Document Classification: Internal | Last Review: January 31, 2026*
