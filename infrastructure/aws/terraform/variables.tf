# Variables for MSIL MCP Infrastructure

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "msil-mcp"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

# Database Configuration
variable "db_name" {
  description = "Database name"
  type        = string
  default     = "msil_mcp_db"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "msil_mcp"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

# Redis Configuration
variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

# Application Configuration
variable "api_gateway_mode" {
  description = "API Gateway mode (mock or msil_apim)"
  type        = string
  default     = "msil_apim"
}

variable "acm_certificate_arn" {
  description = "ARN of ACM certificate for HTTPS"
  type        = string
  default     = ""
}

# ECS Configuration
variable "mcp_server_cpu" {
  description = "CPU units for MCP Server (1024 = 1 vCPU)"
  type        = number
  default     = 1024
}

variable "mcp_server_memory" {
  description = "Memory for MCP Server in MB"
  type        = number
  default     = 2048
}

variable "mcp_server_desired_count" {
  description = "Desired number of MCP Server tasks"
  type        = number
  default     = 2
}
