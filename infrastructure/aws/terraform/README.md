# MSIL MCP Server - AWS Deployment Guide

This guide provides step-by-step instructions for deploying the MSIL MCP Server infrastructure to AWS using Terraform.

## Quick Start

### Prerequisites

| Tool | Version | Installation |
|------|---------|--------------|
| Terraform | >= 1.0 | [Download](https://www.terraform.io/downloads) |
| AWS CLI | v2 | [Download](https://aws.amazon.com/cli/) |
| Docker | Latest | [Download](https://docs.docker.com/get-docker/) |

### 1. Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key, Secret Key, and region (ap-south-1)
```

### 2. Create Configuration File

```bash
cd infrastructure/aws/terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and fill in:
- `db_password` - Secure database password
- `acm_certificate_arn` - SSL certificate ARN (optional for HTTPS)

### 3. Deploy Infrastructure

**Windows (PowerShell):**
```powershell
.\deploy.ps1 deploy
```

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh deploy
```

### 4. Build and Push Docker Images

```powershell
.\deploy.ps1 images
```

That's it! Your infrastructure is now deployed.

---

## Detailed Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud (ap-south-1)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                          VPC (10.0.0.0/16)                             │ │
│  │  ┌──────────────────────────┐ ┌──────────────────────────┐            │ │
│  │  │   Public Subnet AZ-a     │ │   Public Subnet AZ-b     │            │ │
│  │  │      10.0.1.0/24         │ │      10.0.2.0/24         │            │ │
│  │  │  ┌─────────────────┐     │ │  ┌─────────────────┐     │            │ │
│  │  │  │       ALB       │─────┼─┼──│       ALB       │     │            │ │
│  │  │  └─────────────────┘     │ │  └─────────────────┘     │            │ │
│  │  │  ┌─────────────────┐     │ │  ┌─────────────────┐     │            │ │
│  │  │  │   NAT Gateway   │     │ │  │   NAT Gateway   │     │            │ │
│  │  │  └─────────────────┘     │ │  └─────────────────┘     │            │ │
│  │  └──────────────────────────┘ └──────────────────────────┘            │ │
│  │                                                                        │ │
│  │  ┌──────────────────────────┐ ┌──────────────────────────┐            │ │
│  │  │   Private Subnet AZ-a    │ │   Private Subnet AZ-b    │            │ │
│  │  │      10.0.11.0/24        │ │      10.0.12.0/24        │            │ │
│  │  │  ┌─────────────────┐     │ │  ┌─────────────────┐     │            │ │
│  │  │  │  ECS Fargate    │     │ │  │  ECS Fargate    │     │            │ │
│  │  │  │  - MCP Server   │     │ │  │  - MCP Server   │     │            │ │
│  │  │  │  - Chat UI      │     │ │  │  - Chat UI      │     │            │ │
│  │  │  │  - Admin UI     │     │ │  │  - Admin UI     │     │            │ │
│  │  │  │  - Mock API     │     │ │  │  - Mock API     │     │            │ │
│  │  │  └─────────────────┘     │ │  └─────────────────┘     │            │ │
│  │  │  ┌─────────────────┐     │ │                          │            │ │
│  │  │  │   RDS Postgres  │     │ │                          │            │ │
│  │  │  │   (Multi-AZ)    │─────┼─┼──────────────────────────│            │ │
│  │  │  └─────────────────┘     │ │                          │            │ │
│  │  │  ┌─────────────────┐     │ │                          │            │ │
│  │  │  │ ElastiCache     │     │ │                          │            │ │
│  │  │  │   Redis         │─────┼─┼──────────────────────────│            │ │
│  │  │  └─────────────────┘     │ │                          │            │ │
│  │  └──────────────────────────┘ └──────────────────────────┘            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐ │
│  │      ECR      │  │ CloudWatch    │  │   Secrets     │  │      S3       │ │
│  │  Repositories │  │    Logs       │  │   Manager     │  │     Logs      │ │
│  └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## AWS Resources Created

| Resource | Description | Est. Monthly Cost (Dev) |
|----------|-------------|-------------------------|
| VPC | Virtual Private Cloud with 2 AZs | Free |
| RDS PostgreSQL | db.t3.micro, 20GB | ~$15 |
| ElastiCache Redis | cache.t3.micro | ~$12 |
| ECS Fargate | 1 vCPU, 2GB per service | ~$30 |
| ALB | Application Load Balancer | ~$20 |
| NAT Gateway | 2 NAT Gateways | ~$65 |
| ECR | Docker image storage | ~$5 |
| CloudWatch | Logs and monitoring | ~$5 |
| **Total (Dev)** | | **~$150/month** |

> **Note:** Production costs will be higher due to Multi-AZ RDS, more ECS tasks, and larger instance sizes.

## Configuration Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `environment` | Environment name | `dev`, `staging`, `prod` |
| `db_password` | Database password | Secure string |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `aws_region` | `ap-south-1` | AWS region |
| `vpc_cidr` | `10.0.0.0/16` | VPC CIDR block |
| `db_instance_class` | `db.t3.micro` | RDS instance class |
| `redis_node_type` | `cache.t3.micro` | ElastiCache node type |
| `acm_certificate_arn` | `""` | ACM certificate for HTTPS |

## Deployment Commands

### Deploy.ps1 (Windows)

```powershell
# Full deployment
.\deploy.ps1 deploy

# Initialize backend only
.\deploy.ps1 init

# Create plan only
.\deploy.ps1 plan

# Apply existing plan
.\deploy.ps1 apply

# Build and push Docker images
.\deploy.ps1 images

# Show deployment outputs
.\deploy.ps1 outputs

# Destroy all infrastructure
.\deploy.ps1 destroy
```

### Deploy.sh (Linux/Mac)

```bash
./deploy.sh deploy    # Full deployment
./deploy.sh init      # Initialize backend
./deploy.sh plan      # Create plan
./deploy.sh apply     # Apply plan
./deploy.sh images    # Build/push images
./deploy.sh outputs   # Show outputs
./deploy.sh destroy   # Destroy all
```

## Post-Deployment Steps

### 1. Add Secrets to AWS Secrets Manager

After deployment, add the following secrets:

```bash
# OpenAI API Key
aws secretsmanager put-secret-value \
  --secret-id msil-mcp-dev-openai-api-key \
  --secret-string '{"api_key":"sk-your-openai-key"}'

# API Key for MCP Server
aws secretsmanager put-secret-value \
  --secret-id msil-mcp-dev-api-key \
  --secret-string '{"api_key":"your-secure-api-key"}'

# Database Password
aws secretsmanager put-secret-value \
  --secret-id msil-mcp-dev-db-password \
  --secret-string '{"password":"your-db-password"}'
```

### 2. Configure DNS (Optional)

If you have a domain, create a CNAME record pointing to the ALB DNS name:

```
mcp.yourdomain.com -> <ALB_DNS_NAME>
chat.mcp.yourdomain.com -> <ALB_DNS_NAME>
admin.mcp.yourdomain.com -> <ALB_DNS_NAME>
```

### 3. Run Database Migrations

```bash
# Connect to ECS task and run migrations
aws ecs execute-command \
  --cluster msil-mcp-dev-cluster \
  --task <TASK_ID> \
  --container mcp-server \
  --command "alembic upgrade head" \
  --interactive
```

## Troubleshooting

### Common Issues

1. **Terraform init fails**
   - Ensure S3 bucket and DynamoDB table exist
   - Check AWS credentials have permissions

2. **ECS tasks not starting**
   - Check CloudWatch logs: `/ecs/msil-mcp-dev/mcp-server`
   - Verify environment variables are correct
   - Check security group rules

3. **Can't connect to RDS**
   - Ensure security group allows traffic from ECS
   - Check subnet route tables

4. **ALB health checks failing**
   - Verify `/health` endpoint returns 200
   - Check target group health check settings

### Useful Commands

```bash
# View ECS service events
aws ecs describe-services \
  --cluster msil-mcp-dev-cluster \
  --services msil-mcp-dev-mcp-server

# View RDS connection info
terraform output database_endpoint

# View ALB DNS name
terraform output alb_dns_name

# View CloudWatch logs
aws logs tail /ecs/msil-mcp-dev/mcp-server --follow
```

## Security Considerations

- All data encrypted at rest (RDS, Redis, S3)
- All traffic encrypted in transit (TLS)
- Private subnets for databases and ECS
- Security groups with least privilege
- Secrets stored in AWS Secrets Manager
- VPC endpoints for AWS services (optional)

## Cleanup

To destroy all infrastructure:

```powershell
.\deploy.ps1 destroy
```

> **Warning:** This will permanently delete all data including databases.

## Support

For issues or questions, contact the MSIL DevOps team or create an issue in the repository.
