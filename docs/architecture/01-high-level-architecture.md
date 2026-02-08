# High-Level Architecture

**Document Version**: 2.2  
**Last Updated**: February 2, 2026  
**Classification**: Internal

---

## 1. Executive Summary

The MSIL MCP (Model Context Protocol) Server provides a secure, governed bridge between Large Language Models (LLMs) and Maruti Suzuki's enterprise APIs. This document presents the logical architecture view showing the Composite MCP Server topology, integration with MSIL API Manager, and governance components.

**Phase 1-3 Addition**: Exposure Governance (Layer B) controls tool visibility by role. It is managed via the Admin Portal and enforced in the MCP tools/list and tools/call flows.

**Important Architecture Note**:
> The **Host/Agent application** (with embedded MCP Client) communicates with the MCP Server using the MCP protocol. The **LLM** (e.g., GPT-4, Claude) **only decides which tool to call** based on the tool descriptions—it does **not** directly speak MCP. The security and governance responsibility lies with the Host application and MCP Server.

---

## 2. System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    SYSTEM CONTEXT                                        │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│    ┌──────────────┐         ┌──────────────┐         ┌──────────────┐                  │
│    │   End Users  │         │  Developers  │         │    Admins    │                  │
│    │  (Employees) │         │   (IT Team)  │         │  (Platform)  │                  │
│    └──────┬───────┘         └──────┬───────┘         └──────┬───────┘                  │
│           │                        │                        │                           │
│           ▼                        ▼                        ▼                           │
│    ┌──────────────┐         ┌──────────────┐         ┌──────────────┐                  │
│    │   Chat UI    │         │  OpenAPI     │         │  Admin Portal│                  │
│    │  Interface   │         │  Importer    │         │  (React UI)  │                  │
│    └──────┬───────┘         └──────┬───────┘         └──────┬───────┘                  │
│           │                        │                        │                           │
│           └────────────────────────┼────────────────────────┘                           │
│                                    │                                                    │
│                                    ▼                                                    │
│    ┌─────────────────────────────────────────────────────────────────────────┐         │
│    │                                                                         │         │
│    │                     ╔═══════════════════════════════╗                   │         │
│    │                     ║   MSIL MCP SERVER (COMPOSITE)  ║                   │         │
│    │                     ║                               ║                   │         │
│    │                     ║   ┌─────────────────────────┐ ║                   │         │
│    │                     ║   │     Gateway Layer       │ ║                   │         │
│    │                     ║   │   (Auth, Rate Limit)    │ ║                   │         │
│    │                     ║   └───────────┬─────────────┘ ║                   │         │
│    │                     ║               │               ║                   │         │
│    │                     ║   ┌───────────▼─────────────┐ ║                   │         │
│    │                     ║   │    MCP Protocol Layer   │ ║                   │         │
│    │                     ║   │  (Tool Registry, Router)│ ║                   │         │
│    │                     ║   └───────────┬─────────────┘ ║                   │         │
│    │                     ║               │               ║                   │         │
│    │                     ║   ┌───────────▼─────────────┐ ║                   │         │
│    │                     ║   │   Governance Layer      │ ║                   │         │
│    │                     ║   │  (Policy, Audit, PIM)   │ ║                   │         │
│    │                     ║   └─────────────────────────┘ ║                   │         │
│    │                     ╚═══════════════════════════════╝                   │         │
│    │                                    │                                    │         │
│    └────────────────────────────────────┼────────────────────────────────────┘         │
│                                         │                                              │
│                                         ▼                                              │
│    ┌─────────────────────────────────────────────────────────────────────────┐         │
│    │                        MSIL APIM (API Gateway)                          │         │
│    │   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │         │
│    │   │  Dealer API │ │  Service    │ │  Inventory  │ │  Finance    │      │         │
│    │   │  Products   │ │  Products   │ │  Products   │ │  Products   │      │         │
│    │   └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      │         │
│    └─────────────────────────────────────────────────────────────────────────┘         │
│                                         │                                              │
│                                         ▼                                              │
│    ┌─────────────────────────────────────────────────────────────────────────┐         │
│    │                       MSIL Backend Systems                              │         │
│    │   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │         │
│    │   │     DMS     │ │   Nexa+     │ │    SAP      │ │   Legacy    │      │         │
│    │   │   Systems   │ │   Arena     │ │   Systems   │ │   Systems   │      │         │
│    │   └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      │         │
│    └─────────────────────────────────────────────────────────────────────────┘         │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Logical Architecture

### 3.1 Composite MCP Server Topology

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           COMPOSITE MCP SERVER ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              PRESENTATION TIER                                   │   │
│  │                                                                                  │   │
│  │   ┌────────────────┐    ┌────────────────┐    ┌────────────────┐               │   │
│  │   │   Chat UI      │    │  Admin Portal  │    │  API Clients   │               │   │
│  │   │   (React)      │    │   (React)      │    │  (LLM/Agents)  │               │   │
│  │   │   Port: 3000   │    │   Port: 3001   │    │                │               │   │
│  │   └────────┬───────┘    └───────┬────────┘    └───────┬────────┘               │   │
│  │            │                    │                     │                         │   │
│  └────────────┼────────────────────┼─────────────────────┼─────────────────────────┘   │
│               │                    │                     │                             │
│               └────────────────────┼─────────────────────┘                             │
│                                    ▼                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              API GATEWAY TIER                                    │   │
│  │                                                                                  │   │
│  │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│  │   │                    AWS Application Load Balancer                        │   │   │
│  │   │              + AWS WAF (Rate Limiting, OWASP Rules)                     │   │   │
│  │   └────────────────────────────────┬────────────────────────────────────────┘   │   │
│  │                                    │                                            │   │
│  └────────────────────────────────────┼────────────────────────────────────────────┘   │
│                                       ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              APPLICATION TIER                                    │   │
│  │                                                                                  │   │
│  │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│  │   │                     MCP SERVER (FastAPI)                                │   │   │
│  │   │                         Port: 8000                                      │   │   │
│  │   │                                                                         │   │   │
│  │   │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │   │   │
│  │   │   │ Authentication│  │ MCP Protocol │  │   Admin      │                 │   │   │
│  │   │   │   Module     │  │   Handler    │  │   Module     │                 │   │   │
│  │   │   │  (OAuth2/JWT)│  │(Tools/Execute)│  │ (Settings)   │                 │   │   │
│  │   │   └──────────────┘  └──────────────┘  └──────────────┘                 │   │   │
│  │   │                                                                         │   │   │
│  │   │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │   │   │
│  │   │   │ Tool Registry│  │ Policy Engine│  │   Audit      │                 │   │   │
│  │   │   │  & Router    │  │   (OPA)      │  │   Service    │                 │   │   │
│  │   │   └──────────────┘  └──────────────┘  └──────────────┘                 │   │   │
│  │   │                                                                         │   │   │
│  │   └─────────────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                                  │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
│                                       │                                                │
│  ┌────────────────────────────────────┼────────────────────────────────────────────┐   │
│  │                              DATA TIER                                          │   │
│  │                                    │                                            │   │
│  │   ┌──────────────┐    ┌───────────▼──────┐    ┌──────────────┐                 │   │
│  │   │  PostgreSQL  │    │      Redis       │    │   S3 WORM    │                 │   │
│  │   │   (RDS)      │    │  (ElastiCache)   │    │  Audit Logs  │                 │   │
│  │   │              │    │                  │    │              │                 │   │
│  │   │ - Tools      │    │ - Sessions       │    │ - Immutable  │                 │   │
│  │   │ - Audit Logs │    │ - Rate Limits    │    │ - Compliant  │                 │   │
│  │   │ - Users      │    │ - Idempotency    │    │ - Encrypted  │                 │   │
│  │   │ - Policies   │    │ - Cache          │    │              │                 │   │
│  │   └──────────────┘    └──────────────────┘    └──────────────┘                 │   │
│  │                                                                                  │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Integration with MSIL API Manager

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         MCP SERVER ↔ MSIL APIM INTEGRATION                              │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           MCP SERVER                                            │   │
│   │                                                                                 │   │
│   │   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                    │   │
│   │   │   OpenAPI   │      │    Tool     │      │    API      │                    │   │
│   │   │   Importer  │─────▶│   Registry  │─────▶│   Gateway   │                    │   │
│   │   │             │      │             │      │   Client    │                    │   │
│   │   └─────────────┘      └─────────────┘      └──────┬──────┘                    │   │
│   │         │                                          │                            │   │
│   │         │ Auto-discover                            │ mTLS + OAuth2             │   │
│   │         │ & validate                               │ + Subscription Key         │   │
│   │         ▼                                          ▼                            │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                               │
│                                         │ HTTPS/mTLS                                    │
│                                         ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        MSIL API MANAGER (Azure APIM)                            │   │
│   │                                                                                 │   │
│   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │                        Developer Portal                                 │   │   │
│   │   │                    (OpenAPI Spec Discovery)                             │   │   │
│   │   └─────────────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                                 │   │
│   │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│   │   │   Dealer     │  │   Service    │  │  Customer    │  │   Vehicle    │      │   │
│   │   │   Domain     │  │   Domain     │  │   Domain     │  │   Domain     │      │   │
│   │   │              │  │              │  │              │  │              │      │   │
│   │   │ • Enquiry    │  │ • Booking    │  │ • Profile    │  │ • Stock      │      │   │
│   │   │ • Follow-up  │  │ • Status     │  │ • History    │  │ • Specs      │      │   │
│   │   │ • Allocation │  │ • Feedback   │  │ • Complaints │  │ • Variants   │      │   │
│   │   └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘      │   │
│   │                                                                                 │   │
│   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │                      Subscription Management                            │   │   │
│   │   │           MCP-Dedicated-Subscription (Isolated Channel)                 │   │   │
│   │   └─────────────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                               │
│                                         ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                         MSIL BACKEND SYSTEMS                                    │   │
│   │                                                                                 │   │
│   │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│   │   │     DMS      │  │   Nexa+      │  │     SAP      │  │   Legacy     │      │   │
│   │   │   (Dealer)   │  │   Arena      │  │   (Finance)  │  │   Systems    │      │   │
│   │   └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘      │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Governance Components

### 4.1 Governance Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              GOVERNANCE ARCHITECTURE                                     │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                          IDENTITY & ACCESS MANAGEMENT                           │   │
│   │                                                                                 │   │
│   │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                     │   │
│   │   │    Azure     │    │   OAuth2/    │    │    Local     │                     │   │
│   │   │     AD       │◀──▶│    OIDC      │◀──▶│    Users     │                     │   │
│   │   │  (MSIL IdP)  │    │   Provider   │    │    (Dev)     │                     │   │
│   │   └──────────────┘    └──────────────┘    └──────────────┘                     │   │
│   │                              │                                                  │   │
│   │                              ▼                                                  │   │
│   │   ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │                     JWT Token (User Claims)                             │   │   │
│   │   │        sub, roles[], permissions[], groups[], elevation_status          │   │   │
│   │   └─────────────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                               │
│                                         ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                            POLICY ENFORCEMENT                                   │   │
│   │                                                                                 │   │
│   │   ┌──────────────────────────────────────────────────────────────────────┐      │   │
│   │   │                    Open Policy Agent (OPA)                           │      │   │
│   │   │                                                                      │      │   │
│   │   │   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │      │   │
│   │   │   │    RBAC    │  │   Tool     │  │    Risk    │  │   Data     │    │      │   │
│   │   │   │  Policies  │  │  Access    │  │   Based    │  │  Masking   │    │      │   │
│   │   │   │            │  │  Policies  │  │  Policies  │  │  Policies  │    │      │   │
│   │   │   └────────────┘  └────────────┘  └────────────┘  └────────────┘    │      │   │
│   │   │                                                                      │      │   │
│   │   └──────────────────────────────────────────────────────────────────────┘      │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                               │
│                                         ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                          PRIVILEGED ACCESS (PIM/PAM)                            │   │
│   │                                                                                 │   │
│   │   ┌──────────────────────────────────────────────────────────────────────┐      │   │
│   │   │                    Elevation Manager                                 │      │   │
│   │   │                                                                      │      │   │
│   │   │  Request ──▶ Validate ──▶ Approve ──▶ Grant ──▶ Time-bound Access   │      │   │
│   │   │                  │           │          │                           │      │   │
│   │   │              Reason     Manager     Token                           │      │   │
│   │   │              Required   Approval    Claims                          │      │   │
│   │   │                                                                      │      │   │
│   │   └──────────────────────────────────────────────────────────────────────┘      │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                               │
│                                         ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              AUDIT & COMPLIANCE                                 │   │
│   │                                                                                 │   │
│   │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                     │   │
│   │   │  PostgreSQL  │    │   S3 WORM    │    │  CloudWatch  │                     │   │
│   │   │   (Audit)    │    │  (Immutable) │    │    Logs      │                     │   │
│   │   │              │    │              │    │              │                     │   │
│   │   │ • Events     │    │ • Tamper-    │    │ • Real-time  │                     │   │
│   │   │ • Decisions  │    │   proof      │    │ • Searchable │                     │   │
│   │   │ • Changes    │    │ • Compliant  │    │ • Alerting   │                     │   │
│   │   └──────────────┘    └──────────────┘    └──────────────┘                     │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Data Flow Diagram

### 5.1 Tool Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              TOOL EXECUTION DATA FLOW                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  User/LLM                MCP Server                  APIM              Backend          │
│  (Host App)                 │                         │                   │             │
│     │                       │                         │                   │             │
│     │  1. Execute Tool      │                         │                   │             │
│     │  (JWT + Parameters)   │   NOTE: Host app calls  │                   │             │
│     ├──────────────────────▶│   MCP, not LLM directly │                   │             │
│     │                       │                         │                   │             │
│     │                       │ 2. Validate JWT         │                   │             │
│     │                       │    (JWKS/OIDC)          │                   │             │
│     │                       ├────────┐                │                   │             │
│     │                       │        │                │                   │             │
│     │                       │◀───────┘                │                   │             │
│     │                       │                         │                   │             │
│     │                       │ 3. Check Idempotency    │                   │             │
│     │                       │    (Redis)              │                   │             │
│     │                       ├────────┐                │                   │             │
│     │                       │        │ Cache Hit?     │                   │             │
│     │                       │◀───────┘                │                   │             │
│     │                       │                         │                   │             │
│     │                       │ 4. Policy Check (OPA)   │                   │             │
│     │                       │    - RBAC               │                   │             │
│     │                       │    - Tool Access        │                   │             │
│     │                       │    - Risk Level         │                   │             │
│     │                       ├────────┐                │                   │             │
│     │                       │        │ Allow/Deny    │                   │             │
│     │                       │◀───────┘                │                   │             │
│     │                       │                         │                   │             │
│     │                       │ 5. PIM Check            │                   │             │
│     │                       │    (If Privileged)      │                   │             │
│     │                       ├────────┐                │                   │             │
│     │                       │        │ Elevated?     │                   │             │
│     │                       │◀───────┘                │                   │             │
│     │                       │                         │                   │             │
│     │                       │ 6. Validate Input       │                   │             │
│     │                       │    (JSON Schema)        │                   │             │
│     │                       ├────────┐                │                   │             │
│     │                       │        │                │                   │             │
│     │                       │◀───────┘                │                   │             │
│     │                       │                         │                   │             │
│     │                       │ 7. API Call             │                   │             │
│     │                       │    (mTLS + Sub Key)     │                   │             │
│     │                       ├────────────────────────▶│                   │             │
│     │                       │                         │                   │             │
│     │                       │                         │ 8. Route to       │             │
│     │                       │                         │    Backend        │             │
│     │                       │                         ├──────────────────▶│             │
│     │                       │                         │                   │             │
│     │                       │                         │ 9. Response       │             │
│     │                       │                         │◀──────────────────┤             │
│     │                       │                         │                   │             │
│     │                       │ 10. Response            │                   │             │
│     │                       │◀────────────────────────┤                   │             │
│     │                       │                         │                   │             │
│     │                       │ 11. Mask PII            │                   │             │
│     │                       │     (If Configured)     │                   │             │
│     │                       ├────────┐                │                   │             │
│     │                       │        │                │                   │             │
│     │                       │◀───────┘                │                   │             │
│     │                       │                         │                   │             │
│     │                       │ 12. Store Idempotency   │                   │             │
│     │                       │     (Redis)             │                   │             │
│     │                       ├────────┐                │                   │             │
│     │                       │        │                │                   │             │
│     │                       │◀───────┘                │                   │             │
│     │                       │                         │                   │             │
│     │                       │ 13. Audit Log           │                   │             │
│     │                       │     (DB + S3 WORM)      │                   │             │
│     │                       ├────────┐                │                   │             │
│     │                       │        │                │                   │             │
│     │                       │◀───────┘                │                   │             │
│     │                       │                         │                   │             │
│     │ 14. Return Result     │                         │                   │             │
│     │◀──────────────────────┤                         │                   │             │
│     │                       │                         │                   │             │
│     ▼                       ▼                         ▼                   ▼             │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **FastAPI (Python)** | High performance async framework, OpenAPI native support |
| **PostgreSQL** | ACID compliance, JSON support, enterprise reliability |
| **Redis** | Sub-millisecond latency for rate limiting, sessions |
| **OPA** | Declarative policies, decoupled from application code |
| **S3 Object Lock** | Regulatory compliance for immutable audit trails |
| **mTLS** | Zero-trust service-to-service authentication |
| **Kubernetes** | Container orchestration, auto-scaling, self-healing |

---

## 7. Non-Functional Requirements

| Requirement | Target | Implementation |
|-------------|--------|----------------|
| **Availability** | 99.9% | Multi-AZ deployment, health checks |
| **Latency** | < 200ms (p99) | Redis caching, connection pooling |
| **Throughput** | 1000 req/sec | Horizontal scaling, async processing |
| **Recovery** | RTO: 1hr, RPO: 5min | Automated backups, DR strategy |
| **Security** | Zero-trust | mTLS, WAF, RBAC, encryption |

---

## 8. Next Steps

1. Review [Low-Level Technical Architecture](./02-low-level-architecture.md) for component details
2. Review [Security Architecture](./03-security-architecture.md) for security controls
3. Review [Deployment Architecture](./04-deployment-architecture.md) for infrastructure

---

*Document Classification: Internal | Last Review: February 1, 2026*
