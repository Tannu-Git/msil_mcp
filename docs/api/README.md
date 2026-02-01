# API Reference

**Document Version**: 2.1  
**Last Updated**: February 1, 2026  
**Classification**: Internal

---

## 1. Overview

This document provides the complete API reference for the MSIL MCP Platform, including MCP protocol endpoints, admin APIs, and chat APIs.

**Note**: The **Host/Agent application** (with embedded MCP Client) communicates with these APIs. The LLM only decides which tool to call—it does not speak MCP directly.

---

## 2. Base Information

| Property | Value |
|----------|-------|
| **Base URL (Production)** | `https://mcp.msil.com/api` |
| **Base URL (Staging)** | `https://mcp-staging.msil.com/api` |
| **API Version** | `v1` |
| **Content Type** | `application/json` |
| **Authentication** | Bearer Token (OAuth2/OIDC via MSIL IdP) |

---

## 3. Authentication

### 3.1 OAuth2 Token

All API requests require a valid JWT token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
```

### 3.2 Token Claims

```json
{
  "iss": "<MSIL_IDP_ISSUER>",
  "aud": "<MSIL_MCP_API_AUDIENCE>",
  "sub": "user-object-id",
  "preferred_username": "user@msil.com",
  "roles": ["operator"],
  "groups": ["dealer-ops"],
  "exp": 1706698200
}
```

---

## 4. MCP Protocol APIs

### 4.0 Initialize (Required First Step)

Before calling any other MCP methods, clients **must** perform the initialize handshake:

```http
POST /api/mcp
```

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    },
    "clientInfo": {
      "name": "msil-host-app",
      "version": "1.0.0"
    }
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {
        "listChanged": true
      }
    },
    "serverInfo": {
      "name": "msil-mcp-server",
      "version": "1.0.0"
    }
  }
}
```

After receiving the response, send the `initialized` notification:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

### 4.1 List Tools

Get available tools filtered by user's permissions.

```http
GET /api/mcp/tools
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `domain` | string | No | Filter by business domain |
| `risk_level` | string | No | Filter by risk level (read, write, privileged) |
| `search` | string | No | Search tool names/descriptions |
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 20, max: 100) |

**Response:**

```json
{
  "tools": [
    {
      "name": "get_dealer_enquiries",
      "description": "Retrieve enquiries for a specific dealer",
      "version": "1.0.0",
      "risk_level": "read",
      "domain": "dealer",
      "input_schema": {
        "type": "object",
        "properties": {
          "dealer_id": {
            "type": "string",
            "description": "Unique dealer identifier"
          }
        },
        "required": ["dealer_id"]
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 42,
    "total_pages": 3
  },
  "meta": {
    "domains": ["dealer", "inventory", "booking"],
    "risk_levels": ["read", "write"]
  }
}
```

---

### 4.2 Get Tool Schema

Get detailed schema for a specific tool.

```http
GET /api/mcp/tools/{tool_name}/schema
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tool_name` | string | Yes | Tool identifier |

**Response:**

```json
{
  "name": "get_dealer_enquiries",
  "description": "Retrieve enquiries for a specific dealer with optional filtering",
  "version": "1.0.0",
  "input_schema": {
    "type": "object",
    "properties": {
      "dealer_id": {
        "type": "string",
        "description": "Unique dealer identifier",
        "pattern": "^DL[0-9]{6}$"
      },
      "status": {
        "type": "string",
        "enum": ["pending", "contacted", "converted", "lost"]
      },
      "limit": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "default": 20
      }
    },
    "required": ["dealer_id"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "enquiries": {
        "type": "array",
        "items": {"$ref": "#/definitions/Enquiry"}
      },
      "total_count": {"type": "integer"}
    }
  },
  "security": {
    "risk_level": "read",
    "requires_elevation": false,
    "allowed_roles": ["viewer", "operator", "admin"]
  },
  "examples": {
    "positive": [
      {
        "description": "Get all enquiries",
        "input": {"dealer_id": "DL123456"},
        "output": {"enquiries": [...], "total_count": 10}
      }
    ]
  }
}
```

---

### 4.3 Execute Tool

Execute a single tool with provided parameters.

```http
POST /api/mcp/execute
```

**Headers:**

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | Bearer token |
| `X-Idempotency-Key` | No | Unique key for idempotent requests |
| `X-Correlation-ID` | No | Correlation ID for tracing |

**Request Body:**

```json
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
```

**Success Response (200):**

```json
{
  "success": true,
  "tool_name": "get_dealer_enquiries",
  "result": {
    "enquiries": [
      {
        "enquiry_id": "ENQ123456789",
        "customer_name": "John Doe",
        "contact_number": "+91 98***43210",
        "vehicle_model": "Swift ZXi",
        "status": "pending",
        "created_at": "2026-01-31T10:30:00Z"
      }
    ],
    "total_count": 1
  },
  "metadata": {
    "execution_time_ms": 156,
    "correlation_id": "a1b2c3d4-e5f6-7890",
    "cached": false,
    "backend_latency_ms": 142
  }
}
```

**Error Response (4xx/5xx):**

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Invalid parameter: dealer_id must match pattern ^DL[0-9]{6}$",
    "details": {
      "field": "dealer_id",
      "value": "invalid",
      "constraint": "pattern"
    },
    "correlation_id": "a1b2c3d4-e5f6-7890",
    "timestamp": "2026-01-31T10:30:00Z"
  }
}
```

---

### 4.4 Batch Execute

Execute multiple tools in a single request.

```http
POST /api/mcp/batch
```

**Request Body:**

```json
{
  "execution_mode": "parallel",
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
```

**Response:**

```json
{
  "success": true,
  "results": [
    {
      "tool_name": "get_dealer_profile",
      "success": true,
      "result": {
        "dealer_id": "DL123456",
        "name": "Delhi Motors",
        "region": "North"
      }
    },
    {
      "tool_name": "get_dealer_enquiries",
      "success": true,
      "result": {
        "enquiries": [...],
        "total_count": 5
      }
    }
  ],
  "metadata": {
    "total_execution_time_ms": 234,
    "correlation_id": "a1b2c3d4-e5f6-7890"
  }
}
```

---

## 5. Admin APIs

### 5.1 Tool Management

#### List All Tools (Admin)

```http
GET /api/admin/tools
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `include_inactive` | boolean | Include inactive tools |
| `include_deprecated` | boolean | Include deprecated tools |

#### Create Tool

```http
POST /api/admin/tools
```

**Request Body:**

```json
{
  "name": "new_tool_name",
  "description": "Tool description for LLM",
  "version": "1.0.0",
  "input_schema": {...},
  "output_schema": {...},
  "api_config": {
    "endpoint": "/v1/path",
    "method": "GET"
  },
  "security_config": {
    "risk_level": "read",
    "allowed_roles": ["viewer", "operator", "admin"]
  }
}
```

#### Update Tool

```http
PUT /api/admin/tools/{tool_name}
```

#### Deactivate Tool

```http
DELETE /api/admin/tools/{tool_name}
```

### 5.2 Import OpenAPI

```http
POST /api/admin/tools/import-openapi
```

**Request Body:**

```json
{
  "spec_url": "https://api.msil.com/service/v1/openapi.yaml",
  "options": {
    "auto_generate_names": true,
    "default_risk_level": "read",
    "dry_run": false
  }
}
```

---

### 5.3 User Management

#### List Users

```http
GET /api/admin/users
```

#### Get User

```http
GET /api/admin/users/{user_id}
```

#### Update User Role

```http
PATCH /api/admin/users/{user_id}/role
```

**Request Body:**

```json
{
  "role": "operator"
}
```

---

### 5.4 Audit Logs

#### Query Audit Events

```http
GET /api/admin/audit
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | string | Filter by user |
| `tool_name` | string | Filter by tool |
| `event_type` | string | Filter by event type |
| `from_date` | string | Start date (ISO 8601) |
| `to_date` | string | End date (ISO 8601) |
| `page` | integer | Page number |
| `page_size` | integer | Items per page |

**Response:**

```json
{
  "events": [
    {
      "event_id": "evt-123",
      "timestamp": "2026-01-31T10:30:00Z",
      "correlation_id": "a1b2c3d4-e5f6",
      "user_id": "user@msil.com",
      "event_type": "tool_execution",
      "tool_name": "get_dealer_enquiries",
      "status": "success",
      "metadata": {
        "dealer_id": "DL123456",
        "duration_ms": 156
      }
    }
  ],
  "pagination": {
    "page": 1,
    "total_items": 1000
  }
}
```

---

### 5.5 Settings

#### Get Settings

```http
GET /api/admin/settings
```

#### Update Settings

```http
PATCH /api/admin/settings
```

**Request Body:**

```json
{
  "rate_limit_requests_per_minute": 100,
  "tool_execution_timeout_ms": 30000,
  "audit_retention_days": 90
}
```

---

## 5. MCP Notifications

### 5.1 Tools List Changed

When the server's tool catalog changes (due to configuration, feature flags, or deployment), the server sends a `notifications/tools/list_changed` notification.

> **📋 Note**: Per MCP specification, notifications have no `id` field and do not expect a response.

**Server → Client Notification:**

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/tools/list_changed"
}
```

**Client Response:**

The client should call `tools/list` to refresh its tool catalog:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/list",
  "params": {}
}
```

### 5.2 Notification Triggers

| Trigger | Description |
|---------|-------------|
| **Feature Flag Change** | Tool enabled/disabled via configuration |
| **Role Policy Update** | RBAC policy changes affecting tool visibility |
| **Hot Deployment** | New tool version deployed without restart |
| **Circuit Breaker** | Backend unavailable, tool temporarily disabled |

### 5.3 Implementation Guidelines

```python
# Server-side: Broadcast tool change notification
async def broadcast_tool_change(mcp_server):
    """Send tools/list_changed to all connected clients."""
    notification = {
        "jsonrpc": "2.0",
        "method": "notifications/tools/list_changed"
    }
    await mcp_server.broadcast_notification(notification)
```

```python
# Client-side: Handle tool change notification
@mcp_client.on_notification("notifications/tools/list_changed")
async def handle_tool_change():
    """Refresh tool catalog when server notifies of changes."""
    tools = await mcp_client.call("tools/list", {})
    update_local_tool_catalog(tools)
```

---

## 6. Chat APIs

### 6.1 Create Session

```http
POST /api/chat/sessions
```

**Response:**

```json
{
  "session_id": "sess-abc123",
  "created_at": "2026-01-31T10:30:00Z",
  "expires_at": "2026-01-31T11:30:00Z"
}
```

### 6.2 Send Message

```http
POST /api/chat/sessions/{session_id}/messages
```

**Request Body:**

```json
{
  "content": "Show me pending enquiries for dealer DL123456",
  "context": {
    "include_history": true
  }
}
```

**Response:**

```json
{
  "message_id": "msg-xyz789",
  "content": "Here are the pending enquiries for dealer DL123456...",
  "tool_calls": [
    {
      "tool_name": "get_dealer_enquiries",
      "parameters": {"dealer_id": "DL123456", "status": "pending"},
      "result": {...}
    }
  ],
  "metadata": {
    "tokens_used": 150,
    "processing_time_ms": 2500
  }
}
```

---

## 7. Error Codes

### 7.1 HTTP/REST Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_FAILED` | 400 | Request validation failed |
| `INVALID_PARAMETER` | 400 | Invalid parameter value |
| `INJECTION_DETECTED` | 400 | Potential injection attack detected |
| `UNAUTHORIZED` | 401 | Authentication required |
| `TOKEN_EXPIRED` | 401 | JWT token has expired |
| `FORBIDDEN` | 403 | Access denied by policy |
| `ELEVATION_REQUIRED` | 403 | PIM elevation required |
| `USER_CONFIRMATION_REQUIRED` | 403 | Write tool requires user_confirmed=true |
| `TOOL_NOT_FOUND` | 404 | Tool does not exist |
| `USER_NOT_FOUND` | 404 | User does not exist |
| `RATE_LIMITED` | 429 | Rate limit exceeded |
| `IDEMPOTENCY_CONFLICT` | 409 | Duplicate idempotency key with different request |
| `TOOL_EXECUTION_FAILED` | 500 | Backend execution error |
| `CIRCUIT_BREAKER_OPEN` | 503 | Backend service unavailable |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### 7.2 MCP JSON-RPC Error Codes

Per MCP specification, errors follow JSON-RPC 2.0 format:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": {"details": "Missing required field: method"}
  }
}
```

| Code | Name | Description |
|------|------|-------------|
| `-32700` | Parse error | Invalid JSON received |
| `-32600` | Invalid Request | Request object is invalid |
| `-32601` | Method not found | Tool/method does not exist |
| `-32602` | Invalid params | Invalid method parameters |
| `-32603` | Internal error | Internal JSON-RPC error |
| `-32000` | Server error | Generic server error |
| `-32001` | Rate limited | Request rate limit exceeded |
| `-32002` | Confirmation required | Write tool requires user_confirmed |
| `-32003` | Backend unavailable | Downstream service unavailable |

---

## 8. Rate Limits

| Tier | Limit | Window |
|------|-------|--------|
| **Permissive** | 200 req/min | 1 minute |
| **Standard** | 100 req/min | 1 minute |
| **Strict** | 20 req/min | 1 minute |

Rate limit headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1706698260
```

---

## 9. Webhooks (Future)

### 9.1 Event Types

| Event | Description |
|-------|-------------|
| `tool.executed` | Tool execution completed |
| `tool.failed` | Tool execution failed |
| `user.login` | User logged in |
| `security.alert` | Security event detected |

### 9.2 Webhook Payload

```json
{
  "event_type": "tool.executed",
  "timestamp": "2026-01-31T10:30:00Z",
  "data": {
    "tool_name": "get_dealer_enquiries",
    "user_id": "user@msil.com",
    "correlation_id": "a1b2c3d4-e5f6",
    "status": "success"
  }
}
```

---

*Document Classification: Internal | Last Review: January 31, 2026*
