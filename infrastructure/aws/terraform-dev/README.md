# MSIL MCP Server - Minimal Dev Environment

Ultra-low-cost dev/testing deployment using a single EC2 instance.

## Cost Comparison

| Component | Full Stack (ECS/RDS/Redis) | Minimal Dev |
|-----------|---------------------------|-------------|
| ECS Fargate | ~$30/month | - |
| RDS PostgreSQL | ~$15/month | SQLite (free) |
| ElastiCache Redis | ~$12/month | In-memory (free) |
| NAT Gateway (2x) | ~$65/month | - |
| ALB | ~$20/month | - |
| EC2 t3.small | - | ~$15/month |
| **TOTAL** | **~$150/month** | **~$20/month** |

**Savings: ~$130/month (87%)**

## What's Different?

| Feature | Full Stack | Minimal Dev |
|---------|-----------|-------------|
| Compute | ECS Fargate (auto-scaling) | Single EC2 instance |
| Database | RDS PostgreSQL (managed) | SQLite file |
| Cache | ElastiCache Redis | In-memory/disabled |
| Networking | Private subnets + NAT | Public subnet only |
| Load Balancer | ALB | Direct EC2 access |
| High Availability | Multi-AZ | Single AZ |

## Quick Start

```powershell
# 1. Configure
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars if needed

# 2. Deploy
.\deploy.ps1 deploy

# 3. Build and push Docker images
.\deploy.ps1 images

# 4. Check status
.\deploy.ps1 status
```

## Access URLs

After deployment:
- **MCP Server**: `http://<EC2_IP>:8000`
- **Chat UI**: `http://<EC2_IP>:3001`
- **Admin UI**: `http://<EC2_IP>:3002`
- **Mock API**: `http://<EC2_IP>:3000`

## Commands

```powershell
.\deploy.ps1 deploy   # Full deployment
.\deploy.ps1 images   # Build and push Docker images
.\deploy.ps1 status   # Show instance status and URLs
.\deploy.ps1 ssh      # Connect via SSM Session Manager
.\deploy.ps1 logs     # View container logs
.\deploy.ps1 destroy  # Destroy everything
```

## Customization

### Use PostgreSQL instead of SQLite
```hcl
use_rds = true
db_password = "your-secure-password"
```
Adds ~$15/month but provides a real PostgreSQL database.

### Use Elastic IP
```hcl
use_elastic_ip = true
```
Adds ~$3.65/month but IP stays the same when instance restarts.

### Larger Instance
```hcl
instance_type = "t3.medium"  # 2 vCPU, 4GB RAM
```
More resources for ~$30/month total.

## Connecting to the Instance

### Via SSM (no SSH key needed)
```powershell
.\deploy.ps1 ssh
# or
aws ssm start-session --target <instance-id>
```

### Via SSH (if key pair configured)
```bash
ssh -i your-key.pem ec2-user@<EC2_IP>
```

## Managing Services

SSH into the instance, then:

```bash
cd /opt/msil-mcp

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Update images
docker-compose pull
docker-compose up -d

# Stop all
docker-compose down
```

## When to Use This vs Full Stack

| Use Minimal Dev When | Use Full Stack When |
|---------------------|---------------------|
| Local development testing | Production deployment |
| Demo/POC | High availability required |
| Learning/experimentation | Multiple developers |
| Budget constraints | Performance testing |
| Single developer | Security compliance |

## Upgrading to Full Stack

When ready for production:

```powershell
cd ../terraform
.\deploy.ps1 deploy
```

This will create the full ECS/RDS/Redis infrastructure.
