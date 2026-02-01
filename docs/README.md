# MSIL MCP Platform Documentation

**Version**: 2.0  
**Date**: January 31, 2026  
**Classification**: Internal  
**Author**: Nagarro Development Team

---

## Document Index

This documentation suite provides comprehensive coverage of the MSIL Model Context Protocol (MCP) Server Platform, designed to enable secure, governed AI/LLM access to enterprise APIs.

### 📋 Table of Contents

#### Architecture Documents
| # | Document | Description |
|---|----------|-------------|
| 1 | [Architecture Overview](./architecture/README.md) | Complete architecture documentation index |
| 2 | [High-Level Architecture](./architecture/01-high-level-architecture.md) | System context, logical view, topology |
| 3 | [Low-Level Architecture](./architecture/02-low-level-architecture.md) | Component-level design, tool registry, routing |
| 4 | [Security Architecture](./architecture/03-security-architecture.md) | IAM, RBAC, PIM/PAM, guardrails |
| 5 | [Deployment Architecture](./architecture/04-deployment-architecture.md) | AWS, Kubernetes, CI/CD, DR |
| 6 | [Integration Architecture](./architecture/05-integration-architecture.md) | APIM, Azure AD, OPA connectivity |

#### MCP Artefacts
| # | Document | Description |
|---|----------|-------------|
| 7 | [MCP Tool Definition](./artefacts/01-mcp-tool-definition.md) | Tool schema, OpenAPI derivation, examples |
| 8 | [Composite Server](./artefacts/02-composite-server.md) | Server architecture, protocol, configuration |

#### Operations & Development
| # | Document | Description |
|---|----------|-------------|
| 9 | [DevSecOps Guide](./devsecops/README.md) | CI/CD pipelines, security scanning, testing |
| 10 | [Observability Guide](./observability/README.md) | Logging, metrics, tracing, dashboards |
| 11 | [API Reference](./api/README.md) | REST API documentation, endpoints, examples |
| 12 | [Operations Runbook](./operations/README.md) | Deployment, incident response, maintenance |

#### Governance & Project
| # | Document | Description |
|---|----------|-------------|
| 13 | [Team Structure](./governance/01-team-structure.md) | Organization, roles, RACI matrix |
| 14 | [Governance Templates](./governance/02-templates.md) | Change, incident, release templates |
| 15 | [Product Selection](./governance/03-product-selection.md) | Technology evaluation, MCP rationale |
| 16 | [Implementation Roadmap](./project/01-roadmap.md) | WBS, sprints, milestones |

#### Security & Compliance
| # | Document | Description |
|---|----------|-------------|
| 17 | [Security Framework](./security/README.md) | Policies, standards, controls, DPDP |

#### Support & Infrastructure
| # | Document | Description |
|---|----------|-------------|
| 18 | [Support & SLA](./support/README.md) | SLAs, incident management, escalation |
| 19 | [Infrastructure BOM](./infrastructure/01-bom.md) | AWS resources, costs, software inventory |

---

## Platform Overview

### What is MSIL MCP Server?

The MSIL MCP (Model Context Protocol) Server is an enterprise-grade platform that enables Large Language Models (LLMs) to securely interact with Maruti Suzuki's internal APIs through a standardized, governed protocol. 

### Key Capabilities

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MSIL MCP Platform Capabilities                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🔌 API Integration        │  🔐 Security & Governance             │
│  ├─ OpenAPI auto-import    │  ├─ OAuth2/OIDC authentication       │
│  ├─ Dynamic tool creation  │  ├─ RBAC + OPA policies              │
│  ├─ APIM connectivity      │  ├─ PIM/PAM elevation                │
│  └─ Schema validation      │  └─ Prompt injection guards          │
│                            │                                       │
│  📊 Observability          │  🚀 Enterprise Features              │
│  ├─ Structured logging     │  ├─ Circuit breaker resilience       │
│  ├─ Metrics & dashboards   │  ├─ Rate limiting                    │
│  ├─ Distributed tracing    │  ├─ Batch execution                  │
│  └─ WORM audit trails      │  └─ Multi-tenant support             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | Python 3.13 + FastAPI | High-performance async API server |
| **Frontend** | React 18 + TypeScript | Admin Portal & Chat UI |
| **Database** | PostgreSQL 16 | Persistent data storage |
| **Cache** | Redis 7 | Session, rate limiting, idempotency |
| **Policy** | Open Policy Agent | RBAC enforcement |
| **Container** | Docker + Kubernetes | Deployment orchestration |
| **Cloud** | AWS | Infrastructure hosting |
| **API Gateway** | AWS API Gateway + MSIL APIM | API management |

---

## Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 16
- Redis 7

### Local Development
```bash
# Clone repository
git clone https://github.com/msil/mcp-server.git
cd mcp-server

# Start backend
cd mcp-server
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Start frontend (separate terminal)
cd admin-ui
npm install
npm run dev
```

### Docker Deployment
```bash
# Production deployment
docker-compose -f docker-compose.hardened.yml up -d
```

---

## Document Conventions

### Classification Levels
- **Public**: Can be shared externally
- **Internal**: MSIL employees only
- **Confidential**: Need-to-know basis
- **Restricted**: Authorized personnel only

### Version Control
All documentation follows semantic versioning (MAJOR.MINOR.PATCH) aligned with platform releases.

### Feedback
For documentation improvements, contact: mcp-platform@nagarro.com

---

## Compliance & Standards

This platform is designed to comply with:
- **DPDP Act 2023** (Digital Personal Data Protection)
- **GDPR** (General Data Protection Regulation)
- **SOC 2 Type II** (Security controls)
- **ISO 27001** (Information security)
- **CIS Benchmarks** (Container security)

---

*© 2026 Nagarro. All rights reserved.*
