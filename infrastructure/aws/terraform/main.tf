# MSIL MCP Server - AWS Infrastructure
# This Terraform configuration deploys the complete MSIL MCP infrastructure on AWS

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket         = "msil-mcp-terraform-state"
    key            = "terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "msil-mcp-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "MSIL-MCP"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "MSIL-DevOps"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

# Locals
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
  
  azs = slice(data.aws_availability_zones.available.names, 0, 2)
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
  name_prefix         = local.name_prefix
  vpc_cidr            = var.vpc_cidr
  availability_zones  = local.azs
  public_subnet_cidrs = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  
  tags = local.common_tags
}

# Security Groups Module
module "security_groups" {
  source = "./modules/security"
  
  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  
  tags = local.common_tags
}

# RDS PostgreSQL Database
module "rds" {
  source = "./modules/rds"
  
  name_prefix          = local.name_prefix
  vpc_id               = module.vpc.vpc_id
  subnet_ids           = module.vpc.private_subnet_ids
  security_group_ids   = [module.security_groups.rds_security_group_id]
  
  db_name              = var.db_name
  db_username          = var.db_username
  db_password          = var.db_password
  db_instance_class    = var.db_instance_class
  allocated_storage    = var.db_allocated_storage
  multi_az             = var.environment == "prod" ? true : false
  
  backup_retention_period = var.environment == "prod" ? 7 : 1
  
  tags = local.common_tags
}

# ElastiCache Redis
module "redis" {
  source = "./modules/elasticache"
  
  name_prefix        = local.name_prefix
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [module.security_groups.redis_security_group_id]
  
  node_type          = var.redis_node_type
  num_cache_nodes    = var.environment == "prod" ? 2 : 1
  
  tags = local.common_tags
}

# ECS Cluster
module "ecs" {
  source = "./modules/ecs"
  
  name_prefix = local.name_prefix
  
  tags = local.common_tags
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"
  
  name_prefix        = local.name_prefix
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.public_subnet_ids
  security_group_ids = [module.security_groups.alb_security_group_id]
  
  certificate_arn    = var.acm_certificate_arn
  
  tags = local.common_tags
}

# ECR Repositories
module "ecr" {
  source = "./modules/ecr"
  
  name_prefix = local.name_prefix
  
  repositories = [
    "mcp-server",
    "mock-api",
    "chat-ui",
    "admin-ui"
  ]
  
  tags = local.common_tags
}

# ECS Services
module "mcp_server_service" {
  source = "./modules/ecs-service"
  
  name_prefix        = "${local.name_prefix}-mcp-server"
  cluster_id         = module.ecs.cluster_id
  cluster_name       = module.ecs.cluster_name
  
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [module.security_groups.ecs_security_group_id]
  
  container_name     = "mcp-server"
  container_port     = 8000
  image_url          = "${module.ecr.repository_urls["mcp-server"]}:latest"
  
  cpu                = 1024
  memory             = 2048
  desired_count      = var.environment == "prod" ? 2 : 1
  
  target_group_arn   = module.alb.target_group_arns["mcp-server"]
  
  environment_variables = [
    {
      name  = "DATABASE_URL"
      value = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${module.rds.endpoint}/${var.db_name}"
    },
    {
      name  = "REDIS_URL"
      value = "redis://${module.redis.endpoint}:6379/0"
    },
    {
      name  = "API_GATEWAY_MODE"
      value = var.api_gateway_mode
    },
    {
      name  = "ENVIRONMENT"
      value = var.environment
    }
  ]
  
  secrets = [
    {
      name      = "OPENAI_API_KEY"
      valueFrom = aws_secretsmanager_secret.openai_key.arn
    },
    {
      name      = "API_KEY"
      valueFrom = aws_secretsmanager_secret.api_key.arn
    }
  ]
  
  tags = local.common_tags
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "mcp_server" {
  name              = "/ecs/${local.name_prefix}/mcp-server"
  retention_in_days = 7
  
  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "chat_ui" {
  name              = "/ecs/${local.name_prefix}/chat-ui"
  retention_in_days = 7
  
  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "admin_ui" {
  name              = "/ecs/${local.name_prefix}/admin-ui"
  retention_in_days = 7
  
  tags = local.common_tags
}

# Secrets Manager
resource "aws_secretsmanager_secret" "openai_key" {
  name        = "${local.name_prefix}-openai-api-key"
  description = "OpenAI API Key for MSIL MCP Server"
  
  tags = local.common_tags
}

resource "aws_secretsmanager_secret" "api_key" {
  name        = "${local.name_prefix}-api-key"
  description = "API Key for MSIL MCP Server"
  
  tags = local.common_tags
}

resource "aws_secretsmanager_secret" "db_password" {
  name        = "${local.name_prefix}-db-password"
  description = "Database password for MSIL MCP"
  
  tags = local.common_tags
}

# S3 Bucket for logs and backups
resource "aws_s3_bucket" "logs" {
  bucket = "${local.name_prefix}-logs"
  
  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "mcp_server_cpu" {
  alarm_name          = "${local.name_prefix}-mcp-server-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  
  dimensions = {
    ServiceName = "${local.name_prefix}-mcp-server"
    ClusterName = module.ecs.cluster_name
  }
  
  alarm_description = "Alert when MCP Server CPU exceeds 80%"
  
  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${local.name_prefix}-rds-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  
  dimensions = {
    DBInstanceIdentifier = module.rds.db_instance_id
  }
  
  alarm_description = "Alert when RDS CPU exceeds 80%"
  
  tags = local.common_tags
}
