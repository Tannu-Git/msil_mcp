# Variables for MSIL MCP Dev Environment (Minimal Cost)

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"  # 2 vCPU, 2GB RAM - ~$15/month
  # Options:
  # - t3.micro:  1 vCPU, 1GB  - ~$7.5/month (may be slow)
  # - t3.small:  2 vCPU, 2GB  - ~$15/month (recommended)
  # - t3.medium: 2 vCPU, 4GB  - ~$30/month (comfortable)
}

variable "key_pair_name" {
  description = "Name of existing EC2 key pair for SSH access"
  type        = string
  default     = ""  # Set this or use SSM Session Manager
}

variable "allowed_ssh_cidrs" {
  description = "CIDR blocks allowed for SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Restrict this in production!
}

variable "use_elastic_ip" {
  description = "Use Elastic IP (adds ~$3.65/month if instance is stopped)"
  type        = bool
  default     = false
}

variable "use_rds" {
  description = "Use RDS PostgreSQL instead of SQLite (adds ~$15/month)"
  type        = bool
  default     = false
}

variable "db_password" {
  description = "Database password (only if use_rds = true)"
  type        = string
  sensitive   = true
  default     = ""
}
