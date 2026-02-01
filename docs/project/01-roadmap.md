# Implementation Roadmap & WBS

**Document Version**: 2.0  
**Last Updated**: January 31, 2026  
**Classification**: Internal

---

## 1. Project Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PROJECT TIMELINE OVERVIEW                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Phase 1: Foundation          Phase 2: Core Dev       Phase 3: Hardening│
│  ┌────────────────────┐      ┌────────────────────┐  ┌─────────────────┐│
│  │ Weeks 1-4          │      │ Weeks 5-12         │  │ Weeks 13-16     ││
│  │ • Requirements     │      │ • MCP Server       │  │ • Security      ││
│  │ • Architecture     │  ──► │ • Admin Portal     │──►│ • Performance   ││
│  │ • Infrastructure   │      │ • Chat UI          │  │ • Documentation ││
│  │ • CI/CD Setup      │      │ • Integrations     │  │ • UAT           ││
│  └────────────────────┘      └────────────────────┘  └─────────────────┘│
│                                                                          │
│  Phase 4: Launch             Phase 5: Stabilization                     │
│  ┌────────────────────┐      ┌────────────────────┐                     │
│  │ Weeks 17-18        │      │ Weeks 19-24        │                     │
│  │ • Pilot Deployment │      │ • Monitoring       │                     │
│  │ • Training         │  ──► │ • Optimization     │                     │
│  │ • Go-Live          │      │ • Handover         │                     │
│  └────────────────────┘      └────────────────────┘                     │
│                                                                          │
│  Total Duration: 24 Weeks (6 Months)                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Work Breakdown Structure (WBS)

### Level 1: Project Phases

```
1.0 MSIL MCP Platform
├── 1.1 Foundation & Setup
├── 1.2 Core Development
├── 1.3 Security Hardening
├── 1.4 Testing & Quality
├── 1.5 Deployment & Launch
└── 1.6 Stabilization & Handover
```

### Level 2-3: Detailed WBS

```
1.0 MSIL MCP Platform
│
├── 1.1 Foundation & Setup (Weeks 1-4)
│   ├── 1.1.1 Requirements & Design
│   │   ├── 1.1.1.1 Requirements gathering workshops
│   │   ├── 1.1.1.2 Business process documentation
│   │   ├── 1.1.1.3 Tool inventory analysis
│   │   └── 1.1.1.4 Requirements sign-off
│   │
│   ├── 1.1.2 Architecture Design
│   │   ├── 1.1.2.1 High-level architecture
│   │   ├── 1.1.2.2 Low-level design
│   │   ├── 1.1.2.3 Security architecture
│   │   ├── 1.1.2.4 Integration architecture
│   │   └── 1.1.2.5 Architecture review & approval
│   │
│   ├── 1.1.3 Infrastructure Setup
│   │   ├── 1.1.3.1 AWS account configuration
│   │   ├── 1.1.3.2 VPC & networking setup
│   │   ├── 1.1.3.3 EKS cluster provisioning
│   │   ├── 1.1.3.4 RDS PostgreSQL setup
│   │   ├── 1.1.3.5 ElastiCache Redis setup
│   │   └── 1.1.3.6 S3 buckets configuration
│   │
│   └── 1.1.4 Development Environment
│       ├── 1.1.4.1 CI/CD pipeline setup
│       ├── 1.1.4.2 Container registry setup
│       ├── 1.1.4.3 Development tools setup
│       └── 1.1.4.4 Local dev environment guide
│
├── 1.2 Core Development (Weeks 5-12)
│   ├── 1.2.1 MCP Server Backend
│   │   ├── 1.2.1.1 FastAPI application scaffold
│   │   ├── 1.2.1.2 MCP protocol implementation
│   │   ├── 1.2.1.3 Tool registry & management
│   │   ├── 1.2.1.4 OpenAPI import functionality
│   │   ├── 1.2.1.5 Parameter validation engine
│   │   ├── 1.2.1.6 Backend routing & dispatch
│   │   ├── 1.2.1.7 Response transformation
│   │   └── 1.2.1.8 Error handling framework
│   │
│   ├── 1.2.2 Authentication & Authorization
│   │   ├── 1.2.2.1 OAuth2/OIDC integration
│   │   ├── 1.2.2.2 JWKS validation with caching
│   │   ├── 1.2.2.3 OPA policy engine integration
│   │   ├── 1.2.2.4 Role-based access control
│   │   ├── 1.2.2.5 Tool-level permissions
│   │   └── 1.2.2.6 Session management
│   │
│   ├── 1.2.3 Admin Portal
│   │   ├── 1.2.3.1 React application scaffold
│   │   ├── 1.2.3.2 Authentication UI
│   │   ├── 1.2.3.3 Tool management screens
│   │   ├── 1.2.3.4 User management screens
│   │   ├── 1.2.3.5 Audit log viewer
│   │   ├── 1.2.3.6 Dashboard & analytics
│   │   └── 1.2.3.7 Settings management
│   │
│   ├── 1.2.4 Chat UI
│   │   ├── 1.2.4.1 Chat interface scaffold
│   │   ├── 1.2.4.2 Message input & display
│   │   ├── 1.2.4.3 Tool execution visualization
│   │   ├── 1.2.4.4 Session management
│   │   └── 1.2.4.5 User preferences
│   │
│   ├── 1.2.5 APIM Integration
│   │   ├── 1.2.5.1 mTLS certificate setup
│   │   ├── 1.2.5.2 APIM connectivity layer
│   │   ├── 1.2.5.3 Circuit breaker implementation
│   │   ├── 1.2.5.4 Retry policies
│   │   └── 1.2.5.5 Health monitoring
│   │
│   └── 1.2.6 Observability
│       ├── 1.2.6.1 Structured logging
│       ├── 1.2.6.2 CloudWatch integration
│       ├── 1.2.6.3 X-Ray distributed tracing
│       ├── 1.2.6.4 Metrics & dashboards
│       └── 1.2.6.5 Alerting setup
│
├── 1.3 Security Hardening (Weeks 13-14)
│   ├── 1.3.1 P0 Critical Security
│   │   ├── 1.3.1.1 JWKS validation enhancement
│   │   ├── 1.3.1.2 Idempotency key implementation
│   │   ├── 1.3.1.3 PIM/PAM integration
│   │   └── 1.3.1.4 S3 WORM audit store
│   │
│   ├── 1.3.2 P1 High Priority Security
│   │   ├── 1.3.2.1 WAF configuration
│   │   ├── 1.3.2.2 mTLS enforcement
│   │   ├── 1.3.2.3 Tool risk classification
│   │   └── 1.3.2.4 APIM subscription keys
│   │
│   ├── 1.3.3 P2 Medium Priority Security
│   │   ├── 1.3.3.1 Container hardening
│   │   ├── 1.3.3.2 Security test suite
│   │   ├── 1.3.3.3 Network policies
│   │   └── 1.3.3.4 Container scanning
│   │
│   └── 1.3.4 Compliance
│       ├── 1.3.4.1 DPDP compliance review
│       ├── 1.3.4.2 Data classification
│       └── 1.3.4.3 Privacy impact assessment
│
├── 1.4 Testing & Quality (Weeks 15-16)
│   ├── 1.4.1 Test Development
│   │   ├── 1.4.1.1 Unit test suite
│   │   ├── 1.4.1.2 Integration test suite
│   │   ├── 1.4.1.3 E2E test suite
│   │   └── 1.4.1.4 Performance test suite
│   │
│   ├── 1.4.2 Security Testing
│   │   ├── 1.4.2.1 SAST execution
│   │   ├── 1.4.2.2 DAST execution
│   │   ├── 1.4.2.3 Penetration testing
│   │   └── 1.4.2.4 Vulnerability remediation
│   │
│   ├── 1.4.3 UAT
│   │   ├── 1.4.3.1 UAT environment setup
│   │   ├── 1.4.3.2 UAT test case development
│   │   ├── 1.4.3.3 UAT execution
│   │   └── 1.4.3.4 UAT sign-off
│   │
│   └── 1.4.4 Documentation
│       ├── 1.4.4.1 Architecture documentation
│       ├── 1.4.4.2 API documentation
│       ├── 1.4.4.3 Operations runbook
│       └── 1.4.4.4 User guides
│
├── 1.5 Deployment & Launch (Weeks 17-18)
│   ├── 1.5.1 Pilot Deployment
│   │   ├── 1.5.1.1 Production environment setup
│   │   ├── 1.5.1.2 Data migration
│   │   ├── 1.5.1.3 Pilot user onboarding
│   │   └── 1.5.1.4 Pilot monitoring
│   │
│   ├── 1.5.2 Training
│   │   ├── 1.5.2.1 Admin training
│   │   ├── 1.5.2.2 User training
│   │   ├── 1.5.2.3 Ops team training
│   │   └── 1.5.2.4 Training materials
│   │
│   └── 1.5.3 Go-Live
│       ├── 1.5.3.1 Go-live checklist
│       ├── 1.5.3.2 Production deployment
│       ├── 1.5.3.3 Go-live verification
│       └── 1.5.3.4 Hypercare support
│
└── 1.6 Stabilization & Handover (Weeks 19-24)
    ├── 1.6.1 Monitoring & Optimization
    │   ├── 1.6.1.1 Performance monitoring
    │   ├── 1.6.1.2 Cost optimization
    │   └── 1.6.1.3 Capacity planning
    │
    ├── 1.6.2 Knowledge Transfer
    │   ├── 1.6.2.1 Technical documentation review
    │   ├── 1.6.2.2 KT sessions
    │   └── 1.6.2.3 Handover sign-off
    │
    └── 1.6.3 Support Transition
        ├── 1.6.3.1 Support process setup
        ├── 1.6.3.2 Runbook review
        └── 1.6.3.3 Support SLA activation
```

---

## 3. Sprint Plan

### Phase 1: Foundation (Sprints 1-2)

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| **Sprint 1** | Requirements & Architecture | Requirements doc, HLD, LLD |
| **Sprint 2** | Infrastructure Setup | AWS infra, CI/CD, dev env |

### Phase 2: Core Development (Sprints 3-6)

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| **Sprint 3** | MCP Backend Core | FastAPI scaffold, MCP protocol, tool registry |
| **Sprint 4** | Auth & Backend Integration | OAuth2, JWKS, OPA, APIM connectivity |
| **Sprint 5** | Admin Portal | Tool management, user management, audit viewer |
| **Sprint 6** | Chat UI & Observability | Chat interface, logging, tracing, dashboards |

### Phase 3: Security Hardening (Sprints 7-8)

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| **Sprint 7** | P0 & P1 Security | JWKS, idempotency, PIM/PAM, S3 WORM, WAF, mTLS |
| **Sprint 8** | P2 Security & Compliance | Container hardening, security tests, DPDP |

### Phase 4: Testing & Quality (Sprint 9)

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| **Sprint 9** | Testing & Documentation | Test suites, pen test, UAT, documentation |

### Phase 5: Launch (Sprint 10)

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| **Sprint 10** | Pilot & Go-Live | Pilot deployment, training, go-live |

### Phase 6: Stabilization (Sprints 11-12)

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| **Sprint 11** | Stabilization | Performance tuning, cost optimization |
| **Sprint 12** | Handover | KT, documentation, support transition |

---

## 4. Milestones

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PROJECT MILESTONES                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Week 2  ───► M1: Requirements Sign-off                                 │
│                                                                          │
│  Week 4  ───► M2: Architecture Approved & Infra Ready                   │
│                                                                          │
│  Week 8  ───► M3: MCP Backend MVP Complete                              │
│                                                                          │
│  Week 12 ───► M4: All UI Components Complete                            │
│                                                                          │
│  Week 14 ───► M5: Security Hardening Complete                           │
│                                                                          │
│  Week 16 ───► M6: UAT Sign-off                                          │
│                                                                          │
│  Week 18 ───► M7: Production Go-Live ★                                  │
│                                                                          │
│  Week 24 ───► M8: Project Closure & Handover                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

| Milestone | Date | Criteria | Owner |
|-----------|------|----------|-------|
| **M1** | Week 2 | All requirements documented and signed off | Product Owner |
| **M2** | Week 4 | HLD/LLD approved, AWS infra provisioned, CI/CD working | Tech Architect |
| **M3** | Week 8 | MCP server can execute tools, auth working | Tech Lead |
| **M4** | Week 12 | Admin portal and chat UI feature complete | Tech Lead |
| **M5** | Week 14 | All P0/P1/P2 security items implemented | Security Lead |
| **M6** | Week 16 | UAT passed, all critical bugs fixed | QA Lead |
| **M7** | Week 18 | Production deployment successful, go-live approved | Project Manager |
| **M8** | Week 24 | KT complete, support transition done | Project Manager |

---

## 5. Dependencies

### 5.1 Internal Dependencies

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DEPENDENCY MATRIX                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Task                          │ Depends On                             │
│  ─────────────────────────────────────────────────────────────────────  │
│  MCP Server Development        │ Architecture approval, Infra setup     │
│  Admin Portal Development      │ MCP Server APIs available              │
│  Chat UI Development           │ MCP Server APIs available              │
│  APIM Integration              │ mTLS certificates, APIM access         │
│  Security Hardening            │ Core development complete              │
│  UAT                           │ All development complete               │
│  Production Deployment         │ UAT sign-off, security approval        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 External Dependencies

| Dependency | Owner | Required By | Status |
|------------|-------|-------------|--------|
| AWS account provisioning | MSIL IT | Week 1 | Pending |
| Azure AD app registration | MSIL IT | Week 3 | Pending |
| APIM access & endpoints | MSIL IT | Week 5 | Pending |
| mTLS certificates | MSIL Security | Week 5 | Pending |
| PIM/PAM configuration | MSIL Security | Week 7 | Pending |
| Network connectivity | MSIL IT | Week 4 | Pending |
| Tool API documentation | MSIL Business | Week 3 | Pending |

---

## 6. Resource Plan

### 6.1 Team Allocation by Phase

| Phase | Architect | Tech Lead | Backend | Frontend | DevOps | Security | QA |
|-------|-----------|-----------|---------|----------|--------|----------|----|
| Foundation | 50% | 100% | 50% | 0% | 100% | 25% | 0% |
| Core Dev | 25% | 100% | 100% | 100% | 50% | 25% | 50% |
| Security | 25% | 100% | 50% | 25% | 50% | 100% | 50% |
| Testing | 10% | 50% | 50% | 25% | 25% | 50% | 100% |
| Launch | 25% | 100% | 50% | 25% | 100% | 50% | 50% |
| Stabilization | 10% | 50% | 25% | 10% | 50% | 25% | 25% |

### 6.2 Effort Estimation

| Phase | Duration | Total Effort (Person-Days) |
|-------|----------|----------------------------|
| Foundation | 4 weeks | 120 |
| Core Development | 8 weeks | 400 |
| Security Hardening | 2 weeks | 80 |
| Testing & Quality | 2 weeks | 100 |
| Deployment & Launch | 2 weeks | 80 |
| Stabilization | 6 weeks | 120 |
| **Total** | **24 weeks** | **900 person-days** |

---

## 7. Risk Register

| Risk | Impact | Probability | Mitigation | Owner |
|------|--------|-------------|------------|-------|
| APIM access delayed | High | Medium | Early engagement, mock APIs | PM |
| Resource unavailability | High | Low | Cross-training, buffer | PM |
| Security requirements change | Medium | Medium | Weekly security sync | Security Lead |
| Performance issues | High | Medium | Early performance testing | Tech Lead |
| Scope creep | High | High | Strict change control | Product Owner |
| Integration complexity | Medium | Medium | PoC early, iterative approach | Tech Architect |

---

## 8. Quality Gates

### 8.1 Phase Exit Criteria

| Phase | Exit Criteria |
|-------|---------------|
| **Foundation** | HLD/LLD approved, Infra verified, CI/CD working |
| **Core Dev** | All features developed, code reviewed, unit tests >80% |
| **Security** | All P0/P1/P2 items closed, pen test passed |
| **Testing** | UAT passed, no critical/high bugs open |
| **Launch** | Go-live checklist complete, stakeholder approval |
| **Stabilization** | SLAs met, KT complete, support transition done |

### 8.2 Definition of Done

```
□ Code complete and committed
□ Unit tests written and passing (>80% coverage)
□ Code review approved
□ Integration tests passing
□ Security scan passing (no high/critical findings)
□ Documentation updated
□ Deployed to staging
□ Product Owner demo and acceptance
```

---

## 9. Communication Plan

| Communication | Frequency | Audience | Owner |
|---------------|-----------|----------|-------|
| Daily Standup | Daily | Dev Team | Tech Lead |
| Sprint Review | Bi-weekly | All + MSIL | Tech Lead |
| Status Report | Weekly | Stakeholders | PM |
| Steering Committee | Monthly | Leadership | PM |
| Risk Review | Bi-weekly | Leadership | PM |
| Security Review | Weekly | Security Team | Security Lead |

---

*Document Classification: Internal | Last Review: January 31, 2026*
