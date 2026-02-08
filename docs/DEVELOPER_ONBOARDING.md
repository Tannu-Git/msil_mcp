# MSIL MCP Server - Developer Onboarding Guide

**Document Version**: 1.0  
**Date**: February 2, 2026  
**Classification**: Internal  
**Target Audience**: Developers, DevOps Engineers, QA Engineers

---

## Table of Contents

1. [Welcome to MSIL MCP](#welcome-to-msil-mcp)
2. [Platform Overview](#platform-overview)
3. [Technology Stack](#technology-stack)
4. [Environment Setup](#environment-setup)
5. [Project Structure](#project-structure)
6. [Running the Platform](#running-the-platform)
7. [Understanding Core Components](#understanding-core-components)
8. [Development Workflow](#development-workflow)
9. [Key Concepts](#key-concepts)
10. [Testing](#testing)
11. [Security & Compliance](#security--compliance)
12. [Troubleshooting](#troubleshooting)
13. [Useful Resources](#useful-resources)
14. [Getting Help](#getting-help)

---

## Welcome to MSIL MCP

The MSIL MCP (Model Context Protocol) Server is an enterprise-grade platform that provides secure, governed access to Maruti Suzuki India Limited's APIs through large language models (LLMs).

**Key Achievement**: Provides AI-powered service platform with zero-code tool generation from OpenAPI specifications, real-time metrics tracking, comprehensive security governance, and **exposure governance** for fine-grained tool visibility control.

**Current Status**: Phase 3 Complete (Exposure Governance) - Production Ready ✅

---

## Platform Overview

### What is MCP?

The **Model Context Protocol (MCP)** is a standardized protocol enabling secure communication between LLM applications and external services. It defines how tools (API operations) are discovered, described, and executed.

**Architecture Flow**:
```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  End User / UI   │       │   MCP Server     │       │   Backend APIs   │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ • Chat UI        │──────▶│ • Tool Registry  │──────▶│ • Maruti APIs    │
│ • Admin Portal   │◀──────│ • Governance     │◀──────│ • Third-party    │
│ • Agent App      │       │ • Security       │       │ • Legacy systems │
└──────────────────┘       └──────────────────┘       └──────────────────┘
```

### Core Capabilities

| Capability | Description |
|------------|-------------|
| **Zero-Code Tool Generation** | Import OpenAPI specs → Automatic MCP tool creation |
| **Multi-Layered Security** | Authentication → Authorization → Rate Limiting |
| **Exposure Governance (NEW)** | Two-layer security: Layer B (visibility) + Layer A (execution) |
| **Real-Time Metrics** | Track every tool execution with detailed analytics |
| **PII Protection** | Automatic masking of sensitive data |
| **Audit Logging** | Complete activity trail (12-month retention) |
| **Idempotent Operations** | Write operations are safely repeatable |
| **Tool Change Notifications** | Real-time updates when tool registry changes |
| **TTL Caching** | Configurable cache expiration for permissions (Phase 3) |

### Supported Use Cases

- **Service Booking**: AI-assisted vehicle service scheduling
- **Customer Queries**: Intelligent FAQ and support bot
- **Dealer Operations**: Automated dealer system interactions
- **Inventory Management**: Real-time inventory inquiries
- **Financial Services**: Loan and finance product info

---

## Technology Stack

### Backend

| Technology | Purpose | Version |
|-----------|---------|---------|
| **Python** | Runtime | 3.9+ |
| **FastAPI** | Web framework | 0.109.0 |
| **Uvicorn** | ASGI server | 0.27.0 |
| **SQLAlchemy** | ORM | 2.0.36 |
| **AsyncPG** | PostgreSQL driver | 0.30.0 |
| **Redis** | Caching & queuing | 5.0.1 |
| **Pydantic** | Data validation | 2.10.5 |
| **Python-Jose** | JWT handling | 3.3.0 |
| **HTTPX/AIOHTTP** | HTTP clients | 0.26.0 / 3.11.0 |
| **PyYAML** | YAML parsing | 6.0.1 |
| **Prometheus** | Metrics | 0.19.0 |

### Frontend (Admin UI)

| Technology | Purpose | Version |
|-----------|---------|---------|
| **Node.js** | Runtime | 18+ |
| **React** | UI framework | 18.2.0 |
| **TypeScript** | Type safety | 5.3.3 |
| **Vite** | Build tool | 5.1.0 |
| **Tailwind CSS** | Styling | 3.4.1 |
| **React Router** | Navigation | 6.22.0 |
| **Zustand** | State management | 4.5.0 |
| **Radix UI** | Components | Various |

### Frontend (Chat UI)

Same stack as Admin UI - separate Vite project with similar dependencies.

### Infrastructure

| Technology | Purpose |
|-----------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Local orchestration |
| **PostgreSQL** | Primary database |
| **Redis** | Session store & cache |
| **Git** | Version control |

---

## Environment Setup

### Prerequisites

Before you start, ensure you have installed:

#### Windows/Mac/Linux

```bash
# Required
- Python 3.9+ (https://www.python.org/downloads/)
- Node.js 18+ (https://nodejs.org/)
- Git (https://git-scm.com/)
- Docker Desktop (https://www.docker.com/products/docker-desktop) [Optional but recommended]

# For Windows specifically
- PowerShell 5.1+ (usually pre-installed)
- Windows Terminal (recommended, optional)
```

#### Verify Installations

```powershell
# PowerShell
python --version          # Should show Python 3.9+
node --version           # Should show Node 18+
npm --version            # Should show npm 9+
git --version            # Should show git 2.x+
docker --version         # Should show docker 20.x+ (if installed)
```

### Step 1: Clone Repository

```powershell
# Navigate to your desired directory
cd C:\Your\Project\Directory

# Clone the repository
git clone https://github.com/nagarro/msil-mcp.git
cd msil-mcp

# Verify structure
ls  # Should show: admin-ui, chat-ui, mcp-server, docs, infrastructure, etc.
```

### Step 2: Set Up MCP Server Environment

```powershell
# Navigate to MCP server directory
cd mcp-server

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\Activate.ps1

# On Mac/Linux:
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Create .env file from template
Copy-Item .env.example .env

# Edit .env with your configuration
notepad .env  # or use your preferred editor
```

#### Important .env Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/msil_mcp

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:5174"]

# API Gateway
APIM_BASE_URL=http://localhost:8001
MOCK_API_BASE_URL=http://localhost:8001

# Logging
LOG_LEVEL=DEBUG

# Environment
ENVIRONMENT=development
```

### Step 3: Set Up Admin UI

```powershell
# Navigate to admin-ui directory
cd admin-ui

# Install dependencies
npm install

# Create environment file (if needed)
# .env files are typically in vite projects at root
echo "VITE_API_URL=http://localhost:8000" > .env.local

# Verify installation
npm list  # Shows installed packages
```

### Step 4: Set Up Chat UI

```powershell
# Navigate to chat-ui directory
cd chat-ui

# Install dependencies
npm install

# Create environment file
echo "VITE_API_URL=http://localhost:8000" > .env.local
```

### Step 5: Set Up Database (Optional - for full local setup)

If you want to run PostgreSQL and Redis locally:

#### Option A: Using Docker Compose

```powershell
# From project root directory
docker-compose -f docker-compose.yml up -d

# Verify services are running
docker ps

# Check logs
docker-compose logs -f postgres    # PostgreSQL logs
docker-compose logs -f redis       # Redis logs
```

#### Option B: Manual Setup

```powershell
# PostgreSQL (requires separate installation)
# After installation, create database:
psql -U postgres
CREATE DATABASE msil_mcp;
\q

# Redis (requires separate installation)
# After installation, start Redis server
redis-server
```

---

## Project Structure

```
msil-mcp/
│
├── 📄 README.md                              # Project overview & quick start
├── 📄 ARCHITECTURE_AND_DATA_STORAGE.md       # Detailed architecture
├── 📄 overall_requirement_forchecking.txt    # RFP requirements mapping
├── 🔧 start-demo.ps1                        # Automated startup script
│
├── 📁 mcp-server/                           # FastAPI MCP Server (Python)
│   ├── 📄 requirements.txt                  # Python dependencies
│   ├── 📄 pytest.ini                        # Test configuration
│   ├── 🔧 Dockerfile                        # Container image
│   ├── 🔧 .env.example                      # Environment template
│   │
│   └── 📁 app/                              # Application code
│       ├── 📄 main.py                       # FastAPI entry point
│       ├── 📄 config.py                     # Configuration management
│       │
│       ├── 📁 api/                          # API endpoints
│       │   ├── tools.py                     # Tool registry endpoints
│       │   ├── auth.py                      # Authentication endpoints
│       │   ├── import.py                    # OpenAPI import endpoints
│       │   └── metrics.py                   # Metrics endpoints
│       │
│       ├── 📁 core/                         # Core business logic
│       │   ├── mcp_protocol.py              # MCP protocol handler
│       │   ├── tool_registry.py             # Tool management
│       │   ├── openapi_parser.py            # OpenAPI parsing
│       │   └── security.py                  # Security utilities
│       │
│       ├── 📁 db/                           # Database layer
│       │   ├── 📄 base.py                   # SQLAlchemy base
│       │   ├── 📄 session.py                # Session management
│       │   └── 📁 migrations/               # Alembic migrations
│       │
│       ├── 📁 models/                       # Database models
│       │   ├── user.py                      # User model
│       │   ├── tool.py                      # Tool model
│       │   ├── api_config.py                # API configuration model
│       │   └── audit_log.py                 # Audit log model
│       │
│       └── 📁 services/                     # Business services
│           ├── tool_service.py              # Tool operations
│           ├── auth_service.py              # Authentication service
│           ├── metrics_service.py           # Metrics aggregation
│           └── openapi_service.py           # OpenAPI import service
│
├── 📁 tests/                                # Test suite
│   ├── test_mcp_protocol.py
│   ├── test_tools.py
│   ├── test_auth.py
│   └── test_integration.py
│
├── 📁 admin-ui/                             # Admin Portal (React + TypeScript)
│   ├── 📄 package.json                      # Node dependencies
│   ├── 📄 tsconfig.json                     # TypeScript config
│   ├── 📄 vite.config.ts                    # Vite config
│   ├── 🔧 Dockerfile                        # Container image
│   ├── 🔧 nginx.conf                        # Production web server config
│   │
│   └── 📁 src/
│       ├── 📄 main.tsx                      # Entry point
│       ├── 📄 App.tsx                       # Root component
│       │
│       ├── 📁 components/                   # Reusable UI components
│       │   ├── ToolCard.tsx
│       │   ├── ImportForm.tsx
│       │   ├── MetricsChart.tsx
│       │   └── ...
│       │
│       ├── 📁 pages/                        # Page components
│       │   ├── Dashboard.tsx
│       │   ├── Tools.tsx
│       │   ├── Import.tsx
│       │   ├── Metrics.tsx
│       │   └── Settings.tsx
│       │
│       ├── 📁 contexts/                     # React contexts
│       │   └── AuthContext.tsx
│       │
│       ├── 📁 lib/                          # Utility functions
│       │   ├── api.ts                       # API client
│       │   └── utils.ts                     # Helper functions
│       │
│       └── 📁 styles/                       # Tailwind & CSS
│           └── globals.css
│
├── 📁 chat-ui/                              # Chat Interface (React + TypeScript)
│   ├── 📄 package.json                      # Node dependencies
│   ├── 📄 tsconfig.json                     # TypeScript config
│   ├── 📄 vite.config.ts                    # Vite config
│   ├── 🔧 Dockerfile                        # Container image
│   │
│   └── 📁 src/
│       ├── 📄 main.tsx                      # Entry point
│       ├── 📄 App.tsx                       # Root component
│       │
│       ├── 📁 components/                   # UI components
│       │   ├── ChatWindow.tsx
│       │   ├── ToolCard.tsx
│       │   └── MessageBubble.tsx
│       │
│       ├── 📁 lib/                          # Utilities
│       │   ├── api.ts                       # API client
│       │   └── websocket.ts                 # WebSocket handler
│       │
│       └── 📁 stores/                       # Zustand state stores
│           ├── chatStore.ts
│           └── uiStore.ts
│
├── 📁 mock-api/                             # Mock API for testing
│   ├── 📄 requirements.txt
│   └── 📁 app/                              # FastAPI mock server
│
├── 📁 sample-apis/                          # Sample OpenAPI specs
│   └── customer-service-api.yaml            # Customer service API spec
│
├── 📁 infrastructure/                       # Deployment configs
│   ├── 📁 aws/                              # AWS-specific configs
│   ├── 📁 kubernetes/                       # K8s manifests
│   ├── 📁 local/                            # Local dev configs
│   └── 📁 security/                         # Security configs
│
├── 📁 docs/                                 # Documentation (YOU ARE HERE)
│   ├── 📄 README.md                         # Docs index
│   ├── 📄 DEVELOPER_ONBOARDING.md           # This file
│   │
│   ├── 📁 architecture/
│   │   ├── 01-high-level-architecture.md
│   │   ├── 02-low-level-architecture.md
│   │   ├── 03-security-architecture.md
│   │   ├── 04-deployment-architecture.md
│   │   ├── 05-integration-architecture.md
│   │   └── README.md
│   │
│   ├── 📁 artefacts/
│   │   ├── 01-mcp-tool-definition.md
│   │   └── 02-composite-server.md
│   │
│   ├── 📁 devsecops/
│   │   └── README.md
│   │
│   ├── 📁 governance/
│   │   ├── 01-team-structure.md
│   │   ├── 02-templates.md
│   │   └── 03-product-selection.md
│   │
│   ├── 📁 infrastructure/
│   │   └── 01-bom.md
│   │
│   ├── 📁 observability/
│   │   └── README.md
│   │
│   ├── 📁 operations/
│   │   └── README.md
│   │
│   ├── 📁 security/
│   │   └── README.md
│   │
│   ├── 📁 security_implementation/
│   │   ├── P0_IMPLEMENTATION_COMPLETE.md
│   │   └── SECURITY_GAPS_IMPLEMENTATION_PLAN.md
│   │
│   └── 📁 Second_implementation/
│       ├── E2E_DEMO_GUIDE.md
│       ├── MCP_PROTOCOL_GUIDE.md
│       ├── PHASE2_SUMMARY.md
│       ├── PHASE6_STATUS.md
│       └── TESTING_GUIDE.md
│
└── 🐳 docker-compose.yml                    # Local development orchestration
```

### Directory Descriptions

| Directory | Purpose |
|-----------|---------|
| `mcp-server` | FastAPI backend server implementing MCP protocol |
| `admin-ui` | React admin portal for tool management & monitoring |
| `chat-ui` | React chat interface for AI-powered interactions |
| `mock-api` | Mock backend API for testing |
| `infrastructure` | Deployment configurations (Docker, K8s, AWS) |
| `docs` | Complete documentation suite |

---

## Running the Platform

### Quick Start: Automated Startup (Recommended)

```powershell
# From project root directory
.\start-demo.ps1
```

This script automatically:
1. ✅ Checks port availability
2. ✅ Starts MCP Server (port 8000)
3. ✅ Starts Admin UI (port 5174)
4. ✅ Starts Chat UI (port 5173)
5. ✅ Verifies all services are healthy
6. ✅ Displays access URLs

**Access Points**:
- **MCP Server**: http://localhost:8000
- **Swagger API Docs**: http://localhost:8000/docs
- **Admin Portal**: http://localhost:5174
- **Chat Interface**: http://localhost:5173

### Manual Startup

If you prefer to start services individually:

#### Terminal 1: MCP Server

```powershell
cd mcp-server

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start server
python -m uvicorn app.main:app --reload --port 8000

# Expected output:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete
```

#### Terminal 2: Admin UI

```powershell
cd admin-ui

# Start dev server
npm run dev

# Expected output:
# ➜  Local:   http://127.0.0.1:5174/
# ➜  press h to show help
```

#### Terminal 3: Chat UI

```powershell
cd chat-ui

# Start dev server
npm run dev

# Expected output:
# ➜  Local:   http://127.0.0.1:5173/
# ➜  press h to show help
```

### Verify Installation

```powershell
# Check MCP Server health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"2026-02-02T10:30:00Z"}

# Check Swagger documentation
Start-Process http://localhost:8000/docs

# Check Admin UI
Start-Process http://localhost:5174

# Check Chat UI
Start-Process http://localhost:5173
```

### Using Docker Compose (Full Stack)

```powershell
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Clean up volumes
docker-compose down -v
```

---

## Understanding Core Components

### 1. MCP Server (Backend)

**Location**: `mcp-server/`  
**Language**: Python 3.9+  
**Framework**: FastAPI  
**Port**: 8000

#### What it does:
- Implements the MCP protocol for tool discovery and execution
- Manages tool registry and OpenAPI spec parsing
- Handles authentication and authorization
- Tracks metrics and audit logs
- Enforces security policies

#### Key Modules:

**`main.py`** - FastAPI application setup
```python
# Initializes FastAPI app
# Sets up CORS, middleware, exception handlers
# Mounts API routers
```

**`api/`** - REST API endpoints
- `tools.py` - List, get, execute tools
- `auth.py` - Login, logout, token refresh
- `import.py` - Upload and parse OpenAPI specs
- `metrics.py` - Fetch execution metrics

**`core/`** - Business logic
- `mcp_protocol.py` - MCP handshake and message handling
- `tool_registry.py` - Tool CRUD operations
- `openapi_parser.py` - Converts OpenAPI specs to MCP tools
- `security.py` - JWT, RBAC, policy evaluation

**`models/`** - Database models
- `user.py` - User accounts and roles
- `tool.py` - Tool definitions and metadata
- `api_config.py` - API endpoint configurations
- `audit_log.py` - Activity audit trail

**`services/`** - Service layer
- `tool_service.py` - Tool operations
- `auth_service.py` - Authentication logic
- `metrics_service.py` - Metrics calculation
- `openapi_service.py` - OpenAPI import workflow

### 2. Admin UI (Frontend)

**Location**: `admin-ui/`  
**Language**: TypeScript + React  
**Framework**: Vite  
**Port**: 5174

#### What it does:
- Dashboard showing tool statistics and metrics
- Tool management (view, edit, delete)
- OpenAPI import interface (drag-drop upload)
- Real-time metrics visualization
- User and role management
- System settings and configuration

#### Key Pages:

| Page | Component | Purpose |
|------|-----------|---------|
| Dashboard | `pages/Dashboard.tsx` | Overview of tools, metrics, system health |
| Tools | `pages/Tools.tsx` | Browse and manage registered tools |
| Import | `pages/Import.tsx` | Upload OpenAPI specs and register tools |
| Metrics | `pages/Metrics.tsx` | View execution metrics and analytics |
| Settings | `pages/Settings.tsx` | Configure system settings |

#### Key Utilities:

**`lib/api.ts`** - API client
```typescript
// Handles HTTP requests to MCP Server
// Manages authentication tokens
// Error handling and retry logic
```

**`contexts/AuthContext.tsx`** - Authentication state
```typescript
// Manages user login state
// Token management
// Role-based access
```

### 3. Chat UI (Frontend)

**Location**: `chat-ui/`  
**Language**: TypeScript + React  
**Framework**: Vite  
**Port**: 5173

#### What it does:
- Natural language chat interface
- Tool execution through AI agent
- Message history and session management
- Real-time metrics display during execution
- Tool result visualization

#### Key Features:

**Chat Interaction Flow**:
1. User enters message in chat
2. Sent to MCP Server via API
3. Server determines relevant tools via LLM
4. Tools executed automatically
5. Results displayed in chat

**State Management** (`stores/`):
- `chatStore.ts` - Chat history, messages, sessions
- `uiStore.ts` - UI state, themes, modals

### 4. OpenAPI Parser

**Core Function**: Converts OpenAPI specifications to MCP tools

**Process**:
```
OpenAPI Spec (YAML/JSON)
    ↓
┌─────────────────────┐
│ OpenAPI Parser      │
│ (openapi_parser.py) │
└─────────────────────┘
    ↓
Parse endpoints, parameters, responses
    ↓
Generate MCP Tool definitions
    ↓
Store in Tool Registry
```

**Supported OpenAPI Versions**: 3.0.x, 3.1.x

**Example Transformation**:

```yaml
# OpenAPI Spec (Input)
paths:
  /customers:
    post:
      summary: Create a customer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                email:
                  type: string
      responses:
        '201':
          description: Customer created
```

```python
# MCP Tool (Output)
{
    "name": "create_customer",
    "description": "Create a customer",
    "inputSchema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string"}
        },
        "required": ["name", "email"]
    }
}
```

### 5. Tool Registry

**Purpose**: Central repository of all available tools

**Storage**: PostgreSQL database

**Fields**:
```python
class Tool:
    id: UUID
    name: str                      # Unique tool name
    display_name: str              # User-friendly name
    description: str               # What the tool does
    category: str                  # Business domain
    input_schema: Dict             # Parameter schema
    output_schema: Dict            # Response schema
    endpoint_url: str              # Backend API endpoint
    method: str                    # HTTP method (GET, POST, etc.)
    access_control: Dict           # RBAC rules
    is_active: bool                # Registration status
    created_at: DateTime
    updated_at: DateTime
    created_by: User
```

### 6. Security Architecture

**Defense-in-Depth Approach**:

```
┌─────────────────────────────────────┐
│ Layer 1: Authentication             │
│ (JWT tokens, OAuth2, OIDC)          │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ Layer 2: Authorization              │
│ (RBAC roles, OPA policies)          │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ Layer 3: Rate Limiting              │
│ (Per-user, per-tool quotas)         │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ Layer 4: Tool Execution             │
│ (Monitoring, audit logging)         │
└─────────────────────────────────────┘
```

**Key Security Features**:
- ✅ **JWT-based authentication** with token refresh
- ✅ **Role-Based Access Control (RBAC)** using OPA
- ✅ **Rate limiting** per user and per tool
- ✅ **PII masking** in logs and responses
- ✅ **Audit logging** of all operations
- ✅ **Step-up confirmation** for write operations
- ✅ **API rate limiting** and DDoS protection

---

## Development Workflow

### 1. Creating a New Feature

```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes to code

# 3. Run tests
cd mcp-server
pytest

# 4. Run linters
pylint app/
flake8 app/

# 5. Commit changes
git add .
git commit -m "feat: describe your feature"

# 6. Push and create PR
git push origin feature/your-feature-name
```

### 2. Adding a New Tool

#### Via UI:

1. Open Admin Portal (http://localhost:5174)
2. Click "Import OpenAPI"
3. Upload your OpenAPI spec
4. Configure tool parameters
5. Click "Register"

#### Programmatically:

```python
# In your code
from app.services.tool_service import ToolService

tool_service = ToolService()

tool = await tool_service.register_tool(
    name="get_customer",
    description="Retrieve customer details",
    input_schema={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string"}
        }
    },
    endpoint_url="https://api.example.com/customers/{id}",
    method="GET",
    category="customer-service"
)
```

### 3. Modifying Existing Tool

```python
from app.services.tool_service import ToolService

tool_service = ToolService()

updated_tool = await tool_service.update_tool(
    tool_id="tool-uuid",
    name="updated_name",
    description="Updated description",
    is_active=True
)
```

### 4. Adding Metrics

```python
from app.services.metrics_service import MetricsService

metrics_service = MetricsService()

await metrics_service.record_execution(
    tool_id="tool-uuid",
    user_id="user-uuid",
    status="success",
    duration_ms=250,
    input_params={"key": "value"},
    output_tokens=150
)
```

### 5. Testing Your Changes

```powershell
# Run all tests
pytest

# Run specific test file
pytest tests/test_tools.py

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_tools.py::test_create_tool

# Run in verbose mode
pytest -v
```

---

## Key Concepts

### MCP Protocol

**What is MCP?**
The Model Context Protocol is a standardized way for applications to:
1. **Discover** what tools/resources are available
2. **Call** tools with parameters
3. **Receive** results back

**MCP Workflow**:
```
1. Initialize Connection
   Client ──→ Server: Initialize handshake
   Client ←── Server: Confirm capabilities

2. List Tools
   Client ──→ Server: Request tool list
   Client ←── Server: Return available tools

3. Execute Tool
   Client ──→ Server: Call tool with parameters
   Client ←── Server: Execute and return results

4. Monitor Changes
   Client ←── Server: Notify when tools change
```

### Tool Registry

**Purpose**: Centralized catalog of all available API operations

**Key Concepts**:
- **Tool**: A single API operation (e.g., "create_customer")
- **Category**: Business domain grouping (e.g., "customer-service")
- **Active**: Tool is available for use
- **Inactive**: Tool is hidden/deprecated

**Lifecycle**:
```
Import OpenAPI Spec
        ↓
Parse endpoints
        ↓
Generate tools
        ↓
Review & customize
        ↓
Register (active)
        ↓
Available in MCP
```

### Authentication & Authorization

**Authentication Flow**:
```
User Login
    ↓
Verify credentials
    ↓
Generate JWT token
    ↓
Return token to client
    ↓
Client includes token in API requests
```

**Authorization Flow**:
```
Token received
    ↓
Extract user & roles
    ↓
Check OPA policies
    ↓
Compare against tool permissions
    ↓
Allow or deny access
```

### Metrics & Observability

**Tracked Metrics**:
- Total tools registered
- Tools by category
- Execution count per tool
- Success/failure rate
- Average execution time
- Tool execution timeline
- User activity

**Logging Levels**:
- `DEBUG` - Detailed development information
- `INFO` - General informational messages
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `CRITICAL` - Critical errors

### PII Protection

**Personally Identifiable Information (PII)** must be protected:

**Masked Fields**:
- Email addresses: `test****@example.com`
- Phone numbers: `+91 ****0123`
- Customer names: `John D.`

**Protection Mechanisms**:
- Automatic masking in logs
- PII not stored in audit trails
- Encrypted storage
- Restricted access

---

## Testing

### Test Structure

```
tests/
├── test_mcp_protocol.py      # MCP handshake, protocol
├── test_tools.py             # Tool registration, CRUD
├── test_auth.py              # Authentication, authorization
├── test_openapi_parser.py    # OpenAPI parsing
├── test_metrics.py           # Metrics recording
└── test_integration.py       # End-to-end flows
```

### Running Tests

```powershell
# All tests
pytest

# Specific file
pytest tests/test_tools.py

# Specific test function
pytest tests/test_tools.py::test_create_tool

# With coverage report
pytest --cov=app --cov-report=html tests/

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Show print statements
pytest -s
```

### Writing Tests

```python
import pytest
from app.services.tool_service import ToolService

@pytest.fixture
async def tool_service():
    return ToolService()

@pytest.mark.asyncio
async def test_create_tool(tool_service):
    # Arrange
    tool_data = {
        "name": "test_tool",
        "description": "Test tool",
        "endpoint_url": "http://example.com/api",
        "method": "GET"
    }
    
    # Act
    tool = await tool_service.register_tool(**tool_data)
    
    # Assert
    assert tool.name == "test_tool"
    assert tool.is_active == True
```

### CI/CD Testing

Tests run automatically on:
- **Pull Requests**: All tests must pass
- **Commits to main**: Full test suite + coverage check
- **Deployments**: Smoke tests on staging

---

## Security & Compliance

### Key Security Principles

1. **Principle of Least Privilege**: Users get minimum necessary permissions
2. **Defense in Depth**: Multiple security layers
3. **Audit Everything**: Complete activity logging
4. **Fail Securely**: Errors don't expose sensitive info
5. **Secure by Default**: Safe configurations pre-enabled

### Compliance Requirements

| Requirement | Implementation |
|------------|-----------------|
| **Authentication** | JWT + OAuth2/OIDC |
| **Authorization** | RBAC with OPA |
| **Encryption** | TLS 1.2+ in transit |
| **Audit Logging** | 12-month retention |
| **Data Protection** | PII masking |
| **Incident Response** | Documented procedures |

### OWASP Top 10 Mitigations

| Vulnerability | Mitigation |
|--------------|-----------|
| Injection | Parameterized queries, input validation |
| Broken Auth | JWT tokens, MFA-ready |
| Sensitive Data Exposure | Encryption, PII masking |
| XML External Entities | XML validation disabled |
| Broken Access Control | RBAC, OPA policies |
| Security Misconfiguration | Security checklist, hardened Docker |
| XSS | React escaping, CSP headers |
| Insecure Deserialization | Pydantic validation |
| Using Components with Known Vulns | Dependency scanning |
| Insufficient Logging | Comprehensive audit trail |

### Before Committing Code

```bash
# 1. Security scan
bandit -r app/

# 2. Dependency check
pip-audit

# 3. Linting
pylint app/
flake8 app/

# 4. Type checking
mypy app/

# 5. Tests
pytest

# 6. Code review
git push and create PR
```

---

## Troubleshooting

### Common Issues

#### Issue: `Connection refused: localhost:8000`

**Cause**: MCP Server not running

**Solution**:
```powershell
# Terminal 1: Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <PID> /F

# Start server again
cd mcp-server
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
```

#### Issue: `ModuleNotFoundError: No module named 'app'`

**Cause**: Virtual environment not activated or dependencies not installed

**Solution**:
```powershell
cd mcp-server

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Verify prompt shows (venv)
# Then reinstall dependencies
pip install -r requirements.txt
```

#### Issue: `PostgreSQL connection error`

**Cause**: Database not running or connection string incorrect

**Solution**:
```powershell
# Check if PostgreSQL is running
# Using Docker:
docker ps | findstr postgres

# Start with Docker Compose:
docker-compose up -d postgres

# Verify .env DATABASE_URL is correct
notepad mcp-server\.env

# Should be: postgresql://user:password@localhost:5432/msil_mcp
```

#### Issue: `CORS error in browser console`

**Cause**: Frontend and backend on different origins

**Solution**:
```python
# In mcp-server/.env, add frontend URLs:
CORS_ORIGINS=["http://localhost:5173","http://localhost:5174"]

# Restart server
```

#### Issue: `npm: command not found`

**Cause**: Node.js not installed

**Solution**:
```powershell
# Check Node.js version
node --version

# If not found, install from https://nodejs.org/
# Download LTS version for your OS

# After installation, verify
node --version  # Should show v18+
npm --version   # Should show npm 9+
```

### Debug Mode

```python
# In mcp-server/.env
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# This enables:
# - Detailed logging
# - Stack traces in responses
# - Hot reload on code changes
# - Debug endpoints
```

### Health Check Endpoints

```bash
# MCP Server health
curl http://localhost:8000/health

# MCP Server ready
curl http://localhost:8000/ready

# Tool registry status
curl http://localhost:8000/api/tools/health
```

### Checking Logs

```powershell
# MCP Server logs (from its terminal)
# Look for ERROR, WARNING messages

# Docker logs
docker-compose logs -f mcp-server
docker-compose logs -f admin-ui
docker-compose logs -f chat-ui

# Filter logs
docker-compose logs | findstr ERROR
```

---

## Useful Resources

### Documentation

| Resource | Link | Purpose |
|----------|------|---------|
| **Project README** | [README.md](../README.md) | Quick start guide |
| **Architecture** | [Architecture Docs](./architecture/) | System design |
| **API Reference** | [API Docs](./api/README.md) | Endpoint documentation |
| **E2E Demo Guide** | [E2E_DEMO_GUIDE.md](./Second_implementation/E2E_DEMO_GUIDE.md) | Complete workflow demo |
| **MCP Protocol Guide** | [MCP_PROTOCOL_GUIDE.md](./Second_implementation/MCP_PROTOCOL_GUIDE.md) | MCP details |
| **Testing Guide** | [TESTING_GUIDE.md](./Second_implementation/TESTING_GUIDE.md) | Test procedures |
| **Security** | [Security Architecture](./architecture/03-security-architecture.md) | Security details |
| **Operations** | [Operations Runbook](./operations/README.md) | Deployment & operations |

### External Resources

| Resource | URL | Description |
|----------|-----|-------------|
| **FastAPI** | https://fastapi.tiangolo.com/ | Python web framework |
| **React** | https://react.dev/ | UI library |
| **Model Context Protocol** | https://modelcontextprotocol.io/ | MCP specification |
| **OpenAPI Specification** | https://spec.openapis.org/ | API documentation standard |
| **Docker** | https://www.docker.com/ | Containerization |
| **PostgreSQL** | https://www.postgresql.org/ | Database |
| **Redis** | https://redis.io/ | Cache & message broker |

### Tools & IDEs

**Recommended Development Tools**:
- **VS Code** with extensions: Python, ES7+ React/Redux/React-Native snippets, Thunder Client
- **PyCharm Community** - Python IDE
- **Postman** - API testing
- **DBeaver** - Database management
- **Docker Desktop** - Container management

---

## Getting Help

### When You're Stuck

1. **Check Documentation First**
   - Search [ARCHITECTURE_AND_DATA_STORAGE.md](../ARCHITECTURE_AND_DATA_STORAGE.md)
   - Browse [docs/](../docs/) folder

2. **Search Existing Issues**
   - Check GitHub Issues for similar problems
   - Review closed PRs for solutions

3. **Check Logs**
   - Terminal output from services
   - Docker logs: `docker-compose logs -f`
   - Browser console (F12)

4. **Try Troubleshooting Section**
   - See [Troubleshooting](#troubleshooting) section above

5. **Ask the Team**
   - Slack channel: #msil-mcp-dev
   - Email: dev-team@nagarro.com
   - Monday sync-up meeting: 10 AM IST

### Contributing

1. **Found a bug?**
   - Open an issue with reproduction steps
   - Include error logs and environment info

2. **Want to add a feature?**
   - Check open issues first
   - Create an issue proposing your idea
   - Wait for feedback before coding

3. **Submitting PR?**
   - Create feature branch: `git checkout -b feature/name`
   - Write tests for new code
   - Follow code style (run linters)
   - Reference issue number: `Fixes #123`
   - Request review from 2+ team members

### Communication Channels

| Channel | Purpose |
|---------|---------|
| **Slack #msil-mcp-dev** | Daily development discussions |
| **Slack #msil-mcp-urgent** | Critical issues |
| **GitHub Issues** | Bug reports & feature requests |
| **GitHub Discussions** | Design decisions & questions |
| **Email** | dev-team@nagarro.com |
| **Weekly Standup** | Monday 10 AM IST |
| **Bi-weekly Architecture Review** | Thursday 2 PM IST |

---

## Next Steps

### Your First Day

- [ ] Complete environment setup (see [Environment Setup](#environment-setup))
- [ ] Run the platform locally (see [Running the Platform](#running-the-platform))
- [ ] Follow the E2E demo (see [E2E_DEMO_GUIDE.md](./Second_implementation/E2E_DEMO_GUIDE.md))
- [ ] Read the architecture overview (see [High-Level Architecture](./architecture/01-high-level-architecture.md))
- [ ] Connect with your team on Slack

### Your First Week

- [ ] Complete security training
- [ ] Review code style guide
- [ ] Set up code editor with project extensions
- [ ] Run all tests locally
- [ ] Make your first small contribution (e.g., docs update)
- [ ] Shadow a team member on code review

### Your First Month

- [ ] Implement a small feature
- [ ] Own a section of the codebase
- [ ] Lead a peer review
- [ ] Document your learnings
- [ ] Set up your development environment exactly as you like it

---

## Quick Reference

### Common Commands

```bash
# Start all services
.\start-demo.ps1

# Activate Python environment
.\mcp-server\venv\Scripts\Activate.ps1

# Start MCP Server
python -m uvicorn app.main:app --reload --port 8000

# Start Admin UI
npm run dev  # from admin-ui/

# Start Chat UI
npm run dev  # from chat-ui/

# Run tests
pytest

# Docker Compose
docker-compose up -d
docker-compose down
docker-compose logs -f
```

### Important URLs

```
MCP Server Swagger:    http://localhost:8000/docs
MCP Server OpenAPI:    http://localhost:8000/openapi.json
Admin Portal:          http://localhost:5174
Chat Interface:        http://localhost:5173
PostgreSQL:            localhost:5432 (if using Docker)
Redis:                 localhost:6379 (if using Docker)
```

### Key Files to Know

```
# Configuration
mcp-server/.env                    # Environment variables
admin-ui/package.json             # Frontend dependencies
chat-ui/package.json              # Chat UI dependencies

# Documentation
docs/README.md                     # Docs index
docs/architecture/                # Architecture docs
ARCHITECTURE_AND_DATA_STORAGE.md  # Detailed architecture

# Tests
tests/test_*.py                    # Test suite
pytest.ini                         # Test config

# Infrastructure
docker-compose.yml                 # Local orchestration
infrastructure/                    # Production configs
```

---

## Document Metadata

- **Version**: 1.0
- **Last Updated**: February 2, 2026
- **Created By**: Nagarro Development Team
- **Status**: Published
- **Review Schedule**: Quarterly
- **Next Review**: May 2, 2026

---

**Welcome to the team! 🚀 Happy coding!**

For questions, reach out to the team on Slack or email dev-team@nagarro.com
