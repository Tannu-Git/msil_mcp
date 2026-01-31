# MSIL MCP Server - AWS Deployment Guide

This guide provides step-by-step instructions for deploying the MSIL MCP Server infrastructure to AWS using Terraform.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Terraform** >= 1.0 installed
3. **AWS CLI** configured with credentials
4. **Docker** for building container images
5. **Git** for version control

## Architecture Overview

The infrastructure includes:
- **VPC** with public and private subnets across 2 AZs
- **RDS PostgreSQL 15** for database
- **ElastiCache Redis** for caching
- **ECS Fargate** for container orchestration
- **Application Load Balancer** for routing
- **ECR** for Docker image storage
- **CloudWatch** for logging and monitoring
- **Secrets Manager** for sensitive data

## Deployment Steps

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd msil_mcp/infrastructure/aws/terraform
```

### Step 2: Configure Backend

Create an S3 bucket and DynamoDB table for Terraform state:

```bash
# Create S3 bucket for state
aws s3 mb s3://msil-mcp-terraform-state --region ap-south-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket msil-mcp-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name msil-mcp-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-south-1
```

### Step 3: Configure Variables

Create a `terraform.tfvars` file:

```hcl
# Environment Configuration
environment  = "dev"  # or "staging", "prod"
aws_region   = "ap-south-1"
project_name = "msil-mcp"

# VPC Configuration
vpc_cidr             = "10.0.0.0/16"
public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]

# Database Configuration
db_name           = "msil_mcp_db"
db_username       = "msil_mcp"
db_password       = "CHANGE_ME_SECURE_PASSWORD"  # Use strong password
db_instance_class = "db.t3.micro"  # or db.t3.small for prod

# Redis Configuration
redis_node_type = "cache.t3.micro"  # or cache.t3.small for prod

# Application Configuration
api_gateway_mode = "msil_apim"  # or "mock" for testing

# ACM Certificate (optional - for HTTPS)
acm_certificate_arn = ""  # Add your ACM certificate ARN
```

### Step 4: Store Secrets in AWS Secrets Manager

```bash
# Store OpenAI API Key
aws secretsmanager create-secret \
  --name msil-mcp-dev-openai-api-key \
  --secret-string "your-openai-api-key" \
  --region ap-south-1

# Store API Key
aws secretsmanager create-secret \
  --name msil-mcp-dev-api-key \
  --secret-string "msil-mcp-secure-api-key-2026" \
  --region ap-south-1

# Store Database Password
aws secretsmanager create-secret \
  --name msil-mcp-dev-db-password \
  --secret-string "your-secure-db-password" \
  --region ap-south-1
```

### Step 5: Build and Push Docker Images

```bash
# Login to ECR
aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-south-1.amazonaws.com

# Build MCP Server
cd ../../../mcp-server
docker build -t msil-mcp-dev-mcp-server:latest .
docker tag msil-mcp-dev-mcp-server:latest <account-id>.dkr.ecr.ap-south-1.amazonaws.com/msil-mcp-dev-mcp-server:latest
docker push <account-id>.dkr.ecr.ap-south-1.amazonaws.com/msil-mcp-dev-mcp-server:latest

# Build Mock API
cd ../mock-api
docker build -t msil-mcp-dev-mock-api:latest .
docker tag msil-mcp-dev-mock-api:latest <account-id>.dkr.ecr.ap-south-1.amazonaws.com/msil-mcp-dev-mock-api:latest
docker push <account-id>.dkr.ecr.ap-south-1.amazonaws.com/msil-mcp-dev-mock-api:latest

# Build Chat UI
cd ../chat-ui
docker build -t msil-mcp-dev-chat-ui:latest .
docker tag msil-mcp-dev-chat-ui:latest <account-id>.dkr.ecr.ap-south-1.amazonaws.com/msil-mcp-dev-chat-ui:latest
docker push <account-id>.dkr.ecr.ap-south-1.amazonaws.com/msil-mcp-dev-chat-ui:latest

# Build Admin UI
cd ../admin-ui
docker build -t msil-mcp-dev-admin-ui:latest .
docker tag msil-mcp-dev-admin-ui:latest <account-id>.dkr.ecr.ap-south-1.amazonaws.com/msil-mcp-dev-admin-ui:latest
docker push <account-id>.dkr.ecr.ap-south-1.amazonaws.com/msil-mcp-dev-admin-ui:latest
```

### Step 6: Initialize Terraform

```bash
cd infrastructure/aws/terraform
terraform init
```

### Step 7: Plan Infrastructure

```bash
terraform plan -out=tfplan
```

Review the plan carefully to ensure all resources are correct.

### Step 8: Apply Infrastructure

```bash
terraform apply tfplan
```

This will create:
- VPC with subnets, NAT gateways, route tables
- RDS PostgreSQL instance
- ElastiCache Redis cluster
- ECS cluster and services
- Application Load Balancer
- CloudWatch log groups and alarms

**Deployment time**: ~15-20 minutes

### Step 9: Initialize Database

Once the RDS instance is ready, initialize the database schema:

```bash
# Get RDS endpoint from Terraform output
export DB_ENDPOINT=$(terraform output -raw rds_endpoint)

# Run database migrations
cd ../../../mcp-server
python scripts/init_db.py --host $DB_ENDPOINT --database msil_mcp_db --user msil_mcp --password <db-password>
```

### Step 10: Verify Deployment

```bash
# Get ALB DNS name
export ALB_DNS=$(terraform output -raw alb_dns_name)

# Test MCP Server health
curl https://$ALB_DNS/health

# Test MCP protocol
curl -X POST https://$ALB_DNS/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/list","params":{}}'

# Access Chat UI
open https://$ALB_DNS/chat

# Access Admin UI
open https://$ALB_DNS/admin
```

## Post-Deployment Configuration

### Configure Custom Domain (Optional)

1. Create Route53 hosted zone
2. Add ACM certificate for your domain
3. Update `acm_certificate_arn` in `terraform.tfvars`
4. Create Route53 A record pointing to ALB

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id <zone-id> \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "mcp.yourdomain.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "<alb-zone-id>",
          "DNSName": "<alb-dns-name>",
          "EvaluateTargetHealth": false
        }
      }
    }]
  }'
```

### Configure MSIL APIM Integration

Update the following secrets in Secrets Manager:

```bash
# Update MCP Server environment variables
aws secretsmanager put-secret-value \
  --secret-id msil-mcp-dev-msil-apim-key \
  --secret-string "your-msil-apim-subscription-key" \
  --region ap-south-1
```

### Enable CloudWatch Alarms

CloudWatch alarms are automatically created for:
- ECS CPU utilization > 80%
- RDS CPU utilization > 80%
- RDS freeable memory < 256MB
- RDS free storage < 2GB

Configure SNS topic for alarm notifications:

```bash
# Create SNS topic
aws sns create-topic --name msil-mcp-alerts --region ap-south-1

# Subscribe email
aws sns subscribe \
  --topic-arn arn:aws:sns:ap-south-1:<account-id>:msil-mcp-alerts \
  --protocol email \
  --notification-endpoint devops@example.com
```

## Monitoring and Logging

### CloudWatch Logs

View application logs:

```bash
# MCP Server logs
aws logs tail /ecs/msil-mcp-dev/mcp-server --follow

# Chat UI logs
aws logs tail /ecs/msil-mcp-dev/chat-ui --follow
```

### CloudWatch Metrics

Key metrics to monitor:
- ECS Service: CPU, Memory, Task Count
- ALB: Request Count, Target Response Time, HTTP 5xx
- RDS: CPU, Connections, Read/Write IOPS
- ElastiCache: CPU, Memory, Cache Hits/Misses

### Cost Monitoring

Estimated monthly costs (dev environment):
- RDS (db.t3.micro): ~$15
- ElastiCache (cache.t3.micro): ~$12
- ECS Fargate (2 tasks): ~$30
- ALB: ~$20
- Data Transfer: ~$10
- **Total**: ~$87/month

Production costs will be higher based on:
- Multi-AZ RDS
- Larger instance sizes
- More ECS tasks
- Higher data transfer

## Scaling

### Horizontal Scaling (ECS)

```bash
# Update desired count
aws ecs update-service \
  --cluster msil-mcp-dev-cluster \
  --service msil-mcp-dev-mcp-server \
  --desired-count 4 \
  --region ap-south-1
```

### Vertical Scaling (RDS)

```bash
# Modify instance class
aws rds modify-db-instance \
  --db-instance-identifier msil-mcp-dev-postgres \
  --db-instance-class db.t3.small \
  --apply-immediately \
  --region ap-south-1
```

## Backup and Disaster Recovery

### Database Backups

- Automated daily backups (7-day retention)
- Manual snapshots available
- Point-in-time recovery enabled

```bash
# Create manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier msil-mcp-dev-postgres \
  --db-snapshot-identifier msil-mcp-dev-manual-$(date +%Y%m%d) \
  --region ap-south-1
```

### Application Backups

Container images are versioned in ECR with lifecycle policies.

## Troubleshooting

### Common Issues

**Issue**: ECS tasks failing to start
```bash
# Check ECS task logs
aws ecs describe-tasks \
  --cluster msil-mcp-dev-cluster \
  --tasks <task-id> \
  --region ap-south-1
```

**Issue**: Database connection errors
```bash
# Test database connectivity from ECS task
aws ecs execute-command \
  --cluster msil-mcp-dev-cluster \
  --task <task-id> \
  --container mcp-server \
  --interactive \
  --command "pg_isready -h <db-endpoint>"
```

**Issue**: ALB health check failures
```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn> \
  --region ap-south-1
```

## Cleanup

To destroy all infrastructure:

```bash
# Disable deletion protection on RDS
aws rds modify-db-instance \
  --db-instance-identifier msil-mcp-dev-postgres \
  --no-deletion-protection \
  --region ap-south-1

# Wait for modification to complete
aws rds wait db-instance-available \
  --db-instance-identifier msil-mcp-dev-postgres \
  --region ap-south-1

# Destroy infrastructure
terraform destroy
```

**Warning**: This will permanently delete all data!

## Security Best Practices

1. **Use IAM roles** instead of access keys
2. **Enable MFA** for AWS console access
3. **Rotate secrets** regularly in Secrets Manager
4. **Enable VPC Flow Logs** for network monitoring
5. **Use private subnets** for databases and application containers
6. **Enable encryption** at rest and in transit
7. **Regular security audits** using AWS Security Hub
8. **Implement least privilege** IAM policies

## Support

For issues or questions:
- Technical Support: devops@example.com
- Documentation: https://docs.example.com/msil-mcp
- Slack Channel: #msil-mcp-support

## License

Copyright © 2026 Maruti Suzuki India Limited
