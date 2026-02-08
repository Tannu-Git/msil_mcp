# Infrastructure Bill of Materials (BOM)

**Document Version**: 2.1  
**Last Updated**: February 2, 2026  
**Classification**: Internal

---

## 1. AWS Infrastructure BOM

### 1.1 Compute Resources

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AWS COMPUTE INFRASTRUCTURE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Service: Amazon EKS (Elastic Kubernetes Service)                       │
│  Region: ap-south-1 (Mumbai)                                            │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      EKS CLUSTER                                 │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  Cluster Name     : msil-mcp-eks-prod                           │    │
│  │  Version          : 1.29                                         │    │
│  │  Endpoint Access  : Private with VPC endpoint                   │    │
│  │  Logging          : API, Audit, Authenticator, Scheduler        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    NODE GROUPS                                   │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │                                                                  │    │
│  │  Application Nodes:                                              │    │
│  │  ├── Instance Type  : m6i.xlarge (4 vCPU, 16 GB RAM)            │    │
│  │  ├── Min Nodes      : 3                                          │    │
│  │  ├── Max Nodes      : 10                                         │    │
│  │  ├── Desired Nodes  : 4                                          │    │
│  │  └── Disk           : 100 GB gp3                                │    │
│  │                                                                  │    │
│  │  System Nodes (monitoring, logging):                            │    │
│  │  ├── Instance Type  : m6i.large (2 vCPU, 8 GB RAM)              │    │
│  │  ├── Min Nodes      : 2                                          │    │
│  │  ├── Max Nodes      : 4                                          │    │
│  │  └── Disk           : 50 GB gp3                                 │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Database Resources

| Service | Configuration | Specification | Monthly Cost (Est.) |
|---------|---------------|---------------|---------------------|
| **RDS PostgreSQL** | Production | db.r6g.xlarge (4 vCPU, 32 GB) | ₹45,000 |
| | Storage | 500 GB gp3 | ₹6,000 |
| | Multi-AZ | Enabled | Included |
| | Backup | 30-day retention | ₹3,000 |
| **RDS PostgreSQL** | Staging | db.r6g.large (2 vCPU, 16 GB) | ₹22,000 |
| | Storage | 200 GB gp3 | ₹2,400 |
| **ElastiCache Redis** | Production | cache.r6g.large (2 nodes) | ₹18,000 |
| | Cluster Mode | Enabled with 2 shards | Included |
| **ElastiCache Redis** | Staging | cache.r6g.medium (1 node) | ₹6,000 |

**Phase 1-3 Note**: Exposure Governance introduced two new tables (`policy_roles`, `policy_role_permissions`) and indexes for role-based tool visibility. No additional infrastructure capacity is required beyond existing PostgreSQL sizing.

### 1.3 Networking Resources

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    VPC ARCHITECTURE                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  VPC CIDR: 10.100.0.0/16                                                │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    SUBNETS                                       │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │                                                                  │    │
│  │  Public Subnets (NAT, ALB):                                     │    │
│  │  ├── ap-south-1a : 10.100.1.0/24                                │    │
│  │  ├── ap-south-1b : 10.100.2.0/24                                │    │
│  │  └── ap-south-1c : 10.100.3.0/24                                │    │
│  │                                                                  │    │
│  │  Private Subnets (EKS, Apps):                                   │    │
│  │  ├── ap-south-1a : 10.100.10.0/24                               │    │
│  │  ├── ap-south-1b : 10.100.11.0/24                               │    │
│  │  └── ap-south-1c : 10.100.12.0/24                               │    │
│  │                                                                  │    │
│  │  Database Subnets (RDS, ElastiCache):                           │    │
│  │  ├── ap-south-1a : 10.100.20.0/24                               │    │
│  │  ├── ap-south-1b : 10.100.21.0/24                               │    │
│  │  └── ap-south-1c : 10.100.22.0/24                               │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    NETWORK COMPONENTS                            │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │                                                                  │    │
│  │  • NAT Gateways           : 3 (one per AZ)         ₹9,000/mo    │    │
│  │  • Internet Gateway       : 1                       Free        │    │
│  │  • VPC Endpoints          : 6 (S3, ECR, Secrets, etc.)          │    │
│  │  • Transit Gateway        : Optional (cross-VPC)                │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.4 Load Balancing & CDN

| Service | Configuration | Monthly Cost (Est.) |
|---------|---------------|---------------------|
| **Application Load Balancer** | Production (2 LCU avg) | ₹4,000 |
| **Application Load Balancer** | Staging | ₹2,000 |
| **AWS WAF** | 10 rules, 1M requests | ₹4,000 |
| **CloudFront** | 1 TB transfer (optional) | ₹8,000 |

### 1.5 Storage Resources

| Service | Purpose | Configuration | Monthly Cost (Est.) |
|---------|---------|---------------|---------------------|
| **S3 Standard** | Application data | 100 GB | ₹250 |
| **S3 Intelligent-Tiering** | Audit logs (WORM) | 500 GB | ₹1,000 |
| **S3 Glacier Deep Archive** | Long-term audit | 1 TB | ₹100 |
| **ECR** | Container images | 50 GB | ₹500 |
| **EBS gp3** | EKS nodes | 600 GB total | ₹4,500 |

### 1.6 Security Services

| Service | Configuration | Monthly Cost (Est.) |
|---------|---------------|---------------------|
| **AWS Secrets Manager** | 20 secrets | ₹800 |
| **AWS KMS** | 5 CMKs + 100K requests | ₹500 |
| **AWS Certificate Manager** | Public certificates | Free |
| **AWS Shield Standard** | DDoS protection | Free |
| **AWS GuardDuty** | Threat detection | ₹2,000 |

### 1.7 Monitoring & Logging

| Service | Configuration | Monthly Cost (Est.) |
|---------|---------------|---------------------|
| **CloudWatch Logs** | 100 GB ingestion, 30-day retention | ₹5,000 |
| **CloudWatch Metrics** | Custom metrics (100) | ₹3,000 |
| **CloudWatch Alarms** | 50 alarms | ₹500 |
| **AWS X-Ray** | 1M traces sampled | ₹500 |

---

## 2. Software Bill of Materials

### 2.1 Backend Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| Python | 3.13 | PSF | Runtime |
| FastAPI | 0.109+ | MIT | Web framework |
| Uvicorn | 0.27+ | BSD | ASGI server |
| Pydantic | 2.6+ | MIT | Data validation |
| SQLAlchemy | 2.0+ | MIT | ORM |
| asyncpg | 0.29+ | Apache 2.0 | PostgreSQL driver |
| redis | 5.0+ | MIT | Redis client |
| httpx | 0.26+ | BSD | HTTP client |
| PyJWT | 2.8+ | MIT | JWT handling |
| cryptography | 42.0+ | Apache/BSD | Cryptographic operations |
| boto3 | 1.34+ | Apache 2.0 | AWS SDK |
| structlog | 24.1+ | Apache 2.0 | Structured logging |
| opentelemetry-* | 1.22+ | Apache 2.0 | Distributed tracing |

### 2.2 Frontend Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| React | 18.2+ | MIT | UI framework |
| TypeScript | 5.3+ | Apache 2.0 | Type system |
| Vite | 5.0+ | MIT | Build tool |
| React Router | 6.21+ | MIT | Routing |
| TanStack Query | 5.17+ | MIT | Data fetching |
| Tailwind CSS | 3.4+ | MIT | Styling |
| Zustand | 4.4+ | MIT | State management |
| Axios | 1.6+ | MIT | HTTP client |
| date-fns | 3.0+ | MIT | Date utilities |

### 2.3 Infrastructure Tools

| Tool | Version | License | Purpose |
|------|---------|---------|---------|
| Kubernetes | 1.29 | Apache 2.0 | Container orchestration |
| Helm | 3.14+ | Apache 2.0 | Package management |
| Terraform | 1.7+ | MPL 2.0 | Infrastructure as Code |
| Docker | 25.0+ | Apache 2.0 | Containerization |
| Nginx | 1.25+ | BSD-2 | Ingress controller |
| OPA | 0.61+ | Apache 2.0 | Policy engine |
| Fluent Bit | 2.2+ | Apache 2.0 | Log shipping |

### 2.4 Security Tools

| Tool | Version | License | Purpose |
|------|---------|---------|---------|
| Trivy | 0.49+ | Apache 2.0 | Container scanning |
| Grype | 0.74+ | Apache 2.0 | Vulnerability scanning |
| Bandit | 1.7+ | Apache 2.0 | Python SAST |
| Semgrep | 1.56+ | LGPL | Multi-language SAST |
| OWASP ZAP | 2.14+ | Apache 2.0 | DAST |

---

## 3. Cost Summary

### 3.1 Monthly Infrastructure Cost (Production)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MONTHLY COST BREAKDOWN                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Category                              │  Monthly (₹)   │  % of Total   │
│  ──────────────────────────────────────┼────────────────┼──────────────  │
│  EKS Cluster                           │     15,000     │      6%       │
│  EC2 (EKS Nodes - 4 x m6i.xlarge)     │     60,000     │     25%       │
│  RDS PostgreSQL (Production)           │     54,000     │     22%       │
│  ElastiCache Redis (Production)        │     18,000     │      7%       │
│  S3 Storage                            │      2,000     │      1%       │
│  Networking (NAT, VPC Endpoints)       │     15,000     │      6%       │
│  Load Balancers                        │      6,000     │      2%       │
│  WAF                                   │      4,000     │      2%       │
│  Monitoring (CloudWatch, X-Ray)        │      9,000     │      4%       │
│  Security (Secrets, KMS, GuardDuty)    │      3,500     │      1%       │
│  Data Transfer                         │     10,000     │      4%       │
│  ──────────────────────────────────────┼────────────────┼──────────────  │
│  PRODUCTION TOTAL                      │   ₹1,96,500    │              │
│  ──────────────────────────────────────┼────────────────┼──────────────  │
│                                                                          │
│  Staging Environment (~40%)            │     78,600     │              │
│  Development Environment (~20%)        │     39,300     │              │
│  ──────────────────────────────────────┼────────────────┼──────────────  │
│  GRAND TOTAL (All Environments)        │   ₹3,14,400    │              │
│  ──────────────────────────────────────┼────────────────┼──────────────  │
│                                                                          │
│  Annual Cost (Production Only)         │  ₹23,58,000    │              │
│  Annual Cost (All Environments)        │  ₹37,72,800    │              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Cost Optimization Recommendations

| Strategy | Potential Savings | Implementation |
|----------|-------------------|----------------|
| **Reserved Instances (1-year)** | 30-40% on compute | Purchase RI for baseline nodes |
| **Savings Plans** | 20-30% on compute | Commit to consistent usage |
| **Spot Instances** | 60-80% on non-prod | Use for staging/dev nodes |
| **S3 Lifecycle Policies** | 50% on storage | Move old logs to Glacier |
| **Right-sizing** | 10-20% | Monthly review of utilization |
| **Auto-scaling** | 20-30% | Scale down during off-hours |

### 3.3 3-Year TCO

| Year | Infrastructure | Development | Support | Total |
|------|----------------|-------------|---------|-------|
| Year 1 | ₹37.7L | ₹120L | ₹0 | ₹157.7L |
| Year 2 | ₹45.2L (growth) | ₹40L (enhancements) | ₹48L | ₹133.2L |
| Year 3 | ₹54.3L (growth) | ₹40L (enhancements) | ₹48L | ₹142.3L |
| **Total** | **₹137.2L** | **₹200L** | **₹96L** | **₹433.2L** |

---

## 4. Environment Specifications

### 4.1 Environment Comparison

| Aspect | Production | Staging | Development |
|--------|------------|---------|-------------|
| **EKS Nodes** | 4-10 x m6i.xlarge | 2-4 x m6i.large | 2 x m6i.large |
| **RDS** | db.r6g.xlarge, Multi-AZ | db.r6g.large, Single-AZ | db.t3.medium |
| **Redis** | 2x cache.r6g.large | cache.r6g.medium | cache.t3.small |
| **Availability** | 99.9% SLA | 99.5% | Best effort |
| **Backups** | 30-day, PITR | 7-day | On-demand |
| **Monitoring** | Full | Standard | Basic |
| **DR** | Cross-AZ | Single-AZ | None |

### 4.2 Scaling Specifications

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AUTO-SCALING CONFIGURATION                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  MCP Server Pods:                                                        │
│  ├── Min Replicas      : 3                                              │
│  ├── Max Replicas      : 20                                             │
│  ├── Target CPU        : 70%                                            │
│  └── Target Memory     : 75%                                            │
│                                                                          │
│  EKS Node Group:                                                         │
│  ├── Min Nodes         : 3                                              │
│  ├── Max Nodes         : 10                                             │
│  ├── Scale-up          : +2 nodes when capacity <20%                    │
│  └── Scale-down        : -1 node when capacity >60% (10 min cooldown)  │
│                                                                          │
│  RDS Read Replicas (if needed):                                         │
│  ├── Min Replicas      : 0                                              │
│  └── Max Replicas      : 2                                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Licenses & Subscriptions

### 5.1 Third-Party Licenses

| Vendor | Product | License Type | Annual Cost |
|--------|---------|--------------|-------------|
| AWS | Cloud Services | Pay-as-you-go | ~₹37.7L |
| Microsoft | Azure AD (MSIL existing) | Included | ₹0 |
| Microsoft | Azure APIM (MSIL existing) | Included | ₹0 |
| GitHub | GitHub Actions | Free tier | ₹0 |
| Snyk | Container Scanning (optional) | Free tier | ₹0 |

### 5.2 Open Source Licenses (No Cost)

All core platform software uses permissive open-source licenses (MIT, Apache 2.0, BSD) with no licensing fees.

---

## 6. Procurement Checklist

### 6.1 AWS Resources

- [ ] AWS Enterprise Agreement (if applicable)
- [ ] Reserved Instance purchase (Year 2)
- [ ] AWS Support plan (Business tier recommended)

### 6.2 Pre-requisites from MSIL

- [ ] AWS account provisioning
- [ ] VPC connectivity to MSIL network
- [ ] Azure AD application registration
- [ ] APIM subscription and endpoints
- [ ] mTLS certificates
- [ ] Network firewall rules

---

## 7. Resource Tags

### 7.1 Mandatory Tags

```yaml
tags:
  Project: "MSIL-MCP"
  Environment: "production"  # production, staging, development
  Owner: "nagarro"
  CostCenter: "IT-DIGITAL"
  Application: "mcp-platform"
  DataClassification: "confidential"
  Compliance: "dpdp"
  CreatedBy: "terraform"
  CreatedDate: "2026-01-31"
```

### 7.2 Tag-based Cost Allocation

| Tag | Purpose |
|-----|---------|
| Project | Cost allocation by project |
| Environment | Cost split by environment |
| Owner | Responsibility assignment |
| CostCenter | Finance reporting |

---

*Document Classification: Internal | Last Review: January 31, 2026*
