# Support & SLA Management

**Document Version**: 2.0  
**Last Updated**: January 31, 2026  
**Classification**: Internal

---

## 1. Support Model Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       SUPPORT MODEL STRUCTURE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                        USERS / CLIENTS                          │    │
│  └──────────────────────────────┬──────────────────────────────────┘    │
│                                 │                                        │
│                                 ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    LEVEL 1: SERVICE DESK                        │    │
│  │  • First point of contact                                       │    │
│  │  • Incident logging & categorization                            │    │
│  │  • Known issue resolution                                       │    │
│  │  • User guidance & FAQ                                          │    │
│  │  Response: 15 minutes                                           │    │
│  └──────────────────────────────┬──────────────────────────────────┘    │
│                                 │ Escalate                              │
│                                 ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    LEVEL 2: APPLICATION SUPPORT                 │    │
│  │  • Technical troubleshooting                                    │    │
│  │  • Configuration changes                                        │    │
│  │  • Performance investigation                                    │    │
│  │  • Minor bug fixes                                              │    │
│  │  Response: 30 minutes                                           │    │
│  └──────────────────────────────┬──────────────────────────────────┘    │
│                                 │ Escalate                              │
│                                 ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    LEVEL 3: ENGINEERING SUPPORT                 │    │
│  │  • Complex technical issues                                     │    │
│  │  • Code-level debugging                                         │    │
│  │  • Architecture issues                                          │    │
│  │  • Major enhancements                                           │    │
│  │  Response: 2 hours                                              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Service Level Agreements (SLA)

### 2.1 Availability SLA

| Service | Target | Measurement Period | Exclusions |
|---------|--------|-------------------|------------|
| MCP Server | 99.9% | Monthly | Planned maintenance |
| Admin Portal | 99.5% | Monthly | Planned maintenance |
| Chat UI | 99.5% | Monthly | Planned maintenance |
| Database | 99.95% | Monthly | AWS RDS SLA |

#### Availability Calculation

```
Availability % = ((Total Minutes - Downtime Minutes) / Total Minutes) × 100

Monthly Target: 99.9%
Allowed Downtime: 43.8 minutes/month (99.9%)
                  3.65 hours/month (99.5%)
```

### 2.2 Response Time SLA

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RESPONSE TIME MATRIX                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Severity │ Description           │ Response  │ Resolution │ Escalation │
│  ─────────┼───────────────────────┼───────────┼────────────┼────────────│
│  P1       │ Complete outage       │ 15 min    │ 4 hours    │ Immediate  │
│  Critical │ No workaround         │           │            │            │
│           │                       │           │            │            │
│  P2       │ Major degradation     │ 30 min    │ 8 hours    │ 1 hour     │
│  High     │ Limited workaround    │           │            │            │
│           │                       │           │            │            │
│  P3       │ Partial impact        │ 2 hours   │ 3 days     │ 4 hours    │
│  Medium   │ Workaround available  │           │            │            │
│           │                       │           │            │            │
│  P4       │ Minor issue           │ 8 hours   │ 10 days    │ 24 hours   │
│  Low      │ Cosmetic/enhancement  │           │            │            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Performance SLA

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time (P95) | <500ms | CloudWatch |
| Tool Execution Time (P95) | <5s | CloudWatch |
| Page Load Time | <3s | Synthetic monitoring |
| Throughput | 100 req/sec | Load testing |
| Error Rate | <1% | CloudWatch |

### 2.4 Support Hours

| Level | Coverage | Hours | Contact |
|-------|----------|-------|---------|
| L1 Service Desk | Business hours | Mon-Fri 09:00-18:00 IST | Teams/Email |
| L2 Application | Extended hours | Mon-Sat 08:00-20:00 IST | Teams/Phone |
| L3 Engineering | On-call | 24/7 for P1/P2 | PagerDuty |
| Security | On-call | 24/7 | PagerDuty |

---

## 3. Incident Management

### 3.1 Incident Classification

| Category | Description | Examples |
|----------|-------------|----------|
| **Service Outage** | Complete service unavailable | MCP server down, DB unreachable |
| **Performance** | Degraded performance | Slow responses, timeouts |
| **Functionality** | Feature not working | Tool execution failure |
| **Security** | Security-related incident | Unauthorized access, breach |
| **Data** | Data integrity issues | Missing data, corruption |
| **Integration** | External integration failure | APIM connectivity issues |

### 3.2 Incident Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      INCIDENT MANAGEMENT FLOW                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐            │
│   │  DETECT  │──►│  TRIAGE  │──►│  ASSIGN  │──►│ DIAGNOSE │            │
│   └──────────┘   └──────────┘   └──────────┘   └──────────┘            │
│                                                      │                   │
│                                                      ▼                   │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐            │
│   │  CLOSE   │◄──│  VERIFY  │◄──│ RESOLVE  │◄──│ ESCALATE │            │
│   └──────────┘   └──────────┘   └──────────┘   └──────────┘            │
│        │                                                                 │
│        ▼                                                                 │
│   ┌──────────┐                                                          │
│   │  REVIEW  │ ───► Post-Incident Report (PIR)                          │
│   └──────────┘                                                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Escalation Matrix

| Severity | Time Elapsed | Escalation Level | Contact |
|----------|--------------|------------------|---------|
| **P1** | 0 min | L2 + L3 + Management | Tech Lead, PM |
| | 30 min | VP Engineering | VP Eng |
| | 2 hours | Executive | CTO |
| **P2** | 0 min | L2 | On-call engineer |
| | 1 hour | L3 | Tech Lead |
| | 4 hours | Management | PM |
| **P3** | 0 min | L2 | Support engineer |
| | 4 hours | L3 | Senior engineer |
| | 24 hours | Management | PM |
| **P4** | 0 min | L1 | Service desk |
| | 24 hours | L2 | Support engineer |

---

## 4. Problem Management

### 4.1 Problem Identification

| Source | Description |
|--------|-------------|
| Recurring Incidents | Same incident 3+ times in 30 days |
| Trend Analysis | Increasing error patterns |
| Proactive Monitoring | Anomaly detection alerts |
| User Feedback | Reported chronic issues |

### 4.2 Root Cause Analysis (RCA) Template

```
Problem ID: PRB-2026-XXX
Related Incidents: INC-2026-XXX, INC-2026-YYY

1. Problem Statement
   - What happened?
   - When did it start?
   - What was the impact?

2. Timeline
   - Event sequence with timestamps

3. Root Cause Analysis
   - 5 Whys analysis
   - Contributing factors
   - Root cause identification

4. Resolution
   - Immediate fix applied
   - Permanent fix planned

5. Preventive Actions
   - Process improvements
   - Technical changes
   - Monitoring additions

6. Lessons Learned
   - What went well
   - What could improve
```

---

## 5. Change Management

### 5.1 Change Categories

| Category | Description | Approval | Lead Time |
|----------|-------------|----------|-----------|
| **Standard** | Pre-approved, low risk | Auto | 1 day |
| **Normal** | Medium risk, planned | CAB | 5 days |
| **Major** | High risk, significant | CAB + Exec | 14 days |
| **Emergency** | Critical fix needed | Tech Lead | Immediate |

### 5.2 Change Advisory Board (CAB)

| Member | Role | Voting |
|--------|------|--------|
| Product Owner (MSIL) | Business approval | Yes |
| Tech Lead (Nagarro) | Technical approval | Yes |
| Security Lead | Security review | Yes |
| DevOps Lead | Deployment review | Yes |
| PM | Coordination | No |

### 5.3 Change Request Process

```
Request → Review → Approve/Reject → Schedule → Implement → Verify → Close
   │         │          │              │           │          │
   │         │          │              │           │          └─► PIR if issues
   │         │          │              │           │
   │         │          │              │           └─► Rollback if failed
   │         │          │              │
   │         │          │              └─► Change window
   │         │          │
   │         │          └─► Reject → Notify requestor
   │         │
   │         └─► CAB review (Normal/Major)
   │
   └─► Auto-approve (Standard)
```

---

## 6. Service Requests

### 6.1 Common Service Requests

| Request Type | SLA | Approver |
|--------------|-----|----------|
| New user access | 2 business days | Manager + Security |
| Role change | 2 business days | Manager |
| Access removal | 1 business day | Auto (on termination) |
| New tool registration | 5 business days | Tech Lead + Security |
| Tool modification | 3 business days | Tech Lead |
| Password reset | 4 hours | Self-service + MFA |
| Report request | 3 business days | Product Owner |

### 6.2 Service Catalog

| Service | Description | Request Channel |
|---------|-------------|-----------------|
| User Onboarding | New user setup | Jira ticket |
| Access Management | Role/permission changes | Jira ticket |
| Tool Management | New/modify tools | Jira ticket |
| Report Generation | Custom reports | Email/Jira |
| Training | User/admin training | Email |
| Documentation | Documentation updates | Jira/Confluence |

---

## 7. Support Metrics & Reporting

### 7.1 Key Performance Indicators

| KPI | Target | Measurement | Frequency |
|-----|--------|-------------|-----------|
| First Response Time | Per SLA | Time from creation to first response | Daily |
| Resolution Time | Per SLA | Time from creation to resolution | Daily |
| SLA Compliance | >95% | % of tickets meeting SLA | Weekly |
| First Call Resolution | >40% | % resolved at L1 | Weekly |
| Customer Satisfaction | >4.0/5.0 | Post-ticket survey | Monthly |
| Ticket Backlog | <20 | Open tickets older than SLA | Daily |
| Reopen Rate | <5% | % of tickets reopened | Monthly |

### 7.2 Reporting Schedule

| Report | Frequency | Audience | Content |
|--------|-----------|----------|---------|
| Daily Operations | Daily | Support Team | Open tickets, P1/P2 status |
| Weekly Status | Weekly | PM, Tech Lead | Metrics, trends, issues |
| Monthly Service | Monthly | Steering Committee | SLA performance, incidents |
| Quarterly Review | Quarterly | Executives | Service health, improvements |

### 7.3 Dashboard Metrics

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     SUPPORT DASHBOARD                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  Open Tickets   │  │  SLA Compliance │  │  MTTR (P1/P2)   │         │
│  │      12         │  │      97.5%      │  │    3.2 hours    │         │
│  │   ↓ from 15     │  │   ↑ from 95%    │  │   ↓ from 4.1h   │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  P1 Incidents   │  │  Availability   │  │     CSAT        │         │
│  │       0         │  │     99.95%      │  │    4.3/5.0      │         │
│  │   → stable      │  │   ↑ from 99.9%  │  │   ↑ from 4.1    │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│                                                                          │
│  Ticket Trend (Last 30 Days)                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Created  ████████████████████████  48                            │   │
│  │ Resolved ██████████████████████████  52                          │   │
│  │ Open     ████████  12                                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Communication Channels

### 8.1 Support Channels

| Channel | Purpose | Response SLA | Hours |
|---------|---------|--------------|-------|
| **Jira Service Desk** | Formal tickets | Per severity | 24/7 |
| **MS Teams** | Quick questions | 4 hours | Business hours |
| **Email** | General inquiries | 8 hours | Business hours |
| **Phone** | P1/P2 escalation | Immediate | 24/7 |
| **PagerDuty** | Critical alerts | 15 min | 24/7 |

### 8.2 Communication Templates

#### Incident Notification

```
Subject: [INCIDENT] [P1] MCP Platform - [Brief Description]

Status: Investigating / Mitigating / Resolved
Severity: P1 (Critical)
Start Time: 2026-01-31 10:30 IST
Current Impact: All users unable to execute tools

Current Actions:
- Investigation in progress
- Engineering team engaged

Next Update: 30 minutes or upon resolution

Contact: support@nagarro.com | +91-XXX-XXX-XXXX
```

#### Resolution Notification

```
Subject: [RESOLVED] [P1] MCP Platform - [Brief Description]

Status: Resolved
Resolution Time: 2026-01-31 11:15 IST
Duration: 45 minutes

Root Cause: [Brief description]
Resolution: [What was done]

Impact Summary:
- Users affected: ~100
- Tool executions failed: ~250

Follow-up: Post-incident review scheduled
```

---

## 9. Continuous Improvement

### 9.1 Service Improvement Process

```
┌─────────────────────────────────────────────────────────────────────────┐
│                 CONTINUOUS IMPROVEMENT CYCLE                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                         ┌──────────────┐                                │
│                         │   MEASURE    │                                │
│                         │   Metrics    │                                │
│                         └──────┬───────┘                                │
│                                │                                         │
│        ┌───────────────────────┼───────────────────────┐                │
│        │                       │                       │                │
│        ▼                       ▼                       ▼                │
│  ┌──────────┐           ┌──────────┐           ┌──────────┐            │
│  │  ANALYZE │           │  IMPROVE │           │  CONTROL │            │
│  │  Trends  │───────────│  Actions │───────────│  Monitor │            │
│  └──────────┘           └──────────┘           └──────────┘            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Improvement Initiatives

| Initiative | Current | Target | Owner | Due |
|------------|---------|--------|-------|-----|
| Reduce MTTR | 3.5h | 2h | Tech Lead | Q2 |
| Improve FCR | 40% | 60% | Support Lead | Q2 |
| Automation | 20% | 50% | DevOps | Q3 |
| Self-service | 30% | 70% | Product | Q4 |
| Proactive alerts | 60% | 90% | DevOps | Q2 |

---

## 10. Contacts

### 10.1 Support Contacts

| Role | Name | Email | Phone |
|------|------|-------|-------|
| Service Desk | Support Team | support@nagarro.com | +91-XXX |
| L2 Support | Application Team | mcp-support@nagarro.com | +91-XXX |
| L3 Engineering | Tech Lead | tech-lead@nagarro.com | +91-XXX |
| Security | Security Team | security@nagarro.com | +91-XXX |
| Escalation | PM | pm@nagarro.com | +91-XXX |

### 10.2 MSIL Contacts

| Role | Name | Email |
|------|------|-------|
| Product Owner | MSIL PO | po@msil.com |
| IT Security | MSIL Security | security@msil.com |
| Infrastructure | MSIL Infra | infra@msil.com |

---

*Document Classification: Internal | Last Review: January 31, 2026*
