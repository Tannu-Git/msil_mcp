# MSIL MCP Server - Protocol, Configuration & Authentication Guide

## Quick Summary

| Aspect | Details |
|--------|---------|
| **Protocol** | **JSON-RPC 2.0 over HTTP/HTTPS** (Model Context Protocol) |
| **Endpoint** | `POST /mcp` |
| **Transport** | HTTP/HTTPS |
| **Format** | JSON |
| **Authentication** | API Key in header (`X-API-Key`) |
| **Base URL** | `http://localhost:8000` (dev) / `https://mcp.msil-apim.example.com` (prod) |

---

## 1. MCP Protocol Overview

### 1.1 What is MCP?

**Model Context Protocol (MCP)** is a standardized protocol for AI/LLM applications to discover and invoke tools dynamically at runtime.

**Key Benefits:**
- ✅ **Standard protocol** - Works with any LLM client (Claude, GPT-4, etc.)
- ✅ **Dynamic tool discovery** - Clients learn about available tools at runtime
- ✅ **Type-safe execution** - JSON Schema for input validation
- ✅ **Bidirectional communication** - Server-Sent Events (SSE) for streaming

**MSIL Implementation:**
- Uses **JSON-RPC 2.0** over **HTTP** (not stdio or WebSocket)
- Composite MCP server exposing 6+ service booking tools
- Routes all tool calls through a single gateway endpoint

---

## 2. Protocol Communication

### 2.1 Request/Response Model

```
MCP Client
    ↓
(HTTP POST /mcp)
    ↓
MSIL MCP Server
    ↓
Tool Registry → Tool Executor → Mock/APIM APIs
```

### 2.2 Message Format: JSON-RPC 2.0

**All communication uses JSON-RPC 2.0 specification:**

```
{
  "jsonrpc": "2.0",      // Required: Always "2.0"
  "id": "unique-id",     // Required: Request identifier (can be string or number)
  "method": "METHOD",    // Required: RPC method name
  "params": {}           // Optional: Method parameters as object
}
```

### 2.3 Response Format

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "id": "unique-id",
  "result": {}  // Contains the response data
}
```

**Error Response:**
```json
{
  "jsonrpc": "2.0",
  "id": "unique-id",
  "error": {
    "code": -32000,           // Error code (see table below)
    "message": "Error text"   // Error description
  }
}
```

### 2.4 Error Codes

| Code | Meaning | Example |
|------|---------|---------|
| `-32601` | Method not found | Unknown MCP method requested |
| `-32001` | Unauthorized | Missing or invalid API key |
| `-32000` | Server error | Tool execution failed |
| `-32600` | Invalid request | Malformed JSON-RPC |

---

## 3. Supported MCP Methods

### 3.1 Method: `initialize`

**Purpose**: Handshake with server and get capabilities

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "initialize",
  "params": {}
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "protocolVersion": "2024-11-05",
    "serverInfo": {
      "name": "MSIL MCP Server",
      "version": "1.0.0"
    },
    "capabilities": {
      "tools": {}
    }
  }
}
```

---

### 3.2 Method: `tools/list`

**Purpose**: Discover all available tools

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "method": "tools/list",
  "params": {}
}
```

**Response** (example with 2 tools):
```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "result": {
    "tools": [
      {
        "name": "resolve_customer",
        "description": "Resolve customer details from mobile number",
        "inputSchema": {
          "type": "object",
          "required": ["mobile"],
          "properties": {
            "mobile": {
              "type": "string",
              "description": "Customer mobile number (10 digits)"
            }
          }
        }
      },
      {
        "name": "resolve_vehicle",
        "description": "Resolve vehicle details from registration number",
        "inputSchema": {
          "type": "object",
          "required": ["registration_number"],
          "properties": {
            "registration_number": {
              "type": "string",
              "description": "Vehicle registration number"
            }
          }
        }
      }
    ]
  }
}
```

**Available Tools** (Service Booking Bundle):
1. `resolve_customer` - Get customer details
2. `resolve_vehicle` - Get vehicle details
3. `get_nearby_dealers` - Find nearby dealers
4. `create_service_booking` - Create service booking
5. `check_booking_status` - Check booking status
6. `cancel_booking` - Cancel a booking

---

### 3.3 Method: `tools/call`

**Purpose**: Execute a specific tool

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": "3",
  "method": "tools/call",
  "params": {
    "name": "resolve_customer",
    "arguments": {
      "mobile": "9876543210"
    }
  }
}
```

**Response** (Success):
```json
{
  "jsonrpc": "2.0",
  "id": "3",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Customer found: John Doe (ID: CUST123)"
      }
    ],
    "isError": false
  }
}
```

**Response** (Error):
```json
{
  "jsonrpc": "2.0",
  "id": "3",
  "error": {
    "code": -32000,
    "message": "Tool execution failed: Invalid mobile number"
  }
}
```

---

## 4. Client Configuration & Integration

### 4.1 HTTP Headers Required

Every MCP request must include these headers:

```
POST /mcp HTTP/1.1
Host: localhost:8000
Content-Type: application/json
X-API-Key: msil-mcp-dev-key-2026
X-Correlation-ID: unique-request-id-optional
Content-Length: {payload-length}
```

**Header Details:**
- **`Content-Type`**: Always `application/json`
- **`X-API-Key`**: API authentication key (see Section 5)
- **`X-Correlation-ID`**: Optional UUID for request tracing

---

### 4.2 TypeScript/JavaScript Client Example

```typescript
// MCP Client Implementation
class MCPClient {
  private endpoint: string;
  private apiKey: string;

  constructor(endpoint: string = 'http://localhost:8000', apiKey: string) {
    this.endpoint = endpoint;
    this.apiKey = apiKey;
  }

  private async sendRequest(method: string, params?: any) {
    const request = {
      jsonrpc: '2.0',
      id: crypto.randomUUID(),
      method,
      params: params || {}
    };

    const response = await fetch(`${this.endpoint}/mcp`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey,
        'X-Correlation-ID': crypto.randomUUID()
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  // Initialize connection
  async initialize() {
    return this.sendRequest('initialize');
  }

  // List all tools
  async listTools() {
    const response = await this.sendRequest('tools/list');
    return response.result.tools;
  }

  // Execute a tool
  async callTool(toolName: string, arguments: Record<string, any>) {
    return this.sendRequest('tools/call', {
      name: toolName,
      arguments
    });
  }
}

// Usage
const client = new MCPClient('http://localhost:8000', 'msil-mcp-dev-key-2026');

// Get available tools
const tools = await client.listTools();
console.log('Available tools:', tools);

// Execute a tool
const result = await client.callTool('resolve_customer', {
  mobile: '9876543210'
});
console.log('Result:', result);
```

---

### 4.3 Python Client Example

```python
import requests
import json
from typing import Any, Dict, Optional
import uuid

class MCPClient:
    def __init__(self, endpoint: str = 'http://localhost:8000', api_key: str = None):
        self.endpoint = endpoint
        self.api_key = api_key or 'msil-mcp-dev-key-2026'
        self.session = requests.Session()

    def send_request(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Send MCP JSON-RPC request"""
        request = {
            'jsonrpc': '2.0',
            'id': str(uuid.uuid4()),
            'method': method,
            'params': params or {}
        }

        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key,
            'X-Correlation-ID': str(uuid.uuid4())
        }

        response = self.session.post(
            f'{self.endpoint}/mcp',
            json=request,
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    def initialize(self) -> Dict[str, Any]:
        """Initialize MCP connection"""
        return self.send_request('initialize')

    def list_tools(self) -> list:
        """List available tools"""
        response = self.send_request('tools/list')
        return response['result']['tools']

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool"""
        return self.send_request('tools/call', {
            'name': tool_name,
            'arguments': arguments
        })

# Usage Example
if __name__ == '__main__':
    client = MCPClient('http://localhost:8000')
    
    # List tools
    tools = client.list_tools()
    print(f'Available tools: {len(tools)}')
    for tool in tools:
        print(f'  - {tool["name"]}: {tool["description"]}')
    
    # Call a tool
    result = client.call_tool('resolve_customer', {'mobile': '9876543210'})
    print(f'Tool result: {result}')
```

---

### 4.4 cURL Examples

**List Tools:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-Key: msil-mcp-dev-key-2026" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "tools/list",
    "params": {}
  }'
```

**Call a Tool:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-Key: msil-mcp-dev-key-2026" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "tools/call",
    "params": {
      "name": "resolve_customer",
      "arguments": {
        "mobile": "9876543210"
      }
    }
  }'
```

---

## 5. Authentication

### 5.1 API Key Authentication (Current MVP)

**Mechanism**: Header-based API Key

```http
X-API-Key: msil-mcp-dev-key-2026
```

**Implementation**:
- Every request must include the API key header
- Server validates API key against `API_KEY` setting in `.env`
- Invalid/missing key returns error code `-32001`

**Current Key** (Development):
```
msil-mcp-dev-key-2026
```

**Configuration** (in `mcp-server/.env`):
```env
API_KEY=msil-mcp-dev-key-2026
```

**Validation Logic** (in `mcp.py`):
```python
if settings.API_KEY and x_api_key != settings.API_KEY:
    if not settings.DEBUG:
        return MCPResponse(
            jsonrpc="2.0",
            id=request.id,
            error={
                "code": -32001,
                "message": "Unauthorized: Invalid API Key"
            }
        )
```

---

### 5.2 Production Authentication (Planned - Phase 6+)

For production deployment, upgrade to OAuth2/OIDC:

```http
Authorization: Bearer <jwt-token>
```

**JWT Token Structure**:
```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "key-id-123"
  },
  "payload": {
    "sub": "user-id-456",
    "iss": "https://auth.msil-mcp.example.com",
    "aud": "msil-mcp-api",
    "exp": 1738335600,
    "iat": 1738332000,
    "email": "user@example.com",
    "roles": ["user", "developer"],
    "permissions": [
      "tools:execute",
      "tools:read",
      "conversations:create"
    ]
  }
}
```

---

## 6. Client Import/Configuration JSON

### 6.1 Claude (Anthropic) Configuration

**File**: `claude_config.json`

For Claude API clients to import MSIL MCP server:

```json
{
  "name": "MSIL MCP Server",
  "type": "mcp-server",
  "protocol": "json-rpc-2.0",
  "transport": "http",
  "configuration": {
    "endpoint": "http://localhost:8000/mcp",
    "authentication": {
      "type": "api_key",
      "header": "X-API-Key",
      "value": "msil-mcp-dev-key-2026"
    },
    "timeout": 30000,
    "retries": 3
  },
  "tools": {
    "auto_discover": true,
    "cache_enabled": true,
    "cache_ttl": 3600
  },
  "metadata": {
    "version": "1.0.0",
    "description": "Service booking tools for Maruti Suzuki India Limited",
    "provider": "Nagarro",
    "supported_llms": ["claude-3-sonnet", "claude-3-opus", "gpt-4", "gpt-4-turbo"]
  }
}
```

---

### 6.2 Generic MCP Client Configuration

**File**: `mcp_client_config.json`

```json
{
  "servers": [
    {
      "name": "msil-mcp-server",
      "type": "http",
      "endpoint": "http://localhost:8000",
      "auth": {
        "type": "api_key",
        "key": "msil-mcp-dev-key-2026"
      },
      "features": {
        "tools": true,
        "resources": false,
        "prompts": false
      },
      "transport": {
        "protocol": "json-rpc-2.0",
        "timeout_ms": 30000,
        "max_retries": 3,
        "backoff_strategy": "exponential"
      },
      "tool_discovery": {
        "auto_refresh": true,
        "refresh_interval_ms": 3600000
      }
    }
  ]
}
```

---

### 6.3 Environment Configuration

**File**: `.env.client` (Client-side configuration)

```env
# MSIL MCP Server Configuration
MCP_SERVER_URL=http://localhost:8000
MCP_API_KEY=msil-mcp-dev-key-2026
MCP_TIMEOUT_MS=30000
MCP_MAX_RETRIES=3

# Enable debug logging
DEBUG=true
LOG_LEVEL=debug

# Tool caching
CACHE_TOOLS=true
CACHE_TTL_SECONDS=3600

# Correlation tracking
ENABLE_TRACING=true
```

---

## 7. End-to-End Example: Service Booking Flow

### 7.1 Complete Flow Example

```typescript
// 1. Initialize client
const client = new MCPClient('http://localhost:8000', 'msil-mcp-dev-key-2026');

// 2. Get server info
const init = await client.initialize();
console.log(`Connected to: ${init.result.serverInfo.name} v${init.result.serverInfo.version}`);

// 3. Discover tools
const tools = await client.listTools();
console.log(`Found ${tools.length} tools`);
tools.forEach(t => console.log(`  - ${t.name}`));

// 4. Execute tool chain
const customerResult = await client.callTool('resolve_customer', {
  mobile: '9876543210'
});
const customerId = extractCustomerId(customerResult);

const vehicleResult = await client.callTool('resolve_vehicle', {
  registration_number: 'DL01AB1234'
});
const vehicleId = extractVehicleId(vehicleResult);

const dealersResult = await client.callTool('get_nearby_dealers', {
  latitude: 28.7041,
  longitude: 77.1025,
  radius_km: 10
});
const dealerId = selectDealer(dealersResult);

// 5. Create booking
const bookingResult = await client.callTool('create_service_booking', {
  customer_id: customerId,
  vehicle_id: vehicleId,
  dealer_id: dealerId,
  service_type: 'regular_maintenance',
  preferred_date: '2026-02-15',
  preferred_time: '10:00',
  comments: 'Check engine oil and coolant'
});

console.log('Booking created:', bookingResult.result);
```

---

## 8. Debugging & Monitoring

### 8.1 Available Endpoints for Testing

```bash
# Health check
curl http://localhost:8000/health

# Server info
curl http://localhost:8000/

# OpenAPI documentation
http://localhost:8000/docs

# Metrics
curl http://localhost:8000/api/analytics/metrics/summary

# Tools REST endpoint (alternative to MCP JSON-RPC)
curl http://localhost:8000/mcp/tools
```

---

### 8.2 Request Tracing

Use correlation IDs to track requests:

```http
X-Correlation-ID: 123e4567-e89b-12d3-a456-426614174000
```

Server will include this in:
- Response headers
- Server logs
- Audit trail

---

### 8.3 Error Handling

**Always check for error responses:**

```typescript
const response = await client.callTool('resolve_customer', { mobile: '...' });

if (response.error) {
  console.error(`Error [${response.error.code}]: ${response.error.message}`);
  // Handle error
} else {
  console.log('Success:', response.result);
}
```

---

## 9. Performance & Rate Limiting

### 9.1 Current Settings (MVP)

- **Request timeout**: 30 seconds
- **Max retries**: 3 (with exponential backoff)
- **Tool discovery cache**: 1 hour
- **Rate limit**: No limit (dev mode)

### 9.2 Production Settings (Planned)

- **Request timeout**: 30 seconds
- **Max retries**: 3
- **Rate limit**: 100 requests/minute per API key
- **Burst limit**: 500 requests/minute

---

## 10. Migration Paths

### 10.1 From Chat UI to MCP Client

**Current** (Chat UI approach):
```bash
POST /api/chat/send
```

**New** (Direct MCP):
```bash
POST /mcp
```

Both work simultaneously. Chat UI is abstraction over MCP.

### 10.2 From REST to MCP

**Current** (REST endpoint):
```bash
POST /mcp/tools/{tool_name}/call
```

**MCP Protocol** (Recommended):
```bash
POST /mcp
method: tools/call
params: { name: tool_name, arguments: {...} }
```

---

## 11. Quick Reference

### Available MCP Methods

```
initialize      → Get server capabilities
tools/list      → Discover available tools
tools/call      → Execute a tool
```

### Available Tools

| Tool | Purpose | Required Input |
|------|---------|-----------------|
| `resolve_customer` | Get customer details | mobile (10 digits) |
| `resolve_vehicle` | Get vehicle details | registration_number |
| `get_nearby_dealers` | Find dealers | latitude, longitude |
| `create_service_booking` | Create booking | customer_id, vehicle_id, dealer_id, service_type, date, time |
| `check_booking_status` | Check booking | booking_id |
| `cancel_booking` | Cancel booking | booking_id |

### Authentication

```
Header: X-API-Key: msil-mcp-dev-key-2026
```

### Endpoint

```
http://localhost:8000/mcp  (dev)
https://mcp.msil-apim.example.com/mcp  (prod)
```

---

## 12. Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Invalid API Key" | Missing/wrong X-API-Key header | Check `.env` API_KEY value |
| "Method not found" | Typo in method name | Use exact names: `tools/list`, `tools/call` |
| "Tool execution failed" | Invalid tool arguments | Check inputSchema for required fields |
| Connection timeout | Server not running | Start server: `uvicorn app.main:app --port 8000` |
| CORS error | Client on different origin | Check CORS_ORIGINS in `.env` |

---

## 13. Glossary

| Term | Definition |
|------|-----------|
| **MCP** | Model Context Protocol - Standard for LLM tool integration |
| **JSON-RPC** | Remote Procedure Call using JSON format |
| **Tool** | A callable service/function exposed by MCP server |
| **Tool Registry** | In-memory store of all available tools |
| **Correlation ID** | UUID for tracking request across system |
| **API Key** | Authentication credential (temporary for MVP) |

---

## 14. Resources

- **MCP Specification**: https://modelcontextprotocol.io
- **JSON-RPC 2.0 Spec**: https://www.jsonrpc.org/specification
- **Server OpenAPI Docs**: http://localhost:8000/docs
- **Source Code**: `mcp-server/app/api/mcp.py`

---

**Document Version**: 1.0  
**Last Updated**: January 31, 2026  
**Status**: Production Ready (MVP)
