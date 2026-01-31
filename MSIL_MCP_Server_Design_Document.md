# MSIL Composite MCP Server - Technical Design Document

**Document Version:** 1.0  
**Date:** January 30, 2026  
**Prepared By:** Nagarro Development Team  
**Client:** Maruti Suzuki India Limited (MSIL)  
**Project:** Composite MCP Server Platform  

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Architecture](#2-system-architecture)
3. [Component Design](#3-component-design)
4. [Data Models](#4-data-models)
5. [API Design](#5-api-design)
6. [Sequence Diagrams](#6-sequence-diagrams)
7. [Security Design](#7-security-design)
8. [Frontend Architecture](#8-frontend-architecture)
9. [Infrastructure Design](#9-infrastructure-design)
10. [Database Schema](#10-database-schema)
11. [Configuration Management](#11-configuration-management)
12. [Error Handling](#12-error-handling)
13. [Testing Strategy](#13-testing-strategy)

---

## 1. Introduction

### 1.1 Purpose

This document provides the detailed technical design for the MSIL Composite MCP Server platform. It covers architecture decisions, component designs, data models, API specifications, and infrastructure configurations.

### 1.2 Scope

| Aspect | Coverage |
|--------|----------|
| MCP Server Core | Complete design |
| Chat Interface | UI/UX and component architecture |
| Admin Interface | Dashboard and management features |
| Mock API Framework | Service booking simulation |
| AWS Infrastructure | Terraform-based IaC |

### 1.3 Design Principles

1. **Modularity**: Loosely coupled components with clear interfaces
2. **Scalability**: Horizontal scaling capability from day one
3. **Security-First**: Defense in depth at every layer
4. **Observability**: Comprehensive logging, metrics, and tracing
5. **Configuration-Driven**: Behavior controlled via configuration, not code
6. **OpenAPI-First**: All tools derived from OpenAPI specifications

---

## 2. System Architecture

### 2.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              MSIL MCP PLATFORM                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                           CLIENTS                                            │   │
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────┐   │   │
│  │  │    Chat UI        │  │    Admin UI       │  │   External MCP        │   │   │
│  │  │    (React)        │  │    (React)        │  │   Clients             │   │   │
│  │  │    Port: 3000     │  │    Port: 3001     │  │                       │   │   │
│  │  └─────────┬─────────┘  └─────────┬─────────┘  └───────────┬───────────┘   │   │
│  └────────────┼─────────────────────┼─────────────────────────┼────────────────┘   │
│               │                     │                         │                     │
│               └─────────────────────┼─────────────────────────┘                     │
│                                     ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                        MCP SERVER (FastAPI)                                  │   │
│  │                           Port: 8000                                         │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │   │
│  │  │                      API GATEWAY LAYER                               │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │   │
│  │  │  │   Auth      │  │   Rate      │  │   Request   │  │  Routing   │ │   │   │
│  │  │  │  Middleware │  │   Limiter   │  │  Validator  │  │  Engine    │ │   │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │   │
│  │  └─────────────────────────────────────────────────────────────────────┘   │   │
│  │                                     │                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │   │
│  │  │                      CORE SERVICES                                   │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │   │
│  │  │  │    MCP      │  │    Tool     │  │   Policy    │  │  OpenAPI   │ │   │   │
│  │  │  │  Protocol   │  │  Registry   │  │   Engine    │  │  Parser    │ │   │   │
│  │  │  │  Handler    │  │  Service    │  │   (OPA)     │  │  Service   │ │   │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │   │
│  │  │  │    Tool     │  │   Schema    │  │   Cache     │  │  Audit     │ │   │   │
│  │  │  │  Executor   │  │  Validator  │  │   Service   │  │  Service   │ │   │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │   │
│  │  └─────────────────────────────────────────────────────────────────────┘   │   │
│  │                                     │                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────────────┐   │   │
│  │  │                      INTEGRATION LAYER                               │   │   │
│  │  │  ┌─────────────────────────┐  ┌─────────────────────────────────┐  │   │   │
│  │  │  │    API Gateway          │  │       LLM Connector             │  │   │   │
│  │  │  │    Connector            │  │                                 │  │   │   │
│  │  │  │  ┌─────────────────┐   │  │  ┌───────────┐  ┌───────────┐  │  │   │   │
│  │  │  │  │  Mock Adapter   │   │  │  │  OpenAI   │  │  Bedrock  │  │  │   │   │
│  │  │  │  │  MSIL Adapter   │   │  │  │  Adapter  │  │  Adapter  │  │  │   │   │
│  │  │  │  └─────────────────┘   │  │  └───────────┘  └───────────┘  │  │   │   │
│  │  │  └─────────────────────────┘  └─────────────────────────────────┘  │   │   │
│  │  └─────────────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                               │
│               ┌─────────────────────┼─────────────────────┐                        │
│               ▼                     ▼                     ▼                        │
│  ┌─────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐            │
│  │   PostgreSQL    │  │       Redis         │  │    Mock API         │            │
│  │   Port: 5432    │  │    Port: 6379       │  │    Port: 8080       │            │
│  └─────────────────┘  └─────────────────────┘  └─────────────────────┘            │
│                                                           │                        │
│                                                           ▼                        │
│                                               ┌─────────────────────┐              │
│                                               │   MSIL Dev APIM     │              │
│                                               │   (Production)      │              │
│                                               └─────────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Interactions

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        REQUEST FLOW                                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  User Request                                                                 │
│       │                                                                       │
│       ▼                                                                       │
│  ┌─────────────┐                                                             │
│  │  Chat UI    │                                                             │
│  └──────┬──────┘                                                             │
│         │ 1. User message                                                    │
│         ▼                                                                    │
│  ┌─────────────┐     2. Get available tools                                  │
│  │  LLM        │◄────────────────────────────┐                              │
│  │  (GPT-4)    │                             │                              │
│  └──────┬──────┘                             │                              │
│         │ 3. Determine tool calls            │                              │
│         ▼                                    │                              │
│  ┌─────────────┐     4. tools/list           │                              │
│  │  MCP Client │────────────────────────►┌───┴───────┐                      │
│  │  (in Chat)  │                         │           │                      │
│  └──────┬──────┘                         │    MCP    │                      │
│         │ 5. tools/call                  │   Server  │                      │
│         ▼                                │           │                      │
│  ┌─────────────┐     6. Validate &       │           │                      │
│  │  MCP Server │◄────Execute─────────────┤           │                      │
│  └──────┬──────┘                         └───────────┘                      │
│         │ 7. Call API                                                        │
│         ▼                                                                    │
│  ┌─────────────┐                                                             │
│  │  Mock/MSIL  │                                                             │
│  │  API        │                                                             │
│  └──────┬──────┘                                                             │
│         │ 8. Response                                                        │
│         ▼                                                                    │
│  ┌─────────────┐                                                             │
│  │  User sees  │                                                             │
│  │  result     │                                                             │
│  └─────────────┘                                                             │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Technology Stack Summary

| Layer | Technology | Version |
|-------|------------|---------|
| **Frontend** | React + TypeScript | 18.x |
| **UI Components** | Shadcn/UI + Tailwind CSS | Latest |
| **State Management** | Zustand + React Query | Latest |
| **Backend Framework** | FastAPI | 0.109+ |
| **Python Version** | Python | 3.11+ |
| **Database** | PostgreSQL | 15 |
| **Cache** | Redis | 7 |
| **Policy Engine** | Open Policy Agent | 0.60+ |
| **Container Runtime** | Docker | 24+ |
| **IaC** | Terraform | 1.7+ |

---

## 3. Component Design

### 3.1 MCP Protocol Handler

**Purpose**: Implement the Model Context Protocol specification for tool discovery and execution.

**Module**: `app/core/mcp/protocol.py`

```python
# MCP Protocol Handler Design

from enum import Enum
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class MCPMethod(Enum):
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"

class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int
    method: MCPMethod
    params: Optional[Dict[str, Any]] = None

class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int
    result: Optional[Any] = None
    error: Optional[MCPError] = None

class MCPError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None

class MCPTool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]  # JSON Schema

class MCPToolResult(BaseModel):
    content: List[MCPContent]
    isError: bool = False

class MCPContent(BaseModel):
    type: str  # "text", "image", "resource"
    text: Optional[str] = None
    data: Optional[str] = None  # base64 for images
    mimeType: Optional[str] = None
```

**Class Diagram**:
```
┌─────────────────────────────────────────────────────────────────┐
│                     MCPProtocolHandler                           │
├─────────────────────────────────────────────────────────────────┤
│ - tool_registry: ToolRegistryService                            │
│ - policy_engine: PolicyEngine                                   │
│ - executor: ToolExecutor                                        │
│ - validator: SchemaValidator                                    │
├─────────────────────────────────────────────────────────────────┤
│ + handle_request(request: MCPRequest) -> MCPResponse            │
│ + handle_tools_list(params: dict) -> List[MCPTool]             │
│ + handle_tools_call(params: dict) -> MCPToolResult             │
│ - validate_request(request: MCPRequest) -> bool                 │
│ - check_authorization(tool: str, user: User) -> bool           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ uses
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ToolRegistryService                          │
├─────────────────────────────────────────────────────────────────┤
│ - db: Database                                                  │
│ - cache: Redis                                                  │
├─────────────────────────────────────────────────────────────────┤
│ + get_all_tools() -> List[Tool]                                 │
│ + get_tool(name: str) -> Tool                                   │
│ + register_tool(tool: Tool) -> Tool                             │
│ + update_tool(name: str, tool: Tool) -> Tool                    │
│ + delete_tool(name: str) -> bool                                │
│ + get_tools_by_bundle(bundle: str) -> List[Tool]               │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 OpenAPI Tool Generator

**Purpose**: Parse OpenAPI specifications and generate MCP-compatible tool definitions.

**Module**: `app/core/generator/openapi_parser.py`

```python
# OpenAPI Tool Generator Design

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import yaml
import json

@dataclass
class GeneratedTool:
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    http_method: str
    path: str
    operation_id: str
    tags: List[str]
    security: List[Dict[str, Any]]

class OpenAPIToolGenerator:
    """
    Converts OpenAPI operations into MCP tool definitions.
    
    Design Principles:
    1. One OpenAPI operation = One MCP tool
    2. Tool name derived from operationId or path
    3. Input schema built from parameters + requestBody
    4. Output schema from responses.200
    """
    
    def __init__(self, spec_path: str):
        self.spec = self._load_spec(spec_path)
        self.tools: List[GeneratedTool] = []
    
    def generate_tools(self) -> List[GeneratedTool]:
        """Generate MCP tools from all operations."""
        for path, path_item in self.spec.get("paths", {}).items():
            for method in ["get", "post", "put", "delete", "patch"]:
                if method in path_item:
                    operation = path_item[method]
                    tool = self._operation_to_tool(path, method, operation)
                    self.tools.append(tool)
        return self.tools
    
    def _operation_to_tool(
        self, 
        path: str, 
        method: str, 
        operation: Dict
    ) -> GeneratedTool:
        """Convert single operation to MCP tool."""
        # Build input schema from parameters and requestBody
        input_schema = self._build_input_schema(operation)
        
        # Build output schema from responses
        output_schema = self._build_output_schema(operation)
        
        return GeneratedTool(
            name=self._generate_tool_name(operation, path, method),
            description=operation.get("summary", "") or operation.get("description", ""),
            input_schema=input_schema,
            output_schema=output_schema,
            http_method=method.upper(),
            path=path,
            operation_id=operation.get("operationId", ""),
            tags=operation.get("tags", []),
            security=operation.get("security", [])
        )
    
    def _build_input_schema(self, operation: Dict) -> Dict[str, Any]:
        """Build JSON Schema from parameters and requestBody."""
        properties = {}
        required = []
        
        # Process path/query/header parameters
        for param in operation.get("parameters", []):
            prop_name = param["name"]
            properties[prop_name] = self._param_to_schema(param)
            if param.get("required", False):
                required.append(prop_name)
        
        # Process requestBody
        if "requestBody" in operation:
            body_schema = self._extract_body_schema(operation["requestBody"])
            if body_schema:
                properties.update(body_schema.get("properties", {}))
                required.extend(body_schema.get("required", []))
        
        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False
        }
```

**Tool Generation Flow**:
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  OpenAPI Spec   │────▶│  Parser         │────▶│  Tool Def       │
│  (YAML/JSON)    │     │                 │     │  (JSON Schema)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ paths:          │     │ For each        │     │ {               │
│   /booking:     │     │ operation:      │     │   "name": "...",│
│     post:       │────▶│ - Extract params│────▶│   "inputSchema":│
│       summary:  │     │ - Build schema  │     │   {...}         │
│       params:   │     │ - Generate name │     │ }               │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 3.3 Tool Executor

**Purpose**: Execute tool calls by invoking the appropriate API endpoints.

**Module**: `app/core/executor/tool_executor.py`

```python
# Tool Executor Design

from abc import ABC, abstractmethod
from typing import Any, Dict
import httpx
from circuitbreaker import circuit

class APIAdapter(ABC):
    """Abstract base for API adapters."""
    
    @abstractmethod
    async def execute(
        self, 
        method: str, 
        path: str, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        pass

class MockAPIAdapter(APIAdapter):
    """Adapter for local mock API."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def execute(
        self, 
        method: str, 
        path: str, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        response = await self.client.request(
            method=method,
            url=url,
            json=params if method in ["POST", "PUT", "PATCH"] else None,
            params=params if method == "GET" else None
        )
        response.raise_for_status()
        return response.json()

class MSILAPIAdapter(APIAdapter):
    """Adapter for MSIL Dev APIM."""
    
    def __init__(self, config: MSILAPIConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0)
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
    
    async def _get_token(self) -> str:
        """Get OAuth2 token, refreshing if needed."""
        if self._token and self._token_expiry > datetime.utcnow():
            return self._token
        
        response = await self.client.post(
            self.config.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "scope": self.config.scope
            }
        )
        data = response.json()
        self._token = data["access_token"]
        self._token_expiry = datetime.utcnow() + timedelta(seconds=data["expires_in"] - 60)
        return self._token
    
    @circuit(failure_threshold=5, recovery_timeout=60)
    async def execute(
        self, 
        method: str, 
        path: str, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        token = await self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "x-api-key": self.config.api_key,
            "x-correlation-id": str(uuid.uuid4())
        }
        
        url = f"{self.config.base_url}{path}"
        response = await self.client.request(
            method=method,
            url=url,
            headers=headers,
            json=params if method in ["POST", "PUT", "PATCH"] else None,
            params=params if method == "GET" else None
        )
        response.raise_for_status()
        return response.json()

class ToolExecutor:
    """Main executor that routes to appropriate adapter."""
    
    def __init__(self, adapter: APIAdapter):
        self.adapter = adapter
        self.validator = SchemaValidator()
        self.audit = AuditService()
    
    async def execute(
        self, 
        tool: Tool, 
        params: Dict[str, Any],
        context: ExecutionContext
    ) -> ToolResult:
        # 1. Validate input
        self.validator.validate(params, tool.input_schema)
        
        # 2. Log start
        await self.audit.log_tool_start(tool, params, context)
        
        try:
            # 3. Execute
            start_time = time.time()
            result = await self.adapter.execute(
                tool.http_method, 
                tool.path, 
                params
            )
            latency = time.time() - start_time
            
            # 4. Validate output
            self.validator.validate(result, tool.output_schema)
            
            # 5. Log success
            await self.audit.log_tool_success(tool, result, latency, context)
            
            return ToolResult(success=True, data=result, latency=latency)
            
        except Exception as e:
            # 6. Log failure
            await self.audit.log_tool_failure(tool, e, context)
            raise
```

### 3.4 Policy Engine

**Purpose**: Enforce access control, rate limiting, and security policies.

**Module**: `app/core/policy/engine.py`

```python
# Policy Engine Design using OPA

from dataclasses import dataclass
from typing import List, Dict, Any
import httpx

@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    policies_evaluated: List[str]

class PolicyEngine:
    """
    Policy enforcement using Open Policy Agent.
    
    Policies:
    1. RBAC - Role-based tool access
    2. Rate Limiting - Per user/tool limits
    3. Input Validation - Additional constraints
    4. Allow/Deny Lists - Tool-specific rules
    """
    
    def __init__(self, opa_url: str = "http://localhost:8181"):
        self.opa_url = opa_url
        self.client = httpx.AsyncClient()
    
    async def evaluate(
        self, 
        action: str,
        resource: str,
        context: Dict[str, Any]
    ) -> PolicyDecision:
        """
        Evaluate policy for an action on a resource.
        
        Args:
            action: "discover" | "invoke" | "admin"
            resource: Tool name or resource identifier
            context: User info, request metadata
        """
        input_data = {
            "input": {
                "action": action,
                "resource": resource,
                "user": context.get("user"),
                "roles": context.get("roles", []),
                "ip_address": context.get("ip_address"),
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
            reason=result.get("reason", ""),
            policies_evaluated=result.get("policies", [])
        )
```

**OPA Policy Example** (`policies/authz.rego`):
```rego
package msil.authz

default allow = false

# Admin can do everything
allow {
    input.roles[_] == "admin"
}

# Users can invoke tools they have access to
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

### 3.5 Cache Service

**Purpose**: Cache API responses and manage rate limiting.

**Module**: `app/core/cache/service.py`

```python
# Cache Service Design

from typing import Any, Optional
import redis.asyncio as redis
import json
from datetime import timedelta

class CacheService:
    """
    Redis-based caching for:
    1. Tool definitions (avoid DB queries)
    2. API responses (idempotent reads)
    3. Rate limit counters
    4. Session data
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
    
    # Tool Cache
    async def get_tool(self, name: str) -> Optional[dict]:
        data = await self.redis.get(f"tool:{name}")
        return json.loads(data) if data else None
    
    async def set_tool(self, name: str, tool: dict, ttl: int = 3600):
        await self.redis.set(
            f"tool:{name}", 
            json.dumps(tool), 
            ex=ttl
        )
    
    async def invalidate_tool(self, name: str):
        await self.redis.delete(f"tool:{name}")
    
    # API Response Cache
    async def get_response(self, cache_key: str) -> Optional[dict]:
        data = await self.redis.get(f"response:{cache_key}")
        return json.loads(data) if data else None
    
    async def set_response(
        self, 
        cache_key: str, 
        response: dict, 
        ttl: int = 300
    ):
        await self.redis.set(
            f"response:{cache_key}", 
            json.dumps(response), 
            ex=ttl
        )
    
    # Rate Limiting
    async def check_rate_limit(
        self, 
        key: str, 
        limit: int, 
        window: int = 60
    ) -> tuple[bool, int]:
        """
        Check and increment rate limit counter.
        Returns (is_allowed, current_count).
        """
        pipe = self.redis.pipeline()
        pipe.incr(f"ratelimit:{key}")
        pipe.expire(f"ratelimit:{key}", window)
        results = await pipe.execute()
        
        current = results[0]
        return current <= limit, current
```

### 3.6 Audit Service

**Purpose**: Log all actions for compliance and debugging.

**Module**: `app/core/audit/service.py`

```python
# Audit Service Design

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, Optional
import json

@dataclass
class AuditEvent:
    event_id: str
    timestamp: datetime
    event_type: str  # tool_call, policy_decision, auth_event
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
    """
    Audit logging for compliance.
    
    Storage:
    - PostgreSQL for queryable logs
    - S3 for long-term immutable storage
    """
    
    def __init__(self, db: Database, s3_client: Optional[S3Client] = None):
        self.db = db
        self.s3 = s3_client
    
    async def log_event(self, event: AuditEvent):
        """Log audit event to database and optionally S3."""
        # Store in PostgreSQL
        await self.db.execute(
            """
            INSERT INTO audit_logs (
                event_id, timestamp, event_type, correlation_id,
                user_id, tool_name, action, status, latency_ms,
                request_size, response_size, error_message, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
            event.event_id, event.timestamp, event.event_type,
            event.correlation_id, event.user_id, event.tool_name,
            event.action, event.status, event.latency_ms,
            event.request_size, event.response_size, event.error_message,
            json.dumps(event.metadata)
        )
        
        # Async write to S3 for immutable storage
        if self.s3:
            await self._write_to_s3(event)
    
    async def log_tool_call(
        self,
        tool_name: str,
        params: Dict,
        result: Any,
        latency: float,
        context: ExecutionContext
    ):
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            event_type="tool_call",
            correlation_id=context.correlation_id,
            user_id=self._mask_pii(context.user_id),
            tool_name=tool_name,
            action="invoke",
            status="success",
            latency_ms=latency * 1000,
            request_size=len(json.dumps(params)),
            response_size=len(json.dumps(result)),
            error_message=None,
            metadata={"tool_version": context.tool_version}
        )
        await self.log_event(event)
    
    def _mask_pii(self, value: str) -> str:
        """Mask PII for logging."""
        if not value:
            return value
        if len(value) <= 4:
            return "***"
        return f"{value[:2]}***{value[-2:]}"
```

---

## 4. Data Models

### 4.1 Core Domain Models

```python
# Domain Models

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class ToolStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"

class Tool(BaseModel):
    """MCP Tool definition."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=500)
    version: str = Field(default="1.0.0")
    bundle_id: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    http_method: str
    api_path: str
    status: ToolStatus = ToolStatus.ACTIVE
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "GetNearbyDealers",
                "description": "Find Maruti Suzuki dealers near a location",
                "version": "1.0.0",
                "bundle_id": "service-booking",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "latitude": {"type": "number"},
                        "longitude": {"type": "number"},
                        "radius_km": {"type": "integer", "default": 10}
                    },
                    "required": ["latitude", "longitude"]
                }
            }
        }

class ToolBundle(BaseModel):
    """Logical grouping of tools (MCP Product)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    version: str = "1.0.0"
    tools: List[str] = []  # Tool IDs
    owner: str
    status: ToolStatus = ToolStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
class OpenAPISpec(BaseModel):
    """Stored OpenAPI specification."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str
    content: str  # YAML/JSON content
    content_hash: str
    bundle_id: str
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

class User(BaseModel):
    """Platform user."""
    id: str
    email: str
    name: str
    roles: List[str]
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime]

class Policy(BaseModel):
    """Access control policy."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    type: str  # "rbac", "rate_limit", "allow_list", "deny_list"
    rules: Dict[str, Any]
    priority: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.2 Request/Response Models

```python
# API Request/Response Models

class ToolCallRequest(BaseModel):
    """Request to execute a tool."""
    tool_name: str
    arguments: Dict[str, Any]
    
class ToolCallResponse(BaseModel):
    """Response from tool execution."""
    success: bool
    data: Optional[Any]
    error: Optional[str]
    latency_ms: float
    correlation_id: str

class ChatMessage(BaseModel):
    """Chat message for conversation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Conversation(BaseModel):
    """Chat conversation session."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}

# Service Booking Specific Models

class Vehicle(BaseModel):
    """Customer vehicle."""
    registration_number: str
    make: str
    model: str
    year: int
    vin: Optional[str]
    
class Dealer(BaseModel):
    """MSIL Dealer."""
    id: str
    name: str
    address: str
    city: str
    state: str
    pincode: str
    latitude: float
    longitude: float
    phone: str
    rating: Optional[float]
    distance_km: Optional[float]

class TimeSlot(BaseModel):
    """Available service slot."""
    id: str
    dealer_id: str
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    available: bool
    service_type: str

class ServiceBooking(BaseModel):
    """Service booking record."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_mobile: str
    vehicle_registration: str
    dealer_id: str
    slot_id: str
    service_date: str
    service_time: str
    service_type: str
    status: str = "confirmed"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str]
```

---

## 5. API Design

### 5.1 MCP Protocol Endpoints

```yaml
# MCP Protocol API

/mcp:
  post:
    summary: MCP JSON-RPC endpoint
    description: Handle all MCP protocol requests
    requestBody:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/MCPRequest'
          examples:
            tools_list:
              summary: List available tools
              value:
                jsonrpc: "2.0"
                id: 1
                method: "tools/list"
                params: {}
            tools_call:
              summary: Execute a tool
              value:
                jsonrpc: "2.0"
                id: 2
                method: "tools/call"
                params:
                  name: "GetNearbyDealers"
                  arguments:
                    latitude: 18.5912
                    longitude: 73.7389
    responses:
      200:
        description: MCP response
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MCPResponse'

/mcp/sse:
  get:
    summary: Server-Sent Events for streaming
    description: SSE endpoint for real-time updates
    responses:
      200:
        description: SSE stream
        content:
          text/event-stream:
            schema:
              type: string
```

### 5.2 Admin API Endpoints

```yaml
# Admin API

/api/admin/tools:
  get:
    summary: List all tools
    parameters:
      - name: bundle_id
        in: query
        schema:
          type: string
      - name: status
        in: query
        schema:
          type: string
          enum: [active, inactive, deprecated]
      - name: page
        in: query
        schema:
          type: integer
          default: 1
      - name: limit
        in: query
        schema:
          type: integer
          default: 20
    responses:
      200:
        description: List of tools
        content:
          application/json:
            schema:
              type: object
              properties:
                tools:
                  type: array
                  items:
                    $ref: '#/components/schemas/Tool'
                total:
                  type: integer
                page:
                  type: integer
                limit:
                  type: integer

/api/admin/tools/{tool_id}:
  get:
    summary: Get tool details
    parameters:
      - name: tool_id
        in: path
        required: true
        schema:
          type: string
    responses:
      200:
        description: Tool details
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Tool'
  
  put:
    summary: Update tool
    parameters:
      - name: tool_id
        in: path
        required: true
        schema:
          type: string
    requestBody:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ToolUpdate'
    responses:
      200:
        description: Updated tool

/api/admin/openapi:
  post:
    summary: Upload OpenAPI specification
    description: Upload and process OpenAPI spec to generate tools
    requestBody:
      content:
        multipart/form-data:
          schema:
            type: object
            properties:
              file:
                type: string
                format: binary
              bundle_id:
                type: string
              auto_publish:
                type: boolean
                default: false
    responses:
      200:
        description: Generated tools
        content:
          application/json:
            schema:
              type: object
              properties:
                spec_id:
                  type: string
                tools_generated:
                  type: integer
                tools:
                  type: array
                  items:
                    $ref: '#/components/schemas/Tool'

/api/admin/bundles:
  get:
    summary: List tool bundles
  post:
    summary: Create tool bundle

/api/admin/policies:
  get:
    summary: List policies
  post:
    summary: Create policy

/api/admin/audit-logs:
  get:
    summary: Query audit logs
    parameters:
      - name: start_date
        in: query
        schema:
          type: string
          format: date-time
      - name: end_date
        in: query
        schema:
          type: string
          format: date-time
      - name: tool_name
        in: query
        schema:
          type: string
      - name: user_id
        in: query
        schema:
          type: string
      - name: status
        in: query
        schema:
          type: string
          enum: [success, failure, denied]
    responses:
      200:
        description: Audit logs
        content:
          application/json:
            schema:
              type: object
              properties:
                logs:
                  type: array
                  items:
                    $ref: '#/components/schemas/AuditLog'

/api/admin/metrics:
  get:
    summary: Get platform metrics
    responses:
      200:
        description: Metrics summary
        content:
          application/json:
            schema:
              type: object
              properties:
                total_tool_calls:
                  type: integer
                error_rate:
                  type: number
                avg_latency_ms:
                  type: number
                active_tools:
                  type: integer
                tools_by_bundle:
                  type: object
```

### 5.3 Chat API Endpoints

```yaml
# Chat API

/api/chat/conversations:
  get:
    summary: List user conversations
    responses:
      200:
        description: List of conversations
  post:
    summary: Create new conversation
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              title:
                type: string
    responses:
      201:
        description: Created conversation

/api/chat/conversations/{conversation_id}/messages:
  get:
    summary: Get conversation messages
    parameters:
      - name: conversation_id
        in: path
        required: true
        schema:
          type: string
    responses:
      200:
        description: Messages
  
  post:
    summary: Send message
    parameters:
      - name: conversation_id
        in: path
        required: true
        schema:
          type: string
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              content:
                type: string
            required:
              - content
    responses:
      200:
        description: Assistant response (streamed)
        content:
          text/event-stream:
            schema:
              type: string
```

---

## 6. Sequence Diagrams

### 6.1 Service Booking Flow

```
┌───────┐     ┌─────────┐     ┌───────────┐     ┌──────────┐     ┌───────────┐
│ User  │     │ Chat UI │     │ MCP Server│     │   LLM    │     │ Mock/APIM │
└───┬───┘     └────┬────┘     └─────┬─────┘     └────┬─────┘     └─────┬─────┘
    │              │                │                │                  │
    │ "Book service│                │                │                  │
    │  for MH12AB" │                │                │                  │
    │─────────────>│                │                │                  │
    │              │                │                │                  │
    │              │ Get tools list │                │                  │
    │              │───────────────>│                │                  │
    │              │                │                │                  │
    │              │ Tools: [Resolve│Vehicle,        │                  │
    │              │  GetDealers,   │GetSlots,       │                  │
    │              │  CreateBooking]│                │                  │
    │              │<───────────────│                │                  │
    │              │                │                │                  │
    │              │ User msg + tools                │                  │
    │              │────────────────────────────────>│                  │
    │              │                │                │                  │
    │              │ Tool call: ResolveVehicle       │                  │
    │              │<────────────────────────────────│                  │
    │              │                │                │                  │
    │              │ Execute tool   │                │                  │
    │              │───────────────>│                │                  │
    │              │                │ POST /vehicle/resolve             │
    │              │                │─────────────────────────────────>│
    │              │                │                │                  │
    │              │                │ Vehicle details                   │
    │              │                │<─────────────────────────────────│
    │              │ Vehicle result │                │                  │
    │              │<───────────────│                │                  │
    │              │                │                │                  │
    │              │ Tool result    │                │                  │
    │              │────────────────────────────────>│                  │
    │              │                │                │                  │
    │              │ Tool call: GetNearbyDealers     │                  │
    │              │<────────────────────────────────│                  │
    │              │                │                │                  │
    │              │   ... (execute GetNearbyDealers)                   │
    │              │                │                │                  │
    │              │ Tool call: GetSlots             │                  │
    │              │<────────────────────────────────│                  │
    │              │                │                │                  │
    │              │   ... (execute GetSlots)        │                  │
    │              │                │                │                  │
    │              │ Tool call: CreateServiceBooking │                  │
    │              │<────────────────────────────────│                  │
    │              │                │                │                  │
    │              │ Execute tool   │                │                  │
    │              │───────────────>│                │                  │
    │              │                │ POST /booking/create              │
    │              │                │─────────────────────────────────>│
    │              │                │                │                  │
    │              │                │ Booking ID: BK12345              │
    │              │                │<─────────────────────────────────│
    │              │                │                │                  │
    │              │ Booking result │                │                  │
    │              │<───────────────│                │                  │
    │              │                │                │                  │
    │              │ Booking result │                │                  │
    │              │────────────────────────────────>│                  │
    │              │                │                │                  │
    │              │ Final response: "Your booking   │                  │
    │              │ BK12345 is confirmed..."        │                  │
    │              │<────────────────────────────────│                  │
    │              │                │                │                  │
    │ Booking      │                │                │                  │
    │ confirmation │                │                │                  │
    │<─────────────│                │                │                  │
```

### 6.2 OpenAPI Tool Generation Flow

```
┌───────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐     ┌────────┐
│   Admin   │     │ Admin UI  │     │MCP Server │     │  Parser   │     │Database│
└─────┬─────┘     └─────┬─────┘     └─────┬─────┘     └─────┬─────┘     └────┬───┘
      │                 │                 │                 │                │
      │ Upload OpenAPI  │                 │                 │                │
      │ spec file       │                 │                 │                │
      │────────────────>│                 │                 │                │
      │                 │                 │                 │                │
      │                 │ POST /admin/    │                 │                │
      │                 │ openapi         │                 │                │
      │                 │────────────────>│                 │                │
      │                 │                 │                 │                │
      │                 │                 │ Parse spec      │                │
      │                 │                 │────────────────>│                │
      │                 │                 │                 │                │
      │                 │                 │                 │ Validate       │
      │                 │                 │                 │ OpenAPI 3.x    │
      │                 │                 │                 │───┐            │
      │                 │                 │                 │   │            │
      │                 │                 │                 │<──┘            │
      │                 │                 │                 │                │
      │                 │                 │                 │ For each       │
      │                 │                 │                 │ operation:     │
      │                 │                 │                 │ - Generate     │
      │                 │                 │                 │   tool name    │
      │                 │                 │                 │ - Build input  │
      │                 │                 │                 │   schema       │
      │                 │                 │                 │ - Build output │
      │                 │                 │                 │   schema       │
      │                 │                 │                 │───┐            │
      │                 │                 │                 │   │            │
      │                 │                 │                 │<──┘            │
      │                 │                 │                 │                │
      │                 │                 │ Generated tools │                │
      │                 │                 │<────────────────│                │
      │                 │                 │                 │                │
      │                 │                 │ Store spec      │                │
      │                 │                 │─────────────────────────────────>│
      │                 │                 │                 │                │
      │                 │                 │ Store tools     │                │
      │                 │                 │─────────────────────────────────>│
      │                 │                 │                 │                │
      │                 │ Tools generated │                 │                │
      │                 │ (preview)       │                 │                │
      │                 │<────────────────│                 │                │
      │                 │                 │                 │                │
      │ Review tools    │                 │                 │                │
      │<────────────────│                 │                 │                │
      │                 │                 │                 │                │
      │ Approve/Publish │                 │                 │                │
      │────────────────>│                 │                 │                │
      │                 │                 │                 │                │
      │                 │ PUT /tools/     │                 │                │
      │                 │ {id}/publish    │                 │                │
      │                 │────────────────>│                 │                │
      │                 │                 │                 │                │
      │                 │                 │ Update status   │                │
      │                 │                 │─────────────────────────────────>│
      │                 │                 │                 │                │
      │                 │                 │ Invalidate      │                │
      │                 │                 │ cache           │                │
      │                 │                 │───┐             │                │
      │                 │                 │   │             │                │
      │                 │                 │<──┘             │                │
      │                 │                 │                 │                │
      │                 │ Published       │                 │                │
      │                 │<────────────────│                 │                │
      │                 │                 │                 │                │
      │ Success         │                 │                 │                │
      │<────────────────│                 │                 │                │
```

### 6.3 Authentication Flow

```
┌───────┐     ┌─────────┐     ┌───────────┐     ┌───────────┐
│ User  │     │ Chat UI │     │MCP Server │     │   IdP     │
└───┬───┘     └────┬────┘     └─────┬─────┘     └─────┬─────┘
    │              │                │                  │
    │ Access app   │                │                  │
    │─────────────>│                │                  │
    │              │                │                  │
    │              │ Check session  │                  │
    │              │───┐            │                  │
    │              │   │ No valid   │                  │
    │              │<──┘ session    │                  │
    │              │                │                  │
    │ Redirect to  │                │                  │
    │ login        │                │                  │
    │<─────────────│                │                  │
    │              │                │                  │
    │ Login page   │                │                  │
    │──────────────────────────────────────────────────>
    │              │                │                  │
    │ Enter creds  │                │                  │
    │──────────────────────────────────────────────────>
    │              │                │                  │
    │ Auth code    │                │                  │
    │<──────────────────────────────────────────────────
    │              │                │                  │
    │ Redirect with│                │                  │
    │ auth code    │                │                  │
    │─────────────>│                │                  │
    │              │                │                  │
    │              │ Exchange code  │                  │
    │              │ for token      │                  │
    │              │────────────────────────────────────>
    │              │                │                  │
    │              │ Access token + │                  │
    │              │ refresh token  │                  │
    │              │<────────────────────────────────────
    │              │                │                  │
    │              │ Store session  │                  │
    │              │───┐            │                  │
    │              │   │            │                  │
    │              │<──┘            │                  │
    │              │                │                  │
    │              │ API request    │                  │
    │              │ with token     │                  │
    │              │───────────────>│                  │
    │              │                │                  │
    │              │                │ Validate token   │
    │              │                │──────────────────>
    │              │                │                  │
    │              │                │ Token valid      │
    │              │                │<──────────────────
    │              │                │                  │
    │              │ Response       │                  │
    │              │<───────────────│                  │
    │              │                │                  │
    │ Show content │                │                  │
    │<─────────────│                │                  │
```

---

## 7. Security Design

### 7.1 Authentication Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AUTHENTICATION FLOW                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐                                    ┌─────────────────────┐ │
│  │   Client    │                                    │  Identity Provider  │ │
│  │  (Browser)  │                                    │  (Cognito/Auth0)    │ │
│  └──────┬──────┘                                    └──────────┬──────────┘ │
│         │                                                      │            │
│         │ 1. Login request                                     │            │
│         │─────────────────────────────────────────────────────>│            │
│         │                                                      │            │
│         │ 2. Authorization code                                │            │
│         │<─────────────────────────────────────────────────────│            │
│         │                                                      │            │
│  ┌──────┴──────┐                                               │            │
│  │   Chat UI   │                                               │            │
│  └──────┬──────┘                                               │            │
│         │ 3. Exchange code for tokens                          │            │
│         │─────────────────────────────────────────────────────>│            │
│         │                                                      │            │
│         │ 4. Access Token + Refresh Token                      │            │
│         │<─────────────────────────────────────────────────────│            │
│         │                                                      │            │
│         │                    ┌─────────────┐                   │            │
│         │ 5. API Request     │ MCP Server  │                   │            │
│         │ Authorization:     │             │                   │            │
│         │ Bearer <token>     │             │                   │            │
│         │───────────────────>│             │                   │            │
│         │                    │             │                   │            │
│         │                    │ 6. Validate │                   │            │
│         │                    │    token    │                   │            │
│         │                    │─────────────────────────────────>            │
│         │                    │             │                   │            │
│         │                    │ 7. Token    │                   │            │
│         │                    │    valid    │                   │            │
│         │                    │<─────────────────────────────────            │
│         │                    │             │                   │            │
│         │ 8. Response        │             │                   │            │
│         │<───────────────────│             │                   │            │
│         │                    └─────────────┘                   │            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 JWT Token Structure

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
    "name": "John Doe",
    "roles": ["user", "developer"],
    "permissions": [
      "tools:execute",
      "tools:read",
      "conversations:create"
    ]
  }
}
```

### 7.3 Authorization Matrix

| Role | tools:list | tools:execute | tools:write | policies:read | policies:write | audit:read | users:manage |
|------|------------|---------------|-------------|---------------|----------------|------------|--------------|
| **user** | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **developer** | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| **operator** | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ |
| **admin** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

### 7.4 Input Validation Rules

```python
# Input Validation Configuration

VALIDATION_RULES = {
    # Size limits
    "max_request_size": 1 * 1024 * 1024,  # 1 MB
    "max_string_length": 10000,
    "max_array_items": 100,
    "max_object_depth": 10,
    
    # Content validation
    "allow_html": False,
    "allow_scripts": False,
    "sanitize_output": True,
    
    # Schema validation
    "strict_schema": True,
    "additional_properties": False,
    
    # Rate limiting
    "requests_per_minute": 100,
    "tools_per_minute": 50,
}

# Blocked patterns (prompt injection prevention)
BLOCKED_PATTERNS = [
    r"ignore previous instructions",
    r"disregard all prior",
    r"system:\s*",
    r"<script",
    r"javascript:",
]
```

### 7.5 Secrets Management

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SECRETS ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  LOCAL DEVELOPMENT                         AWS PRODUCTION                   │
│  ─────────────────                         ──────────────                   │
│                                                                              │
│  ┌─────────────────┐                      ┌─────────────────────────────┐  │
│  │   .env.local    │                      │   AWS Secrets Manager       │  │
│  │                 │                      │                             │  │
│  │ DB_PASSWORD=... │                      │ /msil-mcp/dev/db-password   │  │
│  │ LLM_API_KEY=... │                      │ /msil-mcp/dev/llm-api-key   │  │
│  │ JWT_SECRET=...  │                      │ /msil-mcp/dev/jwt-secret    │  │
│  │                 │                      │ /msil-mcp/dev/msil-apim-*   │  │
│  └─────────────────┘                      └─────────────────────────────┘  │
│         │                                            │                      │
│         │                                            │                      │
│         ▼                                            ▼                      │
│  ┌─────────────────┐                      ┌─────────────────────────────┐  │
│  │   Application   │                      │        Application          │  │
│  │   (reads env)   │                      │   (reads via AWS SDK)       │  │
│  └─────────────────┘                      └─────────────────────────────┘  │
│                                                                              │
│  NEVER STORED:                                                              │
│  ─────────────                                                              │
│  • Secrets in code                                                          │
│  • Secrets in logs                                                          │
│  • Secrets in API responses                                                 │
│  • Secrets in audit trails                                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Frontend Architecture

### 8.1 Project Structure

```
frontend/
├── chat-ui/                          # Chat Interface
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                   # Shadcn/UI components
│   │   │   │   ├── button.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── dialog.tsx
│   │   │   │   └── ...
│   │   │   ├── chat/
│   │   │   │   ├── ChatContainer.tsx
│   │   │   │   ├── MessageList.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   ├── ToolExecutionCard.tsx
│   │   │   │   ├── InputArea.tsx
│   │   │   │   └── QuickActions.tsx
│   │   │   ├── booking/
│   │   │   │   ├── DealerCard.tsx
│   │   │   │   ├── SlotPicker.tsx
│   │   │   │   ├── BookingConfirmation.tsx
│   │   │   │   └── VehicleInfo.tsx
│   │   │   └── layout/
│   │   │       ├── Header.tsx
│   │   │       ├── Sidebar.tsx
│   │   │       └── Footer.tsx
│   │   ├── hooks/
│   │   │   ├── useChat.ts
│   │   │   ├── useMCP.ts
│   │   │   ├── useAuth.ts
│   │   │   └── useConversation.ts
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   ├── mcp-client.ts
│   │   │   ├── llm-client.ts
│   │   │   └── utils.ts
│   │   ├── stores/
│   │   │   ├── chatStore.ts
│   │   │   ├── authStore.ts
│   │   │   └── uiStore.ts
│   │   ├── types/
│   │   │   ├── chat.ts
│   │   │   ├── mcp.ts
│   │   │   └── booking.ts
│   │   ├── styles/
│   │   │   ├── globals.css
│   │   │   └── themes/
│   │   │       └── msil.css
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   │   ├── msil-logo.svg
│   │   └── favicon.ico
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
│
└── admin-ui/                         # Admin Interface
    ├── src/
    │   ├── components/
    │   │   ├── ui/                   # Shared Shadcn/UI
    │   │   ├── dashboard/
    │   │   │   ├── KPICards.tsx
    │   │   │   ├── InvocationChart.tsx
    │   │   │   ├── ErrorRateChart.tsx
    │   │   │   └── RecentActivity.tsx
    │   │   ├── tools/
    │   │   │   ├── ToolList.tsx
    │   │   │   ├── ToolDetail.tsx
    │   │   │   ├── ToolEditor.tsx
    │   │   │   └── SchemaViewer.tsx
    │   │   ├── openapi/
    │   │   │   ├── SpecUploader.tsx
    │   │   │   ├── ToolPreview.tsx
    │   │   │   └── VersionHistory.tsx
    │   │   ├── policies/
    │   │   │   ├── PolicyList.tsx
    │   │   │   ├── PolicyEditor.tsx
    │   │   │   └── RoleManager.tsx
    │   │   ├── audit/
    │   │   │   ├── AuditLogTable.tsx
    │   │   │   ├── LogDetail.tsx
    │   │   │   └── ExportDialog.tsx
    │   │   └── layout/
    │   │       ├── AdminHeader.tsx
    │   │       ├── Sidebar.tsx
    │   │       └── Breadcrumb.tsx
    │   ├── hooks/
    │   ├── lib/
    │   ├── stores/
    │   ├── pages/
    │   │   ├── Dashboard.tsx
    │   │   ├── Tools.tsx
    │   │   ├── OpenAPI.tsx
    │   │   ├── Policies.tsx
    │   │   ├── AuditLogs.tsx
    │   │   ├── Settings.tsx
    │   │   └── Users.tsx
    │   ├── App.tsx
    │   └── main.tsx
    └── ...
```

### 8.2 Component Design - Chat Interface

```tsx
// ChatContainer.tsx - Main Chat Component

import { useState, useEffect, useRef } from 'react';
import { useChat } from '@/hooks/useChat';
import { useMCP } from '@/hooks/useMCP';
import { MessageList } from './MessageList';
import { InputArea } from './InputArea';
import { QuickActions } from './QuickActions';
import { Message, ToolExecution } from '@/types/chat';

export function ChatContainer() {
  const { messages, sendMessage, isLoading } = useChat();
  const { tools, executeTool } = useMCP();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const handleSendMessage = async (content: string) => {
    await sendMessage(content);
  };
  
  const handleQuickAction = (action: string) => {
    const prompts: Record<string, string> = {
      'book-service': 'I want to book a service appointment for my car',
      'check-status': 'Check my booking status',
      'find-dealer': 'Find nearest Maruti Suzuki dealers'
    };
    handleSendMessage(prompts[action] || action);
  };
  
  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <header className="border-b px-6 py-4 flex items-center gap-4">
        <img src="/msil-logo.svg" alt="MSIL" className="h-10" />
        <div>
          <h1 className="text-xl font-semibold text-gray-900">
            AI Service Assistant
          </h1>
          <p className="text-sm text-gray-500">
            Powered by MCP
          </p>
        </div>
      </header>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <MessageList messages={messages} />
        <div ref={messagesEndRef} />
      </div>
      
      {/* Quick Actions */}
      <QuickActions onAction={handleQuickAction} />
      
      {/* Input */}
      <InputArea 
        onSend={handleSendMessage}
        isLoading={isLoading}
        placeholder="Type your message..."
      />
    </div>
  );
}
```

### 8.3 Component Design - Tool Execution Card

```tsx
// ToolExecutionCard.tsx - Shows tool execution progress

import { useState } from 'react';
import { ChevronDown, ChevronUp, Check, Loader2, AlertCircle } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ToolExecution } from '@/types/chat';

interface ToolExecutionCardProps {
  execution: ToolExecution;
}

export function ToolExecutionCard({ execution }: ToolExecutionCardProps) {
  const [expanded, setExpanded] = useState(false);
  
  const statusIcon = {
    pending: <Loader2 className="h-4 w-4 animate-spin text-blue-500" />,
    success: <Check className="h-4 w-4 text-green-500" />,
    error: <AlertCircle className="h-4 w-4 text-red-500" />
  };
  
  const statusColor = {
    pending: 'bg-blue-100 text-blue-800',
    success: 'bg-green-100 text-green-800',
    error: 'bg-red-100 text-red-800'
  };
  
  return (
    <Card className="my-2 border-l-4 border-l-blue-500">
      <CardContent className="p-3">
        <div 
          className="flex items-center justify-between cursor-pointer"
          onClick={() => setExpanded(!expanded)}
        >
          <div className="flex items-center gap-2">
            {statusIcon[execution.status]}
            <span className="font-medium text-sm">
              {execution.toolName}
            </span>
            <Badge variant="outline" className={statusColor[execution.status]}>
              {execution.status}
            </Badge>
            {execution.latencyMs && (
              <span className="text-xs text-gray-500">
                {execution.latencyMs}ms
              </span>
            )}
          </div>
          {expanded ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </div>
        
        {expanded && (
          <div className="mt-3 pt-3 border-t space-y-2">
            <div>
              <span className="text-xs font-medium text-gray-500">Input:</span>
              <pre className="mt-1 p-2 bg-gray-50 rounded text-xs overflow-x-auto">
                {JSON.stringify(execution.input, null, 2)}
              </pre>
            </div>
            {execution.output && (
              <div>
                <span className="text-xs font-medium text-gray-500">Output:</span>
                <pre className="mt-1 p-2 bg-gray-50 rounded text-xs overflow-x-auto">
                  {JSON.stringify(execution.output, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

### 8.4 State Management

```typescript
// stores/chatStore.ts - Zustand store for chat state

import { create } from 'zustand';
import { Message, Conversation, ToolExecution } from '@/types/chat';

interface ChatState {
  // State
  conversations: Conversation[];
  currentConversationId: string | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  toolExecutions: Record<string, ToolExecution>;
  
  // Actions
  setCurrentConversation: (id: string) => void;
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  addToolExecution: (execution: ToolExecution) => void;
  updateToolExecution: (id: string, updates: Partial<ToolExecution>) => void;
  clearChat: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  // Initial state
  conversations: [],
  currentConversationId: null,
  messages: [],
  isLoading: false,
  error: null,
  toolExecutions: {},
  
  // Actions
  setCurrentConversation: (id) => set({ currentConversationId: id }),
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  
  updateMessage: (id, updates) => set((state) => ({
    messages: state.messages.map((m) =>
      m.id === id ? { ...m, ...updates } : m
    )
  })),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  setError: (error) => set({ error }),
  
  addToolExecution: (execution) => set((state) => ({
    toolExecutions: {
      ...state.toolExecutions,
      [execution.id]: execution
    }
  })),
  
  updateToolExecution: (id, updates) => set((state) => ({
    toolExecutions: {
      ...state.toolExecutions,
      [id]: { ...state.toolExecutions[id], ...updates }
    }
  })),
  
  clearChat: () => set({
    messages: [],
    toolExecutions: {},
    error: null
  })
}));
```

### 8.5 MSIL Theme Configuration

```css
/* styles/themes/msil.css - MSIL Brand Theme */

:root {
  /* MSIL Brand Colors */
  --msil-blue-primary: #003D79;
  --msil-blue-secondary: #0056A8;
  --msil-red: #E31837;
  --msil-silver: #C0C0C0;
  --msil-dark-gray: #333333;
  
  /* Semantic Colors */
  --color-primary: var(--msil-blue-primary);
  --color-primary-hover: var(--msil-blue-secondary);
  --color-accent: var(--msil-red);
  --color-background: #FFFFFF;
  --color-surface: #F8F9FA;
  --color-text: var(--msil-dark-gray);
  --color-text-muted: #6B7280;
  --color-border: #E5E7EB;
  
  /* Chat Colors */
  --color-user-bubble: var(--msil-blue-primary);
  --color-user-text: #FFFFFF;
  --color-assistant-bubble: #F3F4F6;
  --color-assistant-text: var(--msil-dark-gray);
  
  /* Status Colors */
  --color-success: #10B981;
  --color-error: #EF4444;
  --color-warning: #F59E0B;
  --color-info: #3B82F6;
  
  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  
  /* Border Radius */
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-full: 9999px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
}

/* Global Styles */
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: var(--color-text);
  background-color: var(--color-background);
}

/* Button Variants */
.btn-primary {
  background-color: var(--msil-blue-primary);
  color: white;
}

.btn-primary:hover {
  background-color: var(--msil-blue-secondary);
}

.btn-accent {
  background-color: var(--msil-red);
  color: white;
}

/* Chat Bubbles */
.message-user {
  background-color: var(--color-user-bubble);
  color: var(--color-user-text);
  border-radius: var(--radius-lg) var(--radius-lg) var(--radius-sm) var(--radius-lg);
}

.message-assistant {
  background-color: var(--color-assistant-bubble);
  color: var(--color-assistant-text);
  border-radius: var(--radius-lg) var(--radius-lg) var(--radius-lg) var(--radius-sm);
}
```

---

## 9. Infrastructure Design

### 9.1 Local Development Infrastructure

```yaml
# infrastructure/local/docker-compose.infra.yml

version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: msil-mcp-postgres
    environment:
      POSTGRES_USER: mcp_user
      POSTGRES_PASSWORD: mcp_local_password
      POSTGRES_DB: mcp_server
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts/01-init.sql:/docker-entrypoint-initdb.d/01-init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mcp_user -d mcp_server"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - mcp-network

  redis:
    image: redis:7-alpine
    container_name: msil-mcp-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - mcp-network

  # Optional: OPA for policy engine
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
      - ./policies:/policies
    networks:
      - mcp-network

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  mcp-network:
    driver: bridge
```

### 9.2 AWS Infrastructure (Terraform)

```hcl
# infrastructure/terraform/environments/dev/main.tf

terraform {
  required_version = ">= 1.7.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket         = "nagarro-msil-mcp-terraform-state"
    key            = "environments/dev/terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "nagarro-msil-mcp-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "msil-mcp"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Local variables
locals {
  name_prefix = "${var.project}-${var.environment}"
}

# Networking Module
module "networking" {
  source = "../../modules/networking"
  
  name_prefix = local.name_prefix
  vpc_cidr    = var.vpc_cidr
  
  availability_zones = ["ap-south-1a", "ap-south-1b"]
}

# RDS Module
module "rds" {
  source = "../../modules/rds"
  
  name_prefix        = local.name_prefix
  vpc_id             = module.networking.vpc_id
  subnet_ids         = module.networking.private_subnet_ids
  security_group_ids = [module.networking.db_security_group_id]
  
  instance_class     = var.db_instance_class
  allocated_storage  = var.db_allocated_storage
  database_name      = "mcp_server"
  master_username    = "mcp_admin"
}

# ElastiCache Module
module "elasticache" {
  source = "../../modules/elasticache"
  
  name_prefix        = local.name_prefix
  vpc_id             = module.networking.vpc_id
  subnet_ids         = module.networking.private_subnet_ids
  security_group_ids = [module.networking.cache_security_group_id]
  
  node_type          = var.cache_node_type
}

# ECR Repository
module "ecr" {
  source = "../../modules/ecr"
  
  name_prefix = local.name_prefix
  repositories = ["mcp-server", "mock-api"]
}

# ALB Module
module "alb" {
  source = "../../modules/alb"
  
  name_prefix        = local.name_prefix
  vpc_id             = module.networking.vpc_id
  subnet_ids         = module.networking.public_subnet_ids
  security_group_ids = [module.networking.alb_security_group_id]
}

# ECS Module
module "ecs" {
  source = "../../modules/ecs"
  
  name_prefix        = local.name_prefix
  vpc_id             = module.networking.vpc_id
  subnet_ids         = module.networking.private_subnet_ids
  security_group_ids = [module.networking.ecs_security_group_id]
  
  alb_target_group_arn = module.alb.target_group_arn
  
  container_image    = "${module.ecr.repository_urls["mcp-server"]}:latest"
  container_port     = 8000
  cpu                = var.ecs_cpu
  memory             = var.ecs_memory
  desired_count      = var.desired_count
  
  environment_variables = {
    ENVIRONMENT        = var.environment
    DB_HOST           = module.rds.endpoint
    DB_NAME           = "mcp_server"
    REDIS_HOST        = module.elasticache.endpoint
    API_GATEWAY_MODE  = var.api_gateway_mode
    MSIL_APIM_BASE_URL = var.msil_apim_base_url
  }
  
  secrets = {
    DB_PASSWORD          = module.rds.secret_arn
    MSIL_APIM_CLIENT_ID  = aws_secretsmanager_secret.msil_apim_client_id.arn
    MSIL_APIM_SECRET     = aws_secretsmanager_secret.msil_apim_secret.arn
    LLM_API_KEY          = aws_secretsmanager_secret.llm_api_key.arn
  }
}

# CloudFront + S3 for UI
module "cloudfront_chat" {
  source = "../../modules/cloudfront"
  
  name_prefix    = "${local.name_prefix}-chat"
  domain_aliases = []  # Add custom domain later
}

module "cloudfront_admin" {
  source = "../../modules/cloudfront"
  
  name_prefix    = "${local.name_prefix}-admin"
  domain_aliases = []
}

# Secrets
resource "aws_secretsmanager_secret" "msil_apim_client_id" {
  name = "${local.name_prefix}/msil-apim-client-id"
}

resource "aws_secretsmanager_secret" "msil_apim_secret" {
  name = "${local.name_prefix}/msil-apim-secret"
}

resource "aws_secretsmanager_secret" "llm_api_key" {
  name = "${local.name_prefix}/llm-api-key"
}

# Outputs
output "alb_dns_name" {
  value = module.alb.dns_name
}

output "chat_ui_url" {
  value = module.cloudfront_chat.distribution_domain_name
}

output "admin_ui_url" {
  value = module.cloudfront_admin.distribution_domain_name
}

output "rds_endpoint" {
  value     = module.rds.endpoint
  sensitive = true
}
```

### 9.3 ECS Module

```hcl
# infrastructure/terraform/modules/ecs/main.tf

resource "aws_ecs_cluster" "main" {
  name = "${var.name_prefix}-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "mcp_server" {
  family                   = "${var.name_prefix}-mcp-server"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn
  
  container_definitions = jsonencode([
    {
      name      = "mcp-server"
      image     = var.container_image
      essential = true
      
      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]
      
      environment = [
        for key, value in var.environment_variables : {
          name  = key
          value = value
        }
      ]
      
      secrets = [
        for key, arn in var.secrets : {
          name      = key
          valueFrom = arn
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.mcp_server.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "mcp-server"
        }
      }
      
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.container_port}/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
}

resource "aws_ecs_service" "mcp_server" {
  name            = "${var.name_prefix}-mcp-server"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.mcp_server.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = var.security_group_ids
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = var.alb_target_group_arn
    container_name   = "mcp-server"
    container_port   = var.container_port
  }
  
  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
  }
  
  lifecycle {
    ignore_changes = [desired_count]
  }
}

resource "aws_cloudwatch_log_group" "mcp_server" {
  name              = "/ecs/${var.name_prefix}-mcp-server"
  retention_in_days = 30
}

# Auto Scaling
resource "aws_appautoscaling_target" "ecs" {
  max_capacity       = 4
  min_capacity       = var.desired_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.mcp_server.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "cpu" {
  name               = "${var.name_prefix}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
```

---

## 10. Database Schema

### 10.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           DATABASE SCHEMA                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐   │
│  │   tool_bundles  │         │     tools       │         │  openapi_specs  │   │
│  ├─────────────────┤         ├─────────────────┤         ├─────────────────┤   │
│  │ id (PK)         │────┐    │ id (PK)         │    ┌────│ id (PK)         │   │
│  │ name            │    │    │ name            │    │    │ name            │   │
│  │ description     │    │    │ description     │    │    │ version         │   │
│  │ version         │    │    │ version         │    │    │ content         │   │
│  │ owner           │    └───>│ bundle_id (FK)  │<───┘    │ content_hash    │   │
│  │ status          │         │ input_schema    │         │ bundle_id (FK)  │   │
│  │ created_at      │         │ output_schema   │         │ uploaded_by     │   │
│  │ updated_at      │         │ http_method     │         │ uploaded_at     │   │
│  └─────────────────┘         │ api_path        │         └─────────────────┘   │
│                              │ status          │                                │
│                              │ tags            │                                │
│                              │ created_at      │                                │
│                              │ updated_at      │                                │
│                              │ created_by      │                                │
│                              └─────────────────┘                                │
│                                                                                  │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐   │
│  │     users       │         │   user_roles    │         │     roles       │   │
│  ├─────────────────┤         ├─────────────────┤         ├─────────────────┤   │
│  │ id (PK)         │────────>│ user_id (FK)    │         │ id (PK)         │   │
│  │ email           │         │ role_id (FK)    │<────────│ name            │   │
│  │ name            │         │ assigned_at     │         │ description     │   │
│  │ external_id     │         │ assigned_by     │         │ permissions     │   │
│  │ is_active       │         └─────────────────┘         │ created_at      │   │
│  │ created_at      │                                     └─────────────────┘   │
│  │ last_login      │                                                           │
│  └─────────────────┘                                                           │
│                                                                                  │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐   │
│  │    policies     │         │   audit_logs    │         │  conversations  │   │
│  ├─────────────────┤         ├─────────────────┤         ├─────────────────┤   │
│  │ id (PK)         │         │ id (PK)         │         │ id (PK)         │   │
│  │ name            │         │ event_id        │         │ user_id (FK)    │   │
│  │ description     │         │ timestamp       │         │ title           │   │
│  │ type            │         │ event_type      │         │ created_at      │   │
│  │ rules (JSONB)   │         │ correlation_id  │         │ updated_at      │   │
│  │ priority        │         │ user_id         │         │ metadata        │   │
│  │ is_active       │         │ tool_name       │         └────────┬────────┘   │
│  │ created_at      │         │ action          │                  │            │
│  │ updated_at      │         │ status          │                  │            │
│  └─────────────────┘         │ latency_ms      │                  │            │
│                              │ request_size    │         ┌────────▼────────┐   │
│                              │ response_size   │         │    messages     │   │
│                              │ error_message   │         ├─────────────────┤   │
│                              │ metadata        │         │ id (PK)         │   │
│                              └─────────────────┘         │ conversation_id │   │
│                                                          │ role            │   │
│                                                          │ content         │   │
│                                                          │ tool_calls      │   │
│                                                          │ created_at      │   │
│                                                          └─────────────────┘   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        service_bookings (Mock DB)                        │   │
│  ├─────────────────────────────────────────────────────────────────────────┤   │
│  │ id (PK) │ customer_mobile │ vehicle_reg │ dealer_id │ slot_id │ status  │   │
│  │ service_date │ service_time │ service_type │ notes │ created_at         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 SQL Schema

```sql
-- infrastructure/local/init-scripts/01-init.sql

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Tool Bundles
CREATE TABLE tool_bundles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    owner VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tools
CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    bundle_id UUID REFERENCES tool_bundles(id),
    input_schema JSONB NOT NULL,
    output_schema JSONB,
    http_method VARCHAR(10) NOT NULL,
    api_path VARCHAR(500) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    UNIQUE(name, version)
);

-- OpenAPI Specifications
CREATE TABLE openapi_specs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    bundle_id UUID REFERENCES tool_bundles(id),
    uploaded_by VARCHAR(100) NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name, version)
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100),
    external_id VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Roles
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    permissions JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User Roles
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by VARCHAR(100),
    PRIMARY KEY (user_id, role_id)
);

-- Policies
CREATE TABLE policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    type VARCHAR(50) NOT NULL,
    rules JSONB NOT NULL,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit Logs
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
    metadata JSONB DEFAULT '{}'
);

-- Conversations
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    title VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    tool_calls JSONB,
    tool_call_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Service Bookings (for demo/mock)
CREATE TABLE service_bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_number VARCHAR(20) NOT NULL UNIQUE,
    customer_mobile VARCHAR(15) NOT NULL,
    customer_name VARCHAR(100),
    vehicle_registration VARCHAR(20) NOT NULL,
    vehicle_make VARCHAR(50),
    vehicle_model VARCHAR(50),
    dealer_id VARCHAR(50) NOT NULL,
    dealer_name VARCHAR(100),
    slot_id VARCHAR(50),
    service_date DATE NOT NULL,
    service_time TIME NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'confirmed',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_tools_bundle_id ON tools(bundle_id);
CREATE INDEX idx_tools_status ON tools(status);
CREATE INDEX idx_tools_name_trgm ON tools USING gin(name gin_trgm_ops);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_tool_name ON audit_logs(tool_name);
CREATE INDEX idx_audit_logs_correlation_id ON audit_logs(correlation_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_service_bookings_mobile ON service_bookings(customer_mobile);
CREATE INDEX idx_service_bookings_registration ON service_bookings(vehicle_registration);

-- Insert default roles
INSERT INTO roles (name, description, permissions) VALUES
    ('admin', 'Full system access', '["tools:read", "tools:write", "tools:execute", "policies:read", "policies:write", "audit:read", "users:manage"]'),
    ('developer', 'Tool development access', '["tools:read", "tools:write", "tools:execute", "policies:read"]'),
    ('operator', 'Operations and monitoring', '["tools:read", "tools:execute", "audit:read", "metrics:read"]'),
    ('user', 'Standard user access', '["tools:read", "tools:execute"]');

-- Insert default bundle for service booking
INSERT INTO tool_bundles (name, description, owner) VALUES
    ('service-booking', 'MSIL Service Booking Tools', 'msil-mcp-platform');
```

---

## 11. Configuration Management

### 11.1 Configuration Structure

```yaml
# config/default.yaml - Base configuration

app:
  name: "MSIL MCP Server"
  version: "1.0.0"
  environment: "${ENVIRONMENT:development}"

server:
  host: "0.0.0.0"
  port: 8000
  workers: "${WORKERS:4}"
  reload: false
  log_level: "${LOG_LEVEL:INFO}"

database:
  host: "${DB_HOST:localhost}"
  port: "${DB_PORT:5432}"
  name: "${DB_NAME:mcp_server}"
  user: "${DB_USER:mcp_user}"
  password: "${DB_PASSWORD}"
  pool_size: 10
  max_overflow: 20

redis:
  host: "${REDIS_HOST:localhost}"
  port: "${REDIS_PORT:6379}"
  db: 0
  password: "${REDIS_PASSWORD:}"

api_gateway:
  mode: "${API_GATEWAY_MODE:mock}"
  
  mock:
    base_url: "${MOCK_API_URL:http://localhost:8080}"
    timeout: 30
    
  msil_apim:
    base_url: "${MSIL_APIM_BASE_URL}"
    auth:
      type: "oauth2"
      token_url: "${MSIL_AUTH_TOKEN_URL}"
      client_id: "${MSIL_APIM_CLIENT_ID}"
      client_secret: "${MSIL_APIM_CLIENT_SECRET}"
      scope: "${MSIL_APIM_SCOPE:api.read api.write}"
    headers:
      x-api-key: "${MSIL_API_KEY:}"
    timeout: 30
    retry:
      max_attempts: 3
      backoff_factor: 0.5
    circuit_breaker:
      failure_threshold: 5
      recovery_timeout: 60

llm:
  provider: "${LLM_PROVIDER:openai}"
  
  openai:
    api_key: "${LLM_API_KEY}"
    model: "${LLM_MODEL:gpt-4}"
    max_tokens: 4096
    temperature: 0.7
    
  azure:
    endpoint: "${AZURE_OPENAI_ENDPOINT}"
    api_key: "${AZURE_OPENAI_API_KEY}"
    deployment: "${AZURE_OPENAI_DEPLOYMENT}"
    api_version: "2024-02-15-preview"
    
  bedrock:
    region: "${AWS_REGION:ap-south-1}"
    model_id: "${BEDROCK_MODEL_ID:anthropic.claude-3-sonnet}"

security:
  jwt:
    secret: "${JWT_SECRET}"
    algorithm: "HS256"
    expiry_hours: 24
  cors:
    allowed_origins:
      - "${CHAT_UI_URL:http://localhost:3000}"
      - "${ADMIN_UI_URL:http://localhost:3001}"
    allowed_methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allowed_headers: ["*"]
  rate_limit:
    requests_per_minute: 100
    tools_per_minute: 50

observability:
  logging:
    format: "json"
    level: "${LOG_LEVEL:INFO}"
  metrics:
    enabled: true
    port: 9090
  tracing:
    enabled: "${ENABLE_TRACING:true}"
    exporter: "otlp"
    endpoint: "${OTEL_EXPORTER_OTLP_ENDPOINT:}"

cache:
  tool_ttl: 3600
  response_ttl: 300
  rate_limit_window: 60
```

### 11.2 Environment-Specific Overrides

```yaml
# config/development.yaml

server:
  reload: true
  log_level: "DEBUG"

security:
  cors:
    allowed_origins: ["*"]

observability:
  tracing:
    enabled: false
```

```yaml
# config/production.yaml

server:
  reload: false
  workers: 8
  log_level: "INFO"

database:
  pool_size: 20
  max_overflow: 40

security:
  cors:
    allowed_origins:
      - "https://chat.msil-mcp.nagarro.com"
      - "https://admin.msil-mcp.nagarro.com"

observability:
  tracing:
    enabled: true
    exporter: "xray"
```

---

## 12. Error Handling

### 12.1 Error Codes

```python
# Error Code Definitions

from enum import Enum

class ErrorCode(str, Enum):
    # Authentication/Authorization (1xxx)
    AUTH_REQUIRED = "E1001"
    INVALID_TOKEN = "E1002"
    TOKEN_EXPIRED = "E1003"
    INSUFFICIENT_PERMISSIONS = "E1004"
    
    # Validation (2xxx)
    INVALID_REQUEST = "E2001"
    SCHEMA_VALIDATION_FAILED = "E2002"
    MISSING_REQUIRED_FIELD = "E2003"
    INVALID_FIELD_VALUE = "E2004"
    
    # Tool Errors (3xxx)
    TOOL_NOT_FOUND = "E3001"
    TOOL_DISABLED = "E3002"
    TOOL_EXECUTION_FAILED = "E3003"
    TOOL_TIMEOUT = "E3004"
    
    # API Gateway Errors (4xxx)
    APIM_CONNECTION_FAILED = "E4001"
    APIM_TIMEOUT = "E4002"
    APIM_RATE_LIMITED = "E4003"
    APIM_ERROR = "E4004"
    
    # System Errors (5xxx)
    INTERNAL_ERROR = "E5001"
    DATABASE_ERROR = "E5002"
    CACHE_ERROR = "E5003"
    SERVICE_UNAVAILABLE = "E5004"
```

### 12.2 Error Response Format

```json
{
  "error": {
    "code": "E3001",
    "message": "Tool not found",
    "details": {
      "tool_name": "InvalidToolName",
      "suggestion": "Did you mean 'GetNearbyDealers'?"
    },
    "correlation_id": "abc-123-def",
    "timestamp": "2026-01-30T10:15:30.123Z"
  }
}
```

### 12.3 Error Handling Strategy

```python
# Exception Hierarchy

class MCPError(Exception):
    """Base exception for MCP Server."""
    def __init__(
        self, 
        code: ErrorCode, 
        message: str, 
        details: dict = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

class AuthenticationError(MCPError):
    """Authentication failed."""
    pass

class AuthorizationError(MCPError):
    """Permission denied."""
    pass

class ValidationError(MCPError):
    """Request validation failed."""
    pass

class ToolError(MCPError):
    """Tool-related error."""
    pass

class APIGatewayError(MCPError):
    """APIM integration error."""
    pass

# Global Exception Handler
@app.exception_handler(MCPError)
async def mcp_error_handler(request: Request, exc: MCPError):
    return JSONResponse(
        status_code=get_http_status(exc.code),
        content={
            "error": {
                "code": exc.code.value,
                "message": exc.message,
                "details": exc.details,
                "correlation_id": request.state.correlation_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
```

---

## 13. Testing Strategy

### 13.1 Test Pyramid

```
                    ┌───────────────┐
                    │   E2E Tests   │  ← Cypress/Playwright
                    │    (10%)      │
                    └───────┬───────┘
                            │
              ┌─────────────┴─────────────┐
              │    Integration Tests      │  ← pytest + testcontainers
              │          (30%)            │
              └─────────────┬─────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │           Unit Tests                   │  ← pytest
        │             (60%)                      │
        └────────────────────────────────────────┘
```

### 13.2 Test Categories

```python
# tests/unit/test_openapi_parser.py

import pytest
from app.core.generator.openapi_parser import OpenAPIToolGenerator

class TestOpenAPIToolGenerator:
    
    def test_parse_simple_get_operation(self):
        """Test parsing a simple GET operation."""
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/dealers": {
                    "get": {
                        "operationId": "getDealers",
                        "summary": "Get all dealers",
                        "parameters": [
                            {
                                "name": "city",
                                "in": "query",
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Success"
                            }
                        }
                    }
                }
            }
        }
        
        generator = OpenAPIToolGenerator(spec)
        tools = generator.generate_tools()
        
        assert len(tools) == 1
        assert tools[0].name == "getDealers"
        assert tools[0].http_method == "GET"
        assert "city" in tools[0].input_schema["properties"]
    
    def test_parse_post_with_body(self):
        """Test parsing POST operation with request body."""
        # ...
    
    def test_generate_tool_name_from_path(self):
        """Test tool name generation when operationId is missing."""
        # ...

# tests/integration/test_tool_execution.py

import pytest
from httpx import AsyncClient
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="module")
def postgres():
    with PostgresContainer("postgres:15") as pg:
        yield pg

@pytest.mark.asyncio
async def test_execute_tool_success(postgres, mock_api):
    """Test successful tool execution."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "GetNearbyDealers",
                    "arguments": {
                        "latitude": 18.5912,
                        "longitude": 73.7389
                    }
                }
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "result" in result
        assert result["result"]["isError"] == False

# tests/e2e/test_service_booking_flow.py

import pytest
from playwright.sync_api import Page, expect

def test_complete_booking_flow(page: Page):
    """E2E test for complete service booking journey."""
    # Navigate to chat
    page.goto("http://localhost:3000")
    
    # Wait for chat to load
    expect(page.locator(".chat-container")).to_be_visible()
    
    # Send booking request
    page.fill("input[placeholder='Type your message...']", 
              "Book a service for my car MH12AB1234 tomorrow at 10 AM")
    page.click("button[type='submit']")
    
    # Wait for tool executions
    expect(page.locator(".tool-execution-card")).to_be_visible(timeout=30000)
    
    # Verify booking confirmation
    expect(page.locator("text=Your booking")).to_be_visible(timeout=60000)
    expect(page.locator("text=BK")).to_be_visible()  # Booking ID
```

### 13.3 Test Configuration

```python
# pytest.ini

[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = 
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80

markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests
```

---

## Document Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Technical Lead | | | |
| Solution Architect | | | |
| Project Manager | | | |

---

**End of Design Document**
