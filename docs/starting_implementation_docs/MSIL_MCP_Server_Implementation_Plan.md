# MSIL Composite MCP Server - Implementation Plan

**Document Version:** 1.0  
**Date:** January 30, 2026  
**Timeline:** 2 Days (MVP Demo)  
**Prepared By:** Nagarro Development Team  

---

## Executive Summary

This implementation plan is designed for a **2-day sprint** to deliver a working MVP that demonstrates:
1. **Day 1**: Local demo with mock APIs (end of day)
2. **Day 2**: AWS deployment + MSIL APIM integration (demo ready)

> ⚠️ **Critical**: This plan prioritizes a working demo over completeness. Features are cut to minimum viable scope.

---

## Table of Contents

1. [MVP Scope Definition](#1-mvp-scope-definition)
2. [Day 1 Plan - Local MVP](#2-day-1-plan---local-mvp)
3. [Day 2 Plan - AWS Deployment](#3-day-2-plan---aws-deployment)
4. [Task Breakdown with Time Estimates](#4-task-breakdown-with-time-estimates)
5. [Cut Features (Post-MVP)](#5-cut-features-post-mvp)
6. [Risk Mitigation](#6-risk-mitigation)
7. [Demo Script](#7-demo-script)

---

## 1. MVP Scope Definition

### 1.1 What's IN for MVP (Must Have)

| Component | MVP Scope |
|-----------|-----------|
| **MCP Server** | Basic MCP protocol (tools/list, tools/call) |
| **Tool Registry** | In-memory + PostgreSQL (simple CRUD) |
| **OpenAPI Parser** | Parse spec → generate tools (basic) |
| **Tool Executor** | Execute tools against Mock/APIM |
| **Chat UI** | Single page chat with tool visualization |
| **Admin UI** | Dashboard + Tool list view only |
| **Mock API** | Service booking APIs (6 endpoints) |
| **Service Booking Tools** | 6 tools for complete booking flow |
| **LLM Integration** | OpenAI GPT-4 only |
| **Auth** | Simple API key / hardcoded for demo |
| **Terraform** | Basic ECS + RDS + S3/CloudFront |

### 1.2 What's OUT for MVP (Defer)

| Feature | Reason |
|---------|--------|
| Full OAuth2/OIDC | Use simple auth for demo |
| OPA Policy Engine | Hardcode basic checks |
| Rate Limiting | Not needed for demo |
| Audit Logging to S3 | Console/DB logging only |
| User Management | Single demo user |
| Multiple LLM Providers | OpenAI only |
| Tool Versioning | Single version |
| SSE Streaming | Simple request/response |
| Advanced Caching | Basic Redis caching |
| Full Test Suite | Manual testing only |

### 1.3 Success Criteria for Demo

```
✅ User can chat and request service booking
✅ LLM discovers tools via MCP protocol
✅ Tools execute against Mock API (local) / MSIL APIM (AWS)
✅ Booking is created and confirmed
✅ Admin can see tool list and basic metrics
✅ MSIL can verify database entry
```

---

## 2. Day 1 Plan - Local MVP

### Timeline: January 30, 2026 (Today)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DAY 1 TIMELINE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  08:00 ─────────────────────────────────────────────────────────── 10:00   │
│  │ PHASE 1: Project Setup & Infrastructure                              │   │
│  │ • Create project structure                                           │   │
│  │ • Docker compose for PostgreSQL + Redis                              │   │
│  │ • Initialize Python backend                                          │   │
│  │ • Initialize React frontends                                         │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  10:00 ─────────────────────────────────────────────────────────── 13:00   │
│  │ PHASE 2: MCP Server Core                                             │   │
│  │ • MCP protocol handler (tools/list, tools/call)                      │   │
│  │ • Tool registry (in-memory + DB)                                     │   │
│  │ • OpenAPI parser (basic)                                             │   │
│  │ • Tool executor with Mock adapter                                    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  13:00 ─────────────────────────────────────────────────────────── 14:00   │
│  │ LUNCH BREAK                                                          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  14:00 ─────────────────────────────────────────────────────────── 16:00   │
│  │ PHASE 3: Mock API + Service Booking Tools                            │   │
│  │ • Mock API server (6 endpoints)                                      │   │
│  │ • Service booking OpenAPI spec                                       │   │
│  │ • Generate tools from spec                                           │   │
│  │ • Test tool execution                                                │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  16:00 ─────────────────────────────────────────────────────────── 19:00   │
│  │ PHASE 4: Chat UI + LLM Integration                                   │   │
│  │ • Chat UI with MSIL branding                                         │   │
│  │ • OpenAI integration                                                 │   │
│  │ • MCP client in frontend                                             │   │
│  │ • Tool execution visualization                                       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  19:00 ─────────────────────────────────────────────────────────── 21:00   │
│  │ PHASE 5: Admin UI + Polish                                           │   │
│  │ • Admin dashboard (basic metrics)                                    │   │
│  │ • Tool list view                                                     │   │
│  │ • End-to-end testing                                                 │   │
│  │ • Bug fixes                                                          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  21:00 ──────────────────────────────────────────────────────────         │
│  │ ✅ LOCAL DEMO READY                                                  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Day 2 Plan - AWS Deployment

### Timeline: January 31, 2026

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DAY 2 TIMELINE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  08:00 ─────────────────────────────────────────────────────────── 10:00   │
│  │ PHASE 6: Dockerize Applications                                      │   │
│  │ • Dockerfile for MCP Server                                          │   │
│  │ • Dockerfile for Mock API                                            │   │
│  │ • Build and test Docker images locally                               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  10:00 ─────────────────────────────────────────────────────────── 13:00   │
│  │ PHASE 7: Terraform + AWS Infrastructure                              │   │
│  │ • VPC, Subnets, Security Groups                                      │   │
│  │ • ECR repositories                                                   │   │
│  │ • RDS PostgreSQL                                                     │   │
│  │ • ECS Fargate cluster + services                                     │   │
│  │ • ALB                                                                │   │
│  │ • S3 + CloudFront for UI                                            │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  13:00 ─────────────────────────────────────────────────────────── 14:00   │
│  │ LUNCH BREAK                                                          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  14:00 ─────────────────────────────────────────────────────────── 16:00   │
│  │ PHASE 8: Deploy to AWS                                               │   │
│  │ • Push Docker images to ECR                                          │   │
│  │ • Run terraform apply                                                │   │
│  │ • Deploy UI to S3                                                    │   │
│  │ • Configure environment variables                                    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  16:00 ─────────────────────────────────────────────────────────── 18:00   │
│  │ PHASE 9: MSIL APIM Integration                                       │   │
│  │ • Configure MSIL APIM credentials                                    │   │
│  │ • Switch from Mock to APIM mode                                      │   │
│  │ • Test with real APIs                                                │   │
│  │ • Verify database entries                                            │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  18:00 ─────────────────────────────────────────────────────────── 20:00   │
│  │ PHASE 10: Final Testing + Demo Prep                                  │   │
│  │ • End-to-end AWS testing                                             │   │
│  │ • Demo script walkthrough                                            │   │
│  │ • Bug fixes                                                          │   │
│  │ • Documentation                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  20:00 ──────────────────────────────────────────────────────────         │
│  │ ✅ AWS DEMO READY                                                    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Task Breakdown with Time Estimates

### PHASE 1: Project Setup & Infrastructure (2 hours)

| # | Task | Time | Priority | Dependencies |
|---|------|------|----------|--------------|
| 1.1 | Create project folder structure | 15 min | P0 | None |
| 1.2 | Create docker-compose.infra.yml (PostgreSQL + Redis) | 15 min | P0 | 1.1 |
| 1.3 | Start infrastructure containers | 5 min | P0 | 1.2 |
| 1.4 | Create database schema (init.sql) | 20 min | P0 | 1.3 |
| 1.5 | Initialize MCP Server (FastAPI project) | 20 min | P0 | 1.1 |
| 1.6 | Initialize Mock API (FastAPI project) | 15 min | P0 | 1.1 |
| 1.7 | Initialize Chat UI (Vite + React + TypeScript) | 15 min | P0 | 1.1 |
| 1.8 | Initialize Admin UI (Vite + React + TypeScript) | 15 min | P0 | 1.1 |

**Deliverable**: All projects created, infrastructure running, DB initialized

---

### PHASE 2: MCP Server Core (3 hours)

| # | Task | Time | Priority | Dependencies |
|---|------|------|----------|--------------|
| 2.1 | Create MCP protocol models (Pydantic) | 20 min | P0 | 1.5 |
| 2.2 | Implement `/mcp` endpoint (JSON-RPC handler) | 30 min | P0 | 2.1 |
| 2.3 | Implement `tools/list` handler | 20 min | P0 | 2.2 |
| 2.4 | Implement `tools/call` handler | 30 min | P0 | 2.2 |
| 2.5 | Create Tool model and basic registry | 20 min | P0 | 2.1 |
| 2.6 | Create database repository for tools | 20 min | P0 | 2.5 |
| 2.7 | Create OpenAPI parser (basic) | 30 min | P0 | 2.5 |
| 2.8 | Create Tool Executor with Mock adapter | 30 min | P0 | 2.4 |
| 2.9 | Add basic error handling | 10 min | P0 | 2.8 |
| 2.10 | Test MCP endpoints with curl/Postman | 10 min | P0 | 2.9 |

**Deliverable**: MCP Server responds to tools/list and tools/call

---

### PHASE 3: Mock API + Service Booking Tools (2 hours)

| # | Task | Time | Priority | Dependencies |
|---|------|------|----------|--------------|
| 3.1 | Create Mock API project structure | 10 min | P0 | 1.6 |
| 3.2 | Implement POST `/api/customer/resolve` | 10 min | P0 | 3.1 |
| 3.3 | Implement POST `/api/vehicle/resolve` | 10 min | P0 | 3.1 |
| 3.4 | Implement POST `/api/dealers/nearby` | 15 min | P0 | 3.1 |
| 3.5 | Implement POST `/api/slots/available` | 15 min | P0 | 3.1 |
| 3.6 | Implement POST `/api/booking/create` | 15 min | P0 | 3.1 |
| 3.7 | Implement GET `/api/booking/{id}` | 10 min | P0 | 3.1 |
| 3.8 | Create OpenAPI spec for Mock API | 20 min | P0 | 3.7 |
| 3.9 | Load OpenAPI spec and generate tools | 15 min | P0 | 3.8, 2.7 |
| 3.10 | Test complete tool execution flow | 15 min | P0 | 3.9 |

**Deliverable**: 6 service booking tools working with Mock API

---

### PHASE 4: Chat UI + LLM Integration (3 hours)

| # | Task | Time | Priority | Dependencies |
|---|------|------|----------|--------------|
| 4.1 | Install Shadcn/UI + Tailwind | 15 min | P0 | 1.7 |
| 4.2 | Create MSIL theme (colors, logo) | 15 min | P0 | 4.1 |
| 4.3 | Create ChatContainer component | 20 min | P0 | 4.1 |
| 4.4 | Create MessageList component | 15 min | P0 | 4.3 |
| 4.5 | Create MessageBubble component | 15 min | P0 | 4.4 |
| 4.6 | Create InputArea component | 15 min | P0 | 4.3 |
| 4.7 | Create ToolExecutionCard component | 20 min | P0 | 4.4 |
| 4.8 | Create chat store (Zustand) | 15 min | P0 | 4.3 |
| 4.9 | Implement OpenAI API integration | 30 min | P0 | 4.8 |
| 4.10 | Implement MCP client (tools/list, tools/call) | 30 min | P0 | 4.9 |
| 4.11 | Connect LLM with MCP tools | 20 min | P0 | 4.10 |
| 4.12 | Test chat flow end-to-end | 15 min | P0 | 4.11 |

**Deliverable**: Chat UI working with LLM and MCP tools

---

### PHASE 5: Admin UI + Polish (2 hours)

| # | Task | Time | Priority | Dependencies |
|---|------|------|----------|--------------|
| 5.1 | Create Admin layout (sidebar, header) | 20 min | P0 | 1.8 |
| 5.2 | Create Dashboard page with KPI cards | 25 min | P0 | 5.1 |
| 5.3 | Create Tools list page | 25 min | P0 | 5.1 |
| 5.4 | Add basic API to fetch metrics | 15 min | P1 | 5.2 |
| 5.5 | Add basic API to fetch tools | 15 min | P0 | 5.3 |
| 5.6 | End-to-end local testing | 15 min | P0 | 5.5 |
| 5.7 | Bug fixes and polish | 25 min | P0 | 5.6 |

**Deliverable**: Admin UI with dashboard and tools list

---

### PHASE 6: Dockerize Applications (2 hours)

| # | Task | Time | Priority | Dependencies |
|---|------|------|----------|--------------|
| 6.1 | Create Dockerfile for MCP Server | 20 min | P0 | Phase 5 |
| 6.2 | Create Dockerfile for Mock API | 15 min | P0 | Phase 5 |
| 6.3 | Create docker-compose.yml (full stack) | 20 min | P1 | 6.2 |
| 6.4 | Build and test MCP Server image | 15 min | P0 | 6.1 |
| 6.5 | Build and test Mock API image | 10 min | P0 | 6.2 |
| 6.6 | Build Chat UI for production | 15 min | P0 | Phase 5 |
| 6.7 | Build Admin UI for production | 15 min | P0 | Phase 5 |
| 6.8 | Test full stack with Docker | 10 min | P0 | 6.7 |

**Deliverable**: All Docker images built and tested

---

### PHASE 7: Terraform + AWS Infrastructure (3 hours)

| # | Task | Time | Priority | Dependencies |
|---|------|------|----------|--------------|
| 7.1 | Create Terraform project structure | 15 min | P0 | 6.8 |
| 7.2 | Create VPC module (simplified) | 20 min | P0 | 7.1 |
| 7.3 | Create Security Groups | 15 min | P0 | 7.2 |
| 7.4 | Create ECR repositories | 10 min | P0 | 7.1 |
| 7.5 | Create RDS PostgreSQL (db.t3.micro) | 20 min | P0 | 7.2 |
| 7.6 | Create ECS Cluster + Task Definition | 25 min | P0 | 7.5 |
| 7.7 | Create ALB + Target Group | 20 min | P0 | 7.6 |
| 7.8 | Create ECS Service | 15 min | P0 | 7.7 |
| 7.9 | Create S3 buckets for UI | 10 min | P0 | 7.1 |
| 7.10 | Create CloudFront distributions | 20 min | P0 | 7.9 |
| 7.11 | Create Secrets Manager entries | 10 min | P0 | 7.1 |
| 7.12 | Validate terraform plan | 10 min | P0 | 7.11 |

**Deliverable**: Terraform ready to deploy

---

### PHASE 8: Deploy to AWS (2 hours)

| # | Task | Time | Priority | Dependencies |
|---|------|------|----------|--------------|
| 8.1 | Run terraform apply (create infra) | 20 min | P0 | 7.12 |
| 8.2 | Push MCP Server image to ECR | 10 min | P0 | 8.1 |
| 8.3 | Push Mock API image to ECR | 10 min | P0 | 8.1 |
| 8.4 | Initialize RDS database | 15 min | P0 | 8.1 |
| 8.5 | Configure Secrets Manager values | 10 min | P0 | 8.1 |
| 8.6 | Update ECS service (deploy) | 10 min | P0 | 8.5 |
| 8.7 | Deploy Chat UI to S3 | 10 min | P0 | 8.1 |
| 8.8 | Deploy Admin UI to S3 | 10 min | P0 | 8.1 |
| 8.9 | Invalidate CloudFront cache | 5 min | P0 | 8.8 |
| 8.10 | Verify all services running | 15 min | P0 | 8.9 |

**Deliverable**: All services running on AWS

---

### PHASE 9: MSIL APIM Integration (2 hours)

| # | Task | Time | Priority | Dependencies |
|---|------|------|----------|--------------|
| 9.1 | Configure MSIL APIM credentials in Secrets | 15 min | P0 | 8.10 |
| 9.2 | Update API_GATEWAY_MODE to msil_apim | 10 min | P0 | 9.1 |
| 9.3 | Implement MSIL API adapter (if needed) | 30 min | P0 | 9.2 |
| 9.4 | Redeploy with APIM configuration | 15 min | P0 | 9.3 |
| 9.5 | Test service booking with real APIs | 20 min | P0 | 9.4 |
| 9.6 | Verify database entry in MSIL backend | 15 min | P0 | 9.5 |
| 9.7 | Debug and fix issues | 15 min | P0 | 9.6 |

**Deliverable**: MCP Server working with MSIL Dev APIM

---

### PHASE 10: Final Testing + Demo Prep (2 hours)

| # | Task | Time | Priority | Dependencies |
|---|------|------|----------|--------------|
| 10.1 | Full end-to-end AWS testing | 30 min | P0 | 9.7 |
| 10.2 | Test all demo scenarios | 20 min | P0 | 10.1 |
| 10.3 | Prepare demo script | 15 min | P0 | 10.2 |
| 10.4 | Practice demo walkthrough | 15 min | P0 | 10.3 |
| 10.5 | Fix critical bugs | 20 min | P0 | 10.4 |
| 10.6 | Document URLs and credentials | 10 min | P1 | 10.5 |
| 10.7 | Backup and cleanup | 10 min | P1 | 10.6 |

**Deliverable**: Demo ready!

---

## 5. Cut Features (Post-MVP)

These features are explicitly deferred to post-MVP sprints:

| Feature | Effort | Sprint |
|---------|--------|--------|
| Full OAuth2/OIDC authentication | 2 days | Sprint 2 |
| OPA Policy Engine | 1 day | Sprint 2 |
| Rate Limiting | 0.5 day | Sprint 2 |
| Audit Logging to S3 (WORM) | 1 day | Sprint 2 |
| User/Role Management UI | 2 days | Sprint 3 |
| Multiple LLM Providers | 1 day | Sprint 2 |
| Tool Versioning | 1 day | Sprint 3 |
| SSE Streaming | 0.5 day | Sprint 2 |
| Full Test Suite | 3 days | Sprint 3 |
| CI/CD Pipeline | 1 day | Sprint 2 |
| ElastiCache Redis (AWS) | 0.5 day | Sprint 2 |
| WAF Configuration | 0.5 day | Sprint 3 |

---

## 6. Risk Mitigation

### High Risk Items

| Risk | Impact | Mitigation |
|------|--------|------------|
| **MSIL APIM credentials not available** | Cannot demo real integration | Have Mock API ready as fallback; demo local first |
| **OpenAI API issues/rate limits** | Chat won't work | Pre-test, have backup API key, or switch to Azure |
| **Terraform errors** | Cannot deploy to AWS | Pre-validate with `terraform plan`; have manual deploy steps ready |
| **RDS initialization fails** | No database | Have SQL scripts ready for manual execution |
| **Time overrun on MCP Server** | No time for UI | Use minimal UI; focus on core functionality |

### Contingency Plans

**Plan A (Normal)**: Full implementation as planned  
**Plan B (Time crunch)**: Skip Admin UI, focus on Chat + MCP Server  
**Plan C (Major issues)**: Demo locally only with mock APIs  

---

## 7. Demo Script

### 7.1 Local Demo (End of Day 1)

```markdown
## Local Demo Script (5 minutes)

### Setup
- All services running locally
- Browser open to http://localhost:3000 (Chat UI)
- Browser open to http://localhost:3001 (Admin UI)

### Demo Flow

1. **Show Admin UI** (30 sec)
   - "This is the Admin Console where we manage MCP tools"
   - Show dashboard with metrics
   - Show tool list: "6 service booking tools auto-generated from OpenAPI"

2. **Show Chat UI** (30 sec)
   - "This is the AI Service Assistant powered by MCP"
   - Point out MSIL branding

3. **Service Booking Demo** (3 min)
   - Type: "I want to book a car service for my vehicle MH12AB1234 tomorrow at 10 AM near Hinjewadi Pune"
   - Watch tools execute:
     - "MCP Server discovers available tools"
     - "LLM decides to call ResolveVehicle" → Show result
     - "LLM calls GetNearbyDealers" → Show dealers
     - "LLM calls GetSlots" → Show available slots
     - "LLM calls CreateServiceBooking" → Show booking confirmation
   - "Booking BK12345 confirmed!"

4. **Show Database Entry** (30 sec)
   - Query service_bookings table
   - "MSIL can verify this entry in their backend"

5. **Key Points** (30 sec)
   - "Zero static coding - tools generated from OpenAPI"
   - "MCP protocol enables any AI client to use these tools"
   - "Ready for AWS deployment"
```

### 7.2 AWS Demo (End of Day 2)

```markdown
## AWS Demo Script (7 minutes)

### Setup
- Chat UI: https://chat.msil-mcp.example.com
- Admin UI: https://admin.msil-mcp.example.com
- AWS Console open (optional)

### Demo Flow

1. **Architecture Overview** (1 min)
   - Show architecture diagram
   - "Deployed on Nagarro AWS"
   - "Connects to MSIL Dev APIM for real API calls"

2. **Admin UI on AWS** (30 sec)
   - Show live dashboard
   - Show tools list

3. **Service Booking - Real Flow** (4 min)
   - Same as local demo but with real data
   - "This is hitting MSIL's actual Dev APIs"
   - Show booking confirmation

4. **MSIL Validation** (1 min)
   - "MSIL team can now check their database"
   - Show correlation ID in logs
   - "Full audit trail available"

5. **Technical Highlights** (30 sec)
   - "Infrastructure as Code with Terraform"
   - "Scalable with ECS Fargate"
   - "Production-ready architecture"
```

---

## 8. Project Structure (Final)

```
msil_mcp/
├── README.md
├── docker-compose.yml                    # Full stack (optional)
├── docker-compose.infra.yml              # Local infra only
│
├── mcp-server/                           # MCP Server (FastAPI)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                       # FastAPI app
│   │   ├── config.py                     # Configuration
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── mcp.py                    # MCP endpoints
│   │   │   ├── admin.py                  # Admin endpoints
│   │   │   └── chat.py                   # Chat endpoints
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── mcp/
│   │   │   │   ├── protocol.py           # MCP protocol handler
│   │   │   │   └── models.py             # MCP models
│   │   │   ├── tools/
│   │   │   │   ├── registry.py           # Tool registry
│   │   │   │   ├── executor.py           # Tool executor
│   │   │   │   └── generator.py          # OpenAPI parser
│   │   │   └── llm/
│   │   │       └── openai_client.py      # OpenAI integration
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── tool.py
│   │   │   └── booking.py
│   │   └── db/
│   │       ├── __init__.py
│   │       ├── database.py
│   │       └── repositories.py
│   └── specs/
│       └── service-booking.yaml          # OpenAPI spec
│
├── mock-api/                             # Mock API Server
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── customer.py
│   │   │   ├── vehicle.py
│   │   │   ├── dealers.py
│   │   │   ├── slots.py
│   │   │   └── booking.py
│   │   └── data/
│   │       └── mock_data.py              # Mock data
│   └── openapi.yaml                      # OpenAPI spec
│
├── chat-ui/                              # Chat Interface (React)
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   ├── public/
│   │   └── msil-logo.svg
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── components/
│       │   ├── ui/                       # Shadcn components
│       │   ├── chat/
│       │   │   ├── ChatContainer.tsx
│       │   │   ├── MessageList.tsx
│       │   │   ├── MessageBubble.tsx
│       │   │   ├── InputArea.tsx
│       │   │   └── ToolExecutionCard.tsx
│       │   └── layout/
│       │       └── Header.tsx
│       ├── hooks/
│       │   └── useChat.ts
│       ├── lib/
│       │   ├── api.ts
│       │   └── mcp-client.ts
│       ├── stores/
│       │   └── chatStore.ts
│       └── styles/
│           └── globals.css
│
├── admin-ui/                             # Admin Interface (React)
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── components/
│       │   ├── ui/
│       │   ├── dashboard/
│       │   │   ├── KPICards.tsx
│       │   │   └── RecentActivity.tsx
│       │   ├── tools/
│       │   │   └── ToolList.tsx
│       │   └── layout/
│       │       ├── Sidebar.tsx
│       │       └── Header.tsx
│       └── pages/
│           ├── Dashboard.tsx
│           └── Tools.tsx
│
├── infrastructure/
│   ├── local/
│   │   ├── docker-compose.infra.yml
│   │   └── init-scripts/
│   │       └── 01-init.sql
│   │
│   └── terraform/
│       ├── modules/
│       │   ├── vpc/
│       │   │   ├── main.tf
│       │   │   ├── variables.tf
│       │   │   └── outputs.tf
│       │   ├── ecr/
│       │   ├── rds/
│       │   ├── ecs/
│       │   ├── alb/
│       │   └── cloudfront/
│       │
│       └── environments/
│           └── dev/
│               ├── main.tf
│               ├── variables.tf
│               ├── terraform.tfvars
│               └── outputs.tf
│
└── docs/
    ├── MSIL_MCP_Server_Requirements_Specification.md
    ├── MSIL_MCP_Server_Design_Document.md
    └── MSIL_MCP_Server_Implementation_Plan.md
```

---

## 9. Quick Reference Commands

### Day 1 - Local Development

```powershell
# Start infrastructure
cd infrastructure/local
docker-compose -f docker-compose.infra.yml up -d

# Start MCP Server
cd mcp-server
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Start Mock API (new terminal)
cd mock-api
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080

# Start Chat UI (new terminal)
cd chat-ui
npm install
npm run dev

# Start Admin UI (new terminal)
cd admin-ui
npm install
npm run dev
```

### Day 2 - AWS Deployment

```powershell
# Build Docker images
docker build -t msil-mcp-server ./mcp-server
docker build -t msil-mock-api ./mock-api

# Build UI for production
cd chat-ui && npm run build
cd admin-ui && npm run build

# Terraform
cd infrastructure/terraform/environments/dev
terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Push to ECR (after terraform creates ECR)
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.ap-south-1.amazonaws.com
docker tag msil-mcp-server:latest <account>.dkr.ecr.ap-south-1.amazonaws.com/msil-mcp-server:latest
docker push <account>.dkr.ecr.ap-south-1.amazonaws.com/msil-mcp-server:latest

# Deploy UI to S3
aws s3 sync chat-ui/dist/ s3://msil-mcp-chat-ui --delete
aws s3 sync admin-ui/dist/ s3://msil-mcp-admin-ui --delete
```

---

## 10. Checklist

### Day 1 End Checklist

- [ ] Infrastructure containers running (PostgreSQL, Redis)
- [ ] MCP Server running on :8000
- [ ] Mock API running on :8080
- [ ] Chat UI running on :3000
- [ ] Admin UI running on :3001
- [ ] Can list tools via MCP protocol
- [ ] Can execute tools via MCP protocol
- [ ] Chat UI connects to OpenAI
- [ ] Full booking flow works end-to-end
- [ ] Booking saved to database
- [ ] Local demo successful

### Day 2 End Checklist

- [ ] Docker images built and tested
- [ ] Terraform applied successfully
- [ ] RDS database initialized
- [ ] ECS services running healthy
- [ ] UI deployed to S3/CloudFront
- [ ] MCP Server accessible via ALB
- [ ] MSIL APIM credentials configured
- [ ] API_GATEWAY_MODE set to msil_apim
- [ ] Full booking flow works on AWS
- [ ] MSIL database entry verified
- [ ] AWS demo successful

---

**LET'S BUILD THIS! 🚀**

---

**End of Implementation Plan**
