# MSIL Composite MCP Server - Requirements Specification Document

**Document Version:** 1.0  
**Date:** January 30, 2026  
**Prepared By:** Nagarro Development Team  
**Client:** Maruti Suzuki India Limited (MSIL)  
**Project:** Composite MCP Server Platform  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Overview](#2-project-overview)
3. [System Architecture Overview](#3-system-architecture-overview)
4. [Functional Requirements](#4-functional-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [User Interface Requirements](#6-user-interface-requirements)
7. [API & Integration Requirements](#7-api--integration-requirements)
8. [Security Requirements](#8-security-requirements)
9. [Deployment & Configuration Requirements](#9-deployment--configuration-requirements)
10. [Observability & Audit Requirements](#10-observability--audit-requirements)
11. [Demo Requirements (Stage-2)](#11-demo-requirements-stage-2)
12. [Technology Stack](#12-technology-stack)
13. [Development Phases](#13-development-phases)
14. [Glossary](#14-glossary)
15. [Environment Summary](#15-environment-summary)
16. [Success Criteria](#16-success-criteria)

---

## 1. Executive Summary

### 1.1 Purpose

This document defines the complete requirements specification for building a **Composite MCP (Model Context Protocol) Server Platform** for Maruti Suzuki India Limited. The platform will transform 309+ APIs into 30+ MCP Products using OpenAPI-driven tool generation with zero static coding approach.

### 1.2 Scope

| Aspect | Description |
|--------|-------------|
| **In Scope** | MCP Server, Chat Interface, Admin Interface, Mock API Framework, AWS Deployment Infrastructure |
| **Out of Scope** | LLM Training, RAG Implementation, Actual MSIL Backend Systems |

### 1.3 Key Objectives

1. **Local Development First**: Fully functional local environment with mock APIs
2. **Cloud-Ready**: Seamless transition to AWS deployment
3. **Enterprise-Grade UI**: Professional interfaces worthy of MSIL brand
4. **Zero Static Coding**: OpenAPI-driven dynamic tool generation
5. **Production-Ready Security**: OAuth2/OIDC, RBAC, PIM/PAM compliance

---

## 2. Project Overview

### 2.1 Business Context

MSIL requires a Composite MCP Server that enables AI agents to interact with their API ecosystem through standardized MCP protocol. The server must:

- Convert existing APIs into MCP-compatible tools automatically
- Provide centralized governance and discovery
- Support multiple AI clients (chat interfaces, agents)
- Maintain enterprise-grade security and audit capabilities

### 2.2 Target Users

| User Role | Description | Primary Interface |
|-----------|-------------|-------------------|
| **End Users** | MSIL customers/employees using AI chat | Chat Interface |
| **Administrators** | Platform administrators managing tools/policies | Admin Interface |
| **Developers** | API developers registering new tools | Admin Interface + CLI |
| **Auditors** | Security/compliance reviewers | Admin Interface (Audit Dashboard) |

### 2.3 Deployment Modes

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        DEPLOYMENT CONFIGURATIONS                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  MODE 1: LOCAL DEVELOPMENT (Developer Machine + Rancher Desktop)             │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                    NATIVE PROCESSES (localhost)                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐    │   │
│  │  │  Chat UI    │  │  Admin UI   │  │ MCP Server  │  │ Mock API  │    │   │
│  │  │  React Dev  │  │  React Dev  │  │  FastAPI    │  │  FastAPI  │    │   │
│  │  │  :3000      │  │  :3001      │  │  :8000      │  │  :8080    │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘    │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                      │                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │              DOCKER CONTAINERS (Rancher Desktop)                       │   │
│  │  ┌─────────────────────────┐  ┌─────────────────────────────────┐    │   │
│  │  │      PostgreSQL 15      │  │           Redis 7               │    │   │
│  │  │         :5432           │  │            :6379                │    │   │
│  │  └─────────────────────────┘  └─────────────────────────────────┘    │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  MODE 2: AWS MVP (Nagarro AWS Environment)                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                         AWS INFRASTRUCTURE                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │   │
│  │  │  Chat UI    │  │  Admin UI   │  │ MCP Server  │                   │   │
│  │  │ CloudFront  │  │ CloudFront  │  │ ECS Fargate │                   │   │
│  │  │  + S3       │  │  + S3       │  │  + ALB      │                   │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                   │   │
│  │         └────────────────┼────────────────┘                           │   │
│  │                          │                                             │   │
│  │  ┌───────────────────────┼───────────────────────┐                   │   │
│  │  │         ┌─────────────┴──────────────┐        │                   │   │
│  │  │         │     RDS PostgreSQL         │        │                   │   │
│  │  │         │     ElastiCache Redis      │        │                   │   │
│  │  │         └────────────────────────────┘        │                   │   │
│  │  └───────────────────────────────────────────────┘                   │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                      │                                        │
│                                      ▼                                        │
│                        ┌─────────────────────────┐                           │
│                        │    MSIL Dev APIM        │                           │
│                        │   (Actual APIs)         │                           │
│                        │   ───────────────────   │                           │
│                        │   DB Entries Validated  │                           │
│                        │   by MSIL Team          │                           │
│                        └─────────────────────────┘                           │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. System Architecture Overview

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MSIL COMPOSITE MCP PLATFORM                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         PRESENTATION LAYER                            │   │
│  │  ┌─────────────────────────┐    ┌─────────────────────────────────┐  │   │
│  │  │      CHAT INTERFACE     │    │       ADMIN INTERFACE           │  │   │
│  │  │  • AI Conversation UI   │    │  • Tool Management Dashboard    │  │   │
│  │  │  • Service Booking Flow │    │  • Policy Configuration         │  │   │
│  │  │  • Multi-turn Dialog    │    │  • User/Role Management         │  │   │
│  │  │  • MSIL Branded Theme   │    │  • Audit Logs Viewer            │  │   │
│  │  │  • Responsive Design    │    │  • Analytics Dashboard          │  │   │
│  │  └─────────────────────────┘    └─────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         MCP SERVER CORE                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │  Composite  │  │    Tool     │  │   Policy    │  │  Execution  │  │   │
│  │  │   Gateway   │  │  Registry   │  │   Engine    │  │   Engine    │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │  OpenAPI    │  │   Schema    │  │   Cache     │  │ Observabil- │  │   │
│  │  │  Generator  │  │  Validator  │  │   Manager   │  │    ity      │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        INTEGRATION LAYER                              │   │
│  │  ┌─────────────────────────┐    ┌─────────────────────────────────┐  │   │
│  │  │     API CONNECTOR       │    │       LLM CONNECTOR             │  │   │
│  │  │  • Mock API Adapter     │    │  • OpenAI Compatible            │  │   │
│  │  │  • AWS APIM Adapter     │    │  • Azure OpenAI                 │  │   │
│  │  │  • Circuit Breaker      │    │  • AWS Bedrock                  │  │   │
│  │  │  • Retry Logic          │    │  • Configurable Provider        │  │   │
│  │  └─────────────────────────┘    └─────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Core Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Composite MCP Gateway** | Single entry point, AuthN/AuthZ, routing | Python/FastAPI |
| **Tool Registry** | Central tool discovery, versioning, lifecycle | PostgreSQL + Redis |
| **Tool Generator** | OpenAPI → MCP Tool conversion | Python |
| **Policy Engine** | RBAC, allow/deny lists, guardrails | OPA (Open Policy Agent) |
| **Execution Engine** | Tool invocation, APIM calls | Python/asyncio |
| **Cache Manager** | Response caching, rate limiting | Redis |
| **Observability Stack** | Logs, metrics, traces, audit | OpenTelemetry + AWS CloudWatch |

---

## 4. Functional Requirements

### 4.1 MCP Server Core (FR-MCP)

#### FR-MCP-001: MCP Protocol Implementation
- **Description**: Implement full MCP protocol specification for tool discovery and execution
- **Priority**: P0 (Critical)
- **Acceptance Criteria**:
  - Support `tools/list` for tool discovery
  - Support `tools/call` for tool execution
  - Support `resources/list` for resource discovery
  - Support SSE (Server-Sent Events) for streaming responses
  - Maintain MCP protocol version compatibility

#### FR-MCP-002: Composite Gateway
- **Description**: Single MCP endpoint routing to multiple tool bundles
- **Priority**: P0 (Critical)
- **Acceptance Criteria**:
  - Single endpoint URL for all MCP operations
  - Route tool calls to appropriate tool bundles
  - Support tool bundle isolation and namespacing
  - Handle concurrent requests efficiently

#### FR-MCP-003: OpenAPI-Driven Tool Generation
- **Description**: Automatically generate MCP tools from OpenAPI/Swagger specifications
- **Priority**: P0 (Critical)
- **Acceptance Criteria**:
  - Parse OpenAPI 3.0/3.1 specifications
  - Generate tool name, description from operation metadata
  - Generate input JSON schema from parameters + requestBody
  - Generate output schema from response definitions
  - Support automatic regeneration on OpenAPI changes
  - Zero manual coding for tool definitions

#### FR-MCP-004: Tool Registry Management
- **Description**: Central registry for tool discovery and lifecycle
- **Priority**: P0 (Critical)
- **Acceptance Criteria**:
  - Register tools with metadata (name, version, domain, owner)
  - Support tool versioning (tied to OpenAPI version)
  - Provide tool search and filtering APIs
  - Support tool enable/disable without deletion
  - Maintain tool dependency mappings

#### FR-MCP-005: Tool Bundle (MCP Product) Management
- **Description**: Group tools into logical business domains
- **Priority**: P1 (High)
- **Acceptance Criteria**:
  - Create tool bundles representing business journeys
  - Map multiple tools to a single bundle
  - Configure bundle-level policies
  - Support bundle versioning and lifecycle

#### FR-MCP-006: Schema Validation
- **Description**: Strict JSON schema validation for all tool inputs/outputs
- **Priority**: P0 (Critical)
- **Acceptance Criteria**:
  - Validate all tool call inputs against generated schemas
  - Reject requests with additional properties when not allowed
  - Validate enum values strictly
  - Enforce payload size limits
  - Validate response schemas from backends

#### FR-MCP-007: Response Shaping
- **Description**: Transform and compact API responses for token efficiency
- **Priority**: P1 (High)
- **Acceptance Criteria**:
  - Support field selection (include/exclude)
  - Flatten nested structures where appropriate
  - Remove null/empty fields optionally
  - Enforce maximum response size limits

### 4.2 Chat Interface (FR-CHAT)

#### FR-CHAT-001: Conversational AI Interface
- **Description**: Professional chat interface for end-user interactions
- **Priority**: P0 (Critical)
- **Acceptance Criteria**:
  - Multi-turn conversation support
  - Message history persistence
  - Typing indicators and loading states
  - Error handling with user-friendly messages
  - Conversation context management

#### FR-CHAT-002: LLM Integration
- **Description**: Configurable LLM backend integration
- **Priority**: P0 (Critical)
- **Acceptance Criteria**:
  - Support OpenAI API compatible endpoints
  - Support Azure OpenAI
  - Support AWS Bedrock (Claude, Titan)
  - Configurable model selection
  - API key/credential management

#### FR-CHAT-003: Tool Execution Visualization
- **Description**: Show tool execution progress to users
- **Priority**: P1 (High)
- **Acceptance Criteria**:
  - Display which tools are being called
  - Show tool execution status (pending/success/error)
  - Display execution time for each tool
  - Option to expand/collapse tool details

#### FR-CHAT-004: Service Booking Flow
- **Description**: Specialized UI for service booking journey
- **Priority**: P0 (Critical for Demo)
- **Acceptance Criteria**:
  - Guide users through booking process
  - Display dealer selection with map view
  - Show available time slots
  - Booking confirmation with details
  - Support dynamic input collection

#### FR-CHAT-005: Conversation Export
- **Description**: Export conversation history
- **Priority**: P2 (Medium)
- **Acceptance Criteria**:
  - Export to PDF format
  - Export to JSON format
  - Include tool execution details optionally

### 4.3 Admin Interface (FR-ADMIN)

#### FR-ADMIN-001: Dashboard Overview
- **Description**: Central dashboard showing platform health and metrics
- **Priority**: P0 (Critical)
- **Acceptance Criteria**:
  - Real-time tool invocation counts
  - Error rate visualization
  - Latency percentiles (p50, p95, p99)
  - Active user sessions count
  - System health indicators

#### FR-ADMIN-002: Tool Management
- **Description**: CRUD operations for tool bundles and tools
- **Priority**: P0 (Critical)
- **Acceptance Criteria**:
  - List all registered tools with status
  - View tool details and schemas
  - Enable/disable tools
  - View tool invocation history
  - Trigger tool regeneration from OpenAPI

#### FR-ADMIN-003: OpenAPI Specification Management
- **Description**: Upload and manage OpenAPI specifications
- **Priority**: P0 (Critical)
- **Acceptance Criteria**:
  - Upload OpenAPI files (YAML/JSON)
  - Validate OpenAPI syntax
  - Preview generated tools before publishing
  - Version history of specifications
  - Rollback to previous versions

#### FR-ADMIN-004: Policy Configuration
- **Description**: Configure security and access policies
- **Priority**: P0 (Critical)
- **Acceptance Criteria**:
  - Define allow/deny lists per tool
  - Configure role-based tool access
  - Set rate limits per tool/user/role
  - Configure input validation rules
  - Define response filtering rules

#### FR-ADMIN-005: User & Role Management
- **Description**: Manage platform users and their roles
- **Priority**: P1 (High)
- **Acceptance Criteria**:
  - Create/update/delete users
  - Define roles and permissions
  - Assign roles to users
  - Configure PIM/PAM policies
  - View user activity history

#### FR-ADMIN-006: Audit Log Viewer
- **Description**: View and search audit logs
- **Priority**: P0 (Critical)
- **Acceptance Criteria**:
  - Search logs by date range
  - Filter by tool, user, status
  - View detailed log entries
  - Export logs to CSV/JSON
  - Highlight policy violations

#### FR-ADMIN-007: Configuration Management
- **Description**: Manage platform configuration
- **Priority**: P1 (High)
- **Acceptance Criteria**:
  - Configure API endpoint URLs
  - Manage environment variables
  - Configure LLM settings
  - Set cache TTL values
  - Configure observability settings

#### FR-ADMIN-008: Mock API Management
- **Description**: Configure mock APIs for development/testing
- **Priority**: P1 (High for Demo)
- **Acceptance Criteria**:
  - Define mock response templates
  - Configure mock response delays
  - Set up mock error scenarios
  - Toggle between mock and real APIs

### 4.4 Mock API Framework (FR-MOCK)

#### FR-MOCK-001: Service Booking Mock APIs
- **Description**: Complete mock implementation of service booking APIs
- **Priority**: P0 (Critical for Demo)
- **Acceptance Criteria**:
  - Mock customer resolution API
  - Mock vehicle resolution API
  - Mock dealer search API
  - Mock slot availability API
  - Mock booking creation API
  - Mock booking status API

#### FR-MOCK-002: Dynamic Mock Responses
- **Description**: Generate realistic mock data
- **Priority**: P1 (High)
- **Acceptance Criteria**:
  - Generate realistic customer data
  - Generate realistic vehicle data
  - Generate location-aware dealer data
  - Generate time-sensitive slot data
  - Support configurable response delays

#### FR-MOCK-003: Mock Data Persistence
- **Description**: Persist mock data for demo consistency
- **Priority**: P1 (High)
- **Acceptance Criteria**:
  - Store created bookings in mock database
  - Support booking lookup for verification
  - Reset mock data on demand
  - Seed mock data from files

---

## 5. Non-Functional Requirements

### 5.1 Performance (NFR-PERF)

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| NFR-PERF-001 | Tool Discovery Latency | < 100ms p95 | API response time |
| NFR-PERF-002 | Tool Execution Latency | < 500ms p95 (excluding backend) | API response time |
| NFR-PERF-003 | Chat Response Time | < 3s for complete response | End-to-end time |
| NFR-PERF-004 | Concurrent Users | 100+ simultaneous sessions | Load testing |
| NFR-PERF-005 | Tool Registry Load | < 50ms for 1000 tools | Query time |

### 5.2 Scalability (NFR-SCALE)

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-SCALE-001 | Horizontal Scaling | Support auto-scaling 1-10 instances |
| NFR-SCALE-002 | Tool Capacity | Support 500+ tools |
| NFR-SCALE-003 | Request Throughput | 1000 requests/second |

### 5.3 Availability (NFR-AVAIL)

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-AVAIL-001 | Uptime SLA | 99.9% (production) |
| NFR-AVAIL-002 | RTO | < 1 hour |
| NFR-AVAIL-003 | RPO | < 15 minutes |

### 5.4 Maintainability (NFR-MAINT)

| ID | Requirement | Description |
|----|-------------|-------------|
| NFR-MAINT-001 | Code Quality | 80%+ test coverage |
| NFR-MAINT-002 | Documentation | API docs, deployment guides, runbooks |
| NFR-MAINT-003 | Logging | Structured JSON logs with correlation IDs |

---

## 6. User Interface Requirements

### 6.1 Design Principles

#### 6.1.1 Brand Identity
- **Primary Brand**: Maruti Suzuki India Limited
- **Color Palette**:
  - Primary: MSIL Blue (#003D79)
  - Secondary: MSIL Red (#E31837)
  - Accent: Silver (#C0C0C0)
  - Background: Clean White (#FFFFFF)
  - Text: Dark Grey (#333333)
- **Logo**: MSIL logo prominently displayed
- **Typography**: Professional sans-serif (Inter/Roboto)

#### 6.1.2 Design Standards
- Enterprise-grade professional appearance
- Clean, modern, minimalist design
- Consistent spacing and alignment
- Accessible (WCAG 2.1 AA compliant)
- Responsive (desktop, tablet, mobile)

### 6.2 Chat Interface UI Requirements

#### UI-CHAT-001: Layout Structure
```
┌─────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  [MSIL LOGO]    AI Service Assistant    [User Menu] [Settings] │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                              │   │
│  │                    CONVERSATION AREA                         │   │
│  │                                                              │   │
│  │  ┌────────────────────────────────────────────┐             │   │
│  │  │ 🤖 Welcome! How can I help you today?      │             │   │
│  │  └────────────────────────────────────────────┘             │   │
│  │                                                              │   │
│  │              ┌────────────────────────────────────────────┐ │   │
│  │              │ 👤 I'd like to book a service appointment  │ │   │
│  │              └────────────────────────────────────────────┘ │   │
│  │                                                              │   │
│  │  ┌────────────────────────────────────────────┐             │   │
│  │  │ 🤖 I'll help you book a service. Let me   │             │   │
│  │  │    find available slots...                 │             │   │
│  │  │                                            │             │   │
│  │  │  ⚙️ Executing: GetNearbyDealers ✓         │             │   │
│  │  │  ⚙️ Executing: GetSlots ⏳                 │             │   │
│  │  └────────────────────────────────────────────┘             │   │
│  │                                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  [📎] Type your message...                         [Send ➤] │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Quick Actions: [Book Service] [Check Status] [Find Dealer] │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### UI-CHAT-002: Message Components
- **User Messages**: Right-aligned, accent color background
- **AI Messages**: Left-aligned, light grey background
- **Tool Execution Cards**: Expandable cards showing tool progress
- **Booking Confirmation**: Rich card with all booking details
- **Dealer Cards**: Card view with dealer info, ratings, distance

#### UI-CHAT-003: Interactive Elements
- Typing indicator with animated dots
- Message timestamps
- Copy message button
- Feedback buttons (thumbs up/down)
- Quick action buttons

### 6.3 Admin Interface UI Requirements

#### UI-ADMIN-001: Navigation Structure
```
┌─────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  [MSIL LOGO]    MCP Admin Console           [Admin] [Logout] │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌────────┬────────────────────────────────────────────────────┐   │
│  │        │                                                     │   │
│  │  NAV   │                   MAIN CONTENT                      │   │
│  │        │                                                     │   │
│  │ ┌────┐ │  ┌─────────────────────────────────────────────┐   │   │
│  │ │ 📊 │ │  │              DASHBOARD VIEW                  │   │   │
│  │ │Dash│ │  │                                              │   │   │
│  │ └────┘ │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │   │
│  │ ┌────┐ │  │  │ API Calls│ │ Error %  │ │ Latency  │    │   │   │
│  │ │ 🔧 │ │  │  │  12,450  │ │   0.5%   │ │  120ms   │    │   │   │
│  │ │Tool│ │  │  └──────────┘ └──────────┘ └──────────┘    │   │   │
│  │ └────┘ │  │                                              │   │   │
│  │ ┌────┐ │  │  ┌────────────────────────────────────────┐ │   │   │
│  │ │ 📋 │ │  │  │         INVOCATION CHART               │ │   │   │
│  │ │APIs│ │  │  │         ████████████                   │ │   │   │
│  │ └────┘ │  │  │         ████████                       │ │   │   │
│  │ ┌────┐ │  │  │         ██████████████                 │ │   │   │
│  │ │ 🔐 │ │  │  └────────────────────────────────────────┘ │   │   │
│  │ │Poli│ │  │                                              │   │   │
│  │ └────┘ │  └─────────────────────────────────────────────┘   │   │
│  │ ┌────┐ │                                                     │   │
│  │ │ 📜 │ │                                                     │   │
│  │ │Logs│ │                                                     │   │
│  │ └────┘ │                                                     │   │
│  │ ┌────┐ │                                                     │   │
│  │ │ ⚙️ │ │                                                     │   │
│  │ │Conf│ │                                                     │   │
│  │ └────┘ │                                                     │   │
│  └────────┴────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

#### UI-ADMIN-002: Dashboard Widgets
- **KPI Cards**: Total calls, success rate, avg latency, active tools
- **Time Series Charts**: Invocations over time (line/area chart)
- **Tool Breakdown**: Bar chart of top tools by usage
- **Error Distribution**: Pie chart of error types
- **Recent Activity**: Live feed of recent tool calls

#### UI-ADMIN-003: Tool Management Views
- **Tool List**: Sortable, filterable data table
- **Tool Detail**: Side panel with full tool information
- **Schema Viewer**: Syntax-highlighted JSON schema display
- **Version History**: Timeline of tool versions

#### UI-ADMIN-004: Audit Log Views
- **Log Table**: Paginated, searchable log entries
- **Log Detail**: Modal with full log payload
- **Export Options**: CSV, JSON download buttons
- **Filters**: Date picker, status dropdown, tool selector

### 6.4 UI Component Library

| Component | Description | Usage |
|-----------|-------------|-------|
| **Button** | Primary, Secondary, Danger variants | Actions, Submit |
| **Input** | Text, Number, Date, Select | Forms |
| **Card** | Content container with shadow | Dashboard widgets |
| **Table** | Sortable, paginated data table | Lists |
| **Modal** | Overlay dialog | Confirmations, Details |
| **Toast** | Notification popup | Feedback |
| **Badge** | Status indicator | Tool status |
| **Tabs** | Content organization | Navigation |
| **Tooltip** | Hover information | Help text |
| **Skeleton** | Loading placeholder | Loading states |

---

## 7. API & Integration Requirements

### 7.1 MCP Server API Endpoints

#### 7.1.1 MCP Protocol Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/mcp/tools/list` | List available tools |
| POST | `/mcp/tools/call` | Execute a tool |
| POST | `/mcp/resources/list` | List available resources |
| GET | `/mcp/sse` | SSE endpoint for streaming |

#### 7.1.2 Admin API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/tools` | List all tools |
| GET | `/api/admin/tools/{id}` | Get tool details |
| PUT | `/api/admin/tools/{id}` | Update tool |
| POST | `/api/admin/openapi` | Upload OpenAPI spec |
| GET | `/api/admin/policies` | List policies |
| PUT | `/api/admin/policies/{id}` | Update policy |
| GET | `/api/admin/audit-logs` | Query audit logs |
| GET | `/api/admin/metrics` | Get metrics |

### 7.2 External Integrations

#### 7.2.1 LLM Integration

```yaml
llm_providers:
  openai:
    type: openai_compatible
    base_url: https://api.openai.com/v1
    models: [gpt-4, gpt-4-turbo, gpt-3.5-turbo]
    
  azure_openai:
    type: azure
    endpoint: https://{resource}.openai.azure.com
    api_version: 2024-02-15-preview
    
  aws_bedrock:
    type: bedrock
    region: us-east-1
    models: [anthropic.claude-3, amazon.titan-text]
```

#### 7.2.2 API Gateway Integration

```yaml
api_gateway:
  # Mode determines which backend to use
  # - 'mock': Local mock API server for development
  # - 'msil_apim': MSIL Dev APIM for MVP/Production
  mode: ${API_GATEWAY_MODE:mock}
  
  mock:
    base_url: http://localhost:8080
    description: "Local mock API for development and testing"
    
  msil_apim:
    base_url: ${MSIL_APIM_BASE_URL:https://dev-api.msil.example.com}
    auth:
      type: oauth2
      token_url: ${MSIL_AUTH_TOKEN_URL}
      client_id: ${MSIL_APIM_CLIENT_ID}
      client_secret: ${MSIL_APIM_CLIENT_SECRET}
      scope: ${MSIL_APIM_SCOPE:api.read api.write}
    
    # MSIL APIM specific headers
    headers:
      x-api-key: ${MSIL_API_KEY}
      x-correlation-id: "auto-generated"
    
    # Timeout and retry configuration
    timeout_seconds: 30
    retry_count: 3
    circuit_breaker:
      failure_threshold: 5
      recovery_timeout: 60
```

#### 7.2.3 MSIL Dev APIM Integration (MVP)

> **Purpose**: For AWS MVP deployment, the MCP Server connects to MSIL's Dev APIM to execute real API calls. MSIL validates the integration by checking database entries created through these calls.

**Connection Flow:**
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   MCP Server    │────▶│  MSIL Dev APIM  │────▶│  MSIL Backend   │
│  (Nagarro AWS)  │     │                 │     │   Databases     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │ MSIL Validates  │
                                               │ DB Entries      │
                                               └─────────────────┘
```

**Required MSIL APIM Credentials (to be provided by MSIL):**
- OAuth2 Client ID & Secret
- API Key (if required)
- Token endpoint URL
- Allowed scopes
- Whitelisted IP ranges (Nagarro AWS NAT Gateway IPs)

### 7.3 Service Booking APIs (Mock Implementation)

| API | Method | Path | Description |
|-----|--------|------|-------------|
| ResolveCustomer | POST | `/api/customer/resolve` | Get customer by mobile |
| ResolveVehicle | POST | `/api/vehicle/resolve` | Get vehicle by registration |
| GetNearbyDealers | POST | `/api/dealers/nearby` | Find dealers by location |
| GetSlots | POST | `/api/slots/available` | Get available time slots |
| CreateServiceBooking | POST | `/api/booking/create` | Create new booking |
| GetBookingStatus | GET | `/api/booking/{id}` | Get booking details |

---

## 8. Security Requirements

### 8.1 Authentication & Authorization

#### SEC-001: OAuth2/OIDC Authentication
- Support OAuth2 authorization code flow
- Support client credentials flow for service accounts
- JWT token validation
- Token refresh handling
- Configurable identity providers

#### SEC-002: Role-Based Access Control (RBAC)
```yaml
roles:
  admin:
    - tools:read
    - tools:write
    - policies:read
    - policies:write
    - audit:read
    - users:manage
    
  developer:
    - tools:read
    - tools:write
    - policies:read
    
  operator:
    - tools:read
    - audit:read
    - metrics:read
    
  user:
    - tools:execute
```

#### SEC-003: Tool-Level Authorization
- Configure tool visibility per role
- Separate "discover" and "invoke" permissions
- Allow/deny lists per tool

### 8.2 Input Validation & Injection Prevention

#### SEC-004: Request Validation
- Strict JSON schema validation
- Reject additional properties
- Validate enum values
- Enforce payload size limits (max 1MB)
- Sanitize string inputs

#### SEC-005: Prompt Injection Prevention
- Validate tool names against registry
- Reject natural language in tool parameters
- Log suspicious patterns
- Rate limit by user

### 8.3 Secrets Management

#### SEC-006: Secrets Isolation
- Store secrets in AWS Secrets Manager (prod) or local vault (dev)
- Never log secrets
- Never return secrets to clients
- Rotate secrets periodically

### 8.4 PII Handling

#### SEC-007: PII Protection
- Mask PII in logs (phone numbers, emails)
- Redact sensitive fields in audit logs
- Minimal data retention
- Configurable redaction rules

### 8.5 Rate Limiting

#### SEC-008: Rate Limits
| Scope | Limit |
|-------|-------|
| Per User | 100 requests/minute |
| Per Tool | 1000 requests/minute |
| Global | 10000 requests/minute |

---

## 9. Deployment & Configuration Requirements

### 9.1 Local Development Environment

> **Development Philosophy**: Run application code (frontend, backend) natively for hot-reload and fast debugging. Use Docker containers (via Rancher Desktop) only for infrastructure dependencies (database, cache).

#### DEP-LOCAL-001: Infrastructure Containers (Rancher Desktop)

**docker-compose.infra.yml** - Infrastructure services only:
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    container_name: msil-mcp-postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: mcp_user
      POSTGRES_PASSWORD: mcp_local_password
      POSTGRES_DB: mcp_server
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mcp_user -d mcp_server"]
      interval: 10s
      timeout: 5s
      retries: 5
    
  redis:
    image: redis:7-alpine
    container_name: msil-mcp-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

#### DEP-LOCAL-002: Native Application Development

**Backend (MCP Server + Mock API):**
```powershell
# Terminal 1: MCP Server
cd mcp-server
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2: Mock API Server
cd mock-api
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

**Frontend (Chat UI + Admin UI):**
```powershell
# Terminal 3: Chat UI
cd chat-ui
npm install
npm run dev  # Runs on http://localhost:3000

# Terminal 4: Admin UI
cd admin-ui
npm install
npm run dev  # Runs on http://localhost:3001
```

#### DEP-LOCAL-003: Local Environment Variables

**.env.local** (root level):
```env
# Environment
ENVIRONMENT=development

# Database (Docker container via Rancher Desktop)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mcp_server
DB_USER=mcp_user
DB_PASSWORD=mcp_local_password

# Redis (Docker container via Rancher Desktop)
REDIS_HOST=localhost
REDIS_PORT=6379

# API Gateway Mode
API_GATEWAY_MODE=mock
MOCK_API_URL=http://localhost:8080

# LLM Configuration (for local testing)
LLM_PROVIDER=openai
LLM_API_KEY=your-openai-api-key
LLM_MODEL=gpt-4

# Server URLs
MCP_SERVER_URL=http://localhost:8000
CHAT_UI_URL=http://localhost:3000
ADMIN_UI_URL=http://localhost:3001
```

#### DEP-LOCAL-004: Quick Start Commands

```powershell
# Step 1: Start infrastructure containers (run once, persists data)
cd infrastructure/local
docker-compose -f docker-compose.infra.yml up -d

# Step 2: Verify containers are running
docker ps

# Step 3: Initialize database (first time only)
cd mcp-server
python scripts/init_db.py

# Step 4: Start all application services (use separate terminals)
# See DEP-LOCAL-002 for individual commands

# To stop infrastructure
docker-compose -f docker-compose.infra.yml down

# To reset all data
docker-compose -f docker-compose.infra.yml down -v
```

### 9.2 AWS MVP Environment (Nagarro AWS)

> **MVP Goal**: Minimum viable deployment to demonstrate functional MCP Server connecting to MSIL Dev APIM. MSIL will validate success by checking database entries created through MCP tool executions.

#### DEP-AWS-001: MVP Infrastructure Components

| Component | AWS Service | Purpose |
|-----------|-------------|---------|
| Compute | ECS Fargate | Container orchestration (simpler than EKS for MVP) |
| Load Balancer | ALB | HTTP/HTTPS ingress |
| WAF | AWS WAF | Web application firewall (optional for MVP) |
| Database | RDS PostgreSQL | Tool registry, config, **booking records for MSIL validation** |
| Cache | ElastiCache Redis | Caching, rate limiting |
| Secrets | Secrets Manager | MSIL APIM credentials, LLM API keys |
| Logs | CloudWatch Logs | Centralized logging |
| Metrics | CloudWatch Metrics | Monitoring |
| Tracing | X-Ray | Distributed tracing |
| Audit Store | S3 | Audit logs (Object Lock optional for MVP) |
| Static Assets | CloudFront + S3 | UI hosting |

#### DEP-AWS-002: Network Architecture
```
┌─────────────────────────────────────────────────────────────────────┐
│                              VPC                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     Public Subnets                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │   │
│  │  │     ALB     │  │     NAT     │  │     NAT     │         │   │
│  │  │             │  │   Gateway   │  │   Gateway   │         │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Private Subnets                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │   │
│  │  │  EKS/ECS    │  │    RDS      │  │ ElastiCache │         │   │
│  │  │  Cluster    │  │  PostgreSQL │  │    Redis    │         │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.3 Configuration Management

#### DEP-CONFIG-001: Environment Configuration

```yaml
# config.yaml
environment: ${ENV:development}

server:
  host: 0.0.0.0
  port: 8000
  workers: ${WORKERS:4}

database:
  host: ${DB_HOST:localhost}
  port: ${DB_PORT:5432}
  name: ${DB_NAME:mcp_server}
  username: ${DB_USER:mcp}
  password: ${DB_PASSWORD}

redis:
  host: ${REDIS_HOST:localhost}
  port: ${REDIS_PORT:6379}

api_gateway:
  mode: ${API_GATEWAY_MODE:mock}
  base_url: ${API_GATEWAY_URL:http://localhost:8080}
  
llm:
  provider: ${LLM_PROVIDER:openai}
  api_key: ${LLM_API_KEY}
  model: ${LLM_MODEL:gpt-4}

observability:
  log_level: ${LOG_LEVEL:INFO}
  enable_tracing: ${ENABLE_TRACING:true}
```

### 9.4 Terraform Requirements

> **Critical**: Terraform scripts must be developed alongside application code from Day 1. This enables rapid deployment to Nagarro AWS for MVP demo.

#### DEP-TF-001: Infrastructure as Code Structure

```
infrastructure/
├── terraform/
│   ├── modules/                    # Reusable modules
│   │   ├── networking/             # VPC, Subnets, Security Groups
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── ecs/                    # ECS Cluster, Services, Tasks
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── rds/                    # RDS PostgreSQL
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── elasticache/            # Redis Cache
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── cloudfront/             # CDN + S3 for UI
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── alb/                    # Application Load Balancer
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   └── observability/          # CloudWatch, X-Ray
│   │       ├── main.tf
│   │       ├── variables.tf
│   │       └── outputs.tf
│   │
│   ├── environments/
│   │   ├── dev/                    # Nagarro AWS MVP Environment
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── terraform.tfvars
│   │   │   └── backend.tf
│   │   ├── staging/                # Future: Staging
│   │   └── prod/                   # Future: Production
│   │
│   └── shared/
│       ├── ecr/                    # ECR Repositories
│       └── iam/                    # IAM Roles & Policies
│
└── local/
    └── docker-compose.infra.yml    # Local dev infrastructure
```

#### DEP-TF-002: Terraform State Management

```hcl
# backend.tf - Remote state configuration
terraform {
  backend "s3" {
    bucket         = "nagarro-msil-mcp-terraform-state"
    key            = "environments/dev/terraform.tfstate"
    region         = "ap-south-1"  # Mumbai region for MSIL
    encrypt        = true
    dynamodb_table = "nagarro-msil-mcp-terraform-locks"
  }
}
```

#### DEP-TF-003: MVP Deployment Variables

```hcl
# terraform.tfvars for Nagarro AWS MVP
environment = "dev"
project     = "msil-mcp"
aws_region  = "ap-south-1"

# Networking
vpc_cidr = "10.0.0.0/16"

# ECS Configuration
ecs_cpu    = 512
ecs_memory = 1024
desired_count = 1  # MVP: single instance

# RDS Configuration
db_instance_class = "db.t3.micro"  # MVP: smallest instance
db_allocated_storage = 20

# ElastiCache Configuration
cache_node_type = "cache.t3.micro"  # MVP: smallest instance

# MSIL APIM Configuration
msil_apim_base_url = "https://dev-api.msil.example.com"
api_gateway_mode   = "msil_apim"  # Switch from mock to real APIM
```

#### DEP-TF-004: Quick Deployment Commands

```powershell
# One-time setup: Create S3 bucket and DynamoDB table for state
cd infrastructure/terraform/shared
terraform init
terraform apply

# Initialize and deploy MVP environment
cd infrastructure/terraform/environments/dev
terraform init

# Plan deployment (review changes)
terraform plan -out=tfplan

# Deploy MVP to Nagarro AWS
terraform apply tfplan

# Get outputs (URLs, endpoints)
terraform output

# Destroy when done (cost savings)
terraform destroy
```

#### DEP-TF-005: CI/CD Integration

```yaml
# .github/workflows/deploy-aws.yml
name: Deploy to AWS MVP

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  AWS_REGION: ap-south-1
  ECR_REGISTRY: ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.ap-south-1.amazonaws.com

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
          
      - name: Login to Amazon ECR
        uses: aws-actions/amazon-ecr-login@v2
          
      - name: Build and Push MCP Server Image
        run: |
          docker build -t msil-mcp-server ./mcp-server
          docker tag msil-mcp-server:latest $ECR_REGISTRY/msil-mcp-server:latest
          docker tag msil-mcp-server:latest $ECR_REGISTRY/msil-mcp-server:${{ github.sha }}
          docker push $ECR_REGISTRY/msil-mcp-server:latest
          docker push $ECR_REGISTRY/msil-mcp-server:${{ github.sha }}
          
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        
      - name: Deploy Infrastructure
        run: |
          cd infrastructure/terraform/environments/dev
          terraform init
          terraform apply -auto-approve
          
      - name: Build and Deploy Chat UI
        run: |
          cd chat-ui
          npm ci
          npm run build
          aws s3 sync dist/ s3://${{ secrets.CHAT_UI_BUCKET }} --delete
          aws cloudfront create-invalidation --distribution-id ${{ secrets.CHAT_CF_DIST }} --paths "/*"
          
      - name: Build and Deploy Admin UI
        run: |
          cd admin-ui
          npm ci
          npm run build
          aws s3 sync dist/ s3://${{ secrets.ADMIN_UI_BUCKET }} --delete
          aws cloudfront create-invalidation --distribution-id ${{ secrets.ADMIN_CF_DIST }} --paths "/*"
          
      - name: Update ECS Service
        run: |
          aws ecs update-service --cluster msil-mcp-cluster --service mcp-server --force-new-deployment
```

---

## 10. Observability & Audit Requirements

### 10.1 Logging

#### OBS-LOG-001: Structured Logging
```json
{
  "timestamp": "2026-01-30T10:15:30.123Z",
  "level": "INFO",
  "service": "mcp-server",
  "correlation_id": "abc-123-def",
  "tool_name": "GetNearbyDealers",
  "tool_version": "1.2.0",
  "user_id": "user-***-456",
  "action": "tool_execution",
  "status": "success",
  "latency_ms": 245,
  "message": "Tool executed successfully"
}
```

#### OBS-LOG-002: Log Levels
- ERROR: Failures requiring attention
- WARN: Potential issues
- INFO: Normal operations
- DEBUG: Detailed debugging (dev only)

### 10.2 Metrics

#### OBS-MET-001: Required Metrics

| Metric | Type | Labels |
|--------|------|--------|
| `mcp_tool_calls_total` | Counter | tool, status |
| `mcp_tool_latency_seconds` | Histogram | tool |
| `mcp_policy_decisions_total` | Counter | tool, decision |
| `mcp_active_sessions` | Gauge | - |
| `mcp_rate_limit_hits_total` | Counter | tool, user |

### 10.3 Tracing

#### OBS-TRACE-001: Distributed Tracing
- OpenTelemetry instrumentation
- Trace context propagation
- Span attributes for tool calls
- Integration with AWS X-Ray

### 10.4 Audit Trail

#### OBS-AUDIT-001: Audit Events
- All tool invocations
- Policy decisions (allow/deny)
- Configuration changes
- User authentication events

#### OBS-AUDIT-002: Audit Retention
- 12-month retention (mandatory)
- Immutable storage (S3 Object Lock)
- Tamper-evident records

### 10.5 Dashboards

#### OBS-DASH-001: Required Dashboards

| Dashboard | Purpose | Key Widgets |
|-----------|---------|-------------|
| Operations | Real-time monitoring | Invocations, Errors, Latency |
| Security | Security monitoring | Auth failures, Policy denies |
| Audit | Compliance review | Event timeline, User activity |
| Performance | Performance analysis | Latency trends, Throughput |

---

## 11. Demo Requirements (Stage-2)

### 11.1 Demo Scenario: Service Booking

#### DEMO-001: End-to-End Flow

```
User Prompt: "I want to book a car service for my vehicle MH12AB1234 
              tomorrow at 10 AM near Hinjewadi, Pune"

Expected Flow:
1. Chat UI receives prompt
2. LLM determines required tools
3. MCP Server discovers available tools
4. Execute: ResolveVehicle (MH12AB1234) → Vehicle details
5. Execute: GetNearbyDealers (Hinjewadi, Pune) → Dealer list
6. Execute: GetSlots (dealer_id, tomorrow, 10:00) → Available slots
7. Execute: CreateServiceBooking (all parameters) → Booking ID
8. Display: Booking confirmation to user
```

#### DEMO-002: Validation Points

| Validation | Method | Expected |
|------------|--------|----------|
| **DB Entry (MSIL Primary Validation)** | MSIL queries their backend database | Booking record exists with correct data |
| Tool Invocation | Code tracing & logs | Correct sequence of tools called |
| Guardrails | Log inspection | Input validation applied, invalid requests rejected |
| Audit Logs | Admin dashboard | All events captured with correlation IDs |
| Zero Static Coding | Schema inspection | Tools dynamically match OpenAPI specs |

> **Critical MSIL Validation**: MSIL team will independently verify that service bookings created through the MCP Server result in valid database entries in their backend systems. This is the **primary success criterion** for the MVP demo.

### 11.2 Demo Data Requirements

#### DEMO-003: Mock Data Setup

**Vehicles:**
```json
[
  {"registration": "MH12AB1234", "make": "Maruti", "model": "Swift", "year": 2022},
  {"registration": "DL10CD5678", "make": "Maruti", "model": "Baleno", "year": 2023}
]
```

**Dealers:**
```json
[
  {"id": "DLR001", "name": "MSIL Hinjewadi", "location": {"lat": 18.5912, "lng": 73.7389}},
  {"id": "DLR002", "name": "MSIL Wakad", "location": {"lat": 18.5985, "lng": 73.7603}}
]
```

**Available Slots:**
```json
[
  {"dealer_id": "DLR001", "date": "2026-01-31", "time": "10:00", "available": true},
  {"dealer_id": "DLR001", "date": "2026-01-31", "time": "11:00", "available": true}
]
```

---

## 12. Technology Stack

### 12.1 Backend

| Component | Technology | Justification |
|-----------|------------|---------------|
| **MCP Server** | Python 3.11+ / FastAPI | Async support, MCP SDK compatibility |
| **API Framework** | FastAPI | High performance, OpenAPI support |
| **Database** | PostgreSQL 15 | Reliable, feature-rich |
| **Cache** | Redis 7 | Fast, versatile |
| **Task Queue** | Celery (optional) | Background jobs |
| **Policy Engine** | OPA (Open Policy Agent) | Flexible policy rules |

### 12.2 Frontend

| Component | Technology | Justification |
|-----------|------------|---------------|
| **Framework** | React 18 + TypeScript | Industry standard, type safety |
| **UI Library** | Shadcn/UI + Tailwind CSS | Professional, customizable |
| **State Management** | Zustand / React Query | Lightweight, efficient |
| **Charts** | Recharts | React-native charts |
| **Icons** | Lucide React | Consistent icon set |

### 12.3 Infrastructure

| Component | Technology | Justification |
|-----------|------------|---------------|
| **Container Runtime** | Docker | Standard containerization |
| **Orchestration** | Kubernetes (EKS) | Scalable, AWS-native |
| **IaC** | Terraform | Industry standard |
| **CI/CD** | GitHub Actions | Integrated, flexible |

### 12.4 Observability

| Component | Technology | Justification |
|-----------|------------|---------------|
| **Logging** | OpenTelemetry + CloudWatch | Unified observability |
| **Metrics** | Prometheus + CloudWatch | Standard metrics |
| **Tracing** | OpenTelemetry + X-Ray | Distributed tracing |
| **Dashboards** | CloudWatch Dashboards | AWS-native |

---

## 13. Development Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Project setup and scaffolding
- [ ] MCP protocol implementation
- [ ] Basic tool registry
- [ ] Mock API framework
- [ ] **Local infrastructure setup (Docker containers for DB/Redis via Rancher Desktop)**
- [ ] **Terraform module scaffolding (parallel development from Day 1)**

### Phase 2: Core Features (Week 3-4)
- [ ] OpenAPI tool generator
- [ ] Schema validation engine
- [ ] Policy engine integration
- [ ] Chat UI basic implementation
- [ ] Admin UI basic implementation
- [ ] **Terraform modules: VPC, ECS, RDS, ElastiCache**

### Phase 3: Integration (Week 5-6)
- [ ] LLM integration (configurable)
- [ ] Service booking tool bundle
- [ ] End-to-end flow testing (local with mock APIs)
- [ ] Mock data population
- [ ] **Terraform modules: ALB, CloudFront, S3, IAM**
- [ ] **First AWS deployment test (infrastructure only)**

### Phase 4: MVP Deployment & Demo Prep (Week 7-8)
- [ ] UI/UX refinement (MSIL branding, enterprise-grade look)
- [ ] Observability dashboards
- [ ] Audit log implementation
- [ ] **Configure MSIL APIM integration (credentials, endpoints)**
- [ ] **Deploy MVP to Nagarro AWS environment**
- [ ] **End-to-end testing with MSIL Dev APIM**
- [ ] Demo rehearsal
- [ ] Documentation

### Phase 5: Validation & Handover (Week 9-10)
- [ ] **MSIL validation of backend database entries**
- [ ] Security hardening
- [ ] Performance testing
- [ ] Final demo to MSIL stakeholders
- [ ] Handover documentation
- [ ] Knowledge transfer sessions

---

## 15. Environment Summary

| Environment | Purpose | API Backend | Database | Hosting |
|-------------|---------|-------------|----------|---------|
| **Local Dev** | Development & debugging | Mock APIs (localhost:8080) | PostgreSQL (Rancher Desktop) | Native processes |
| **AWS MVP** | Demo to MSIL | MSIL Dev APIM | RDS PostgreSQL | ECS Fargate + CloudFront |
| **AWS Prod** | Future production | MSIL Prod APIM | RDS PostgreSQL (Multi-AZ) | ECS/EKS |

---

## 16. Success Criteria

### 16.1 MVP Demo Success
| Criteria | Validation Method |
|----------|-------------------|
| Service booking completes end-to-end | MSIL checks backend DB entry |
| Tools auto-generated from OpenAPI | Show tool schema matches spec |
| No static coding for tool definitions | Demonstrate dynamic generation |
| Audit trail captured | Show audit logs in admin UI |
| Professional UI/UX | Visual inspection by stakeholders |

### 16.2 Technical Success
| Criteria | Target |
|----------|--------|
| API response time | < 500ms p95 |
| System availability during demo | 100% |
| Zero security vulnerabilities | SAST/DAST clean |
| Terraform deployment time | < 30 minutes |

---

## 14. Glossary

| Term | Definition |
|------|------------|
| **MCP** | Model Context Protocol - Standard for AI tool integration |
| **APIM** | API Management - MSIL's AWS-based API gateway |
| **Tool** | An MCP-compatible function exposed to AI agents |
| **Tool Bundle** | Logical grouping of tools (MCP Product) |
| **OpenAPI** | API specification format (Swagger) |
| **RBAC** | Role-Based Access Control |
| **PIM/PAM** | Privileged Identity/Access Management |
| **SSE** | Server-Sent Events |
| **WORM** | Write Once Read Many (immutable storage) |

---

## Document Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Technical Lead | | | |
| Solution Architect | | | |
| Project Manager | | | |
| Client Stakeholder | | | |

---

**End of Document**
