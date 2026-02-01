# MSIL MCP Server - Minimal Dev Environment
# ==========================================
# This configuration deploys a low-cost dev environment using:
# - Single EC2 instance running Docker Compose (instead of ECS Fargate)
# - No Redis (uses in-memory caching)
# - No NAT Gateway (public subnet only)
# - Optional: Skip RDS and use SQLite
#
# Estimated Cost: ~$15-25/month

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # For dev, you can use local backend instead of S3
  # backend "local" {
  #   path = "terraform.tfstate"
  # }
  
  backend "s3" {
    bucket         = "msil-mcp-terraform-state"
    key            = "dev/terraform.tfstate"
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
      Environment = "dev"
      ManagedBy   = "Terraform"
      CostCenter  = "Development"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

# Get latest Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
  
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

locals {
  name_prefix = "msil-mcp-dev"
  
  user_data = <<-EOF
    #!/bin/bash
    set -e
    
    # Update system
    dnf update -y
    
    # Install Docker
    dnf install -y docker git
    systemctl start docker
    systemctl enable docker
    usermod -aG docker ec2-user
    
    # Install Docker Compose
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Create app directory
    mkdir -p /opt/msil-mcp
    cd /opt/msil-mcp
    
    # Create docker-compose.yml
    cat > docker-compose.yml << 'COMPOSE'
    version: '3.8'
    services:
      mcp-server:
        image: ${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${local.name_prefix}/mcp-server:latest
        ports:
          - "8000:8000"
        environment:
          - DATABASE_URL=sqlite:///./data/mcp.db
          - REDIS_ENABLED=false
          - API_GATEWAY_MODE=mock
          - DEMO_MODE=true
          - LOG_LEVEL=DEBUG
        volumes:
          - ./data:/app/data
        restart: unless-stopped
      
      chat-ui:
        image: ${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${local.name_prefix}/chat-ui:latest
        ports:
          - "3001:3001"
        environment:
          - VITE_API_URL=http://localhost:8000
        restart: unless-stopped
      
      admin-ui:
        image: ${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${local.name_prefix}/admin-ui:latest
        ports:
          - "3002:3002"
        environment:
          - VITE_API_URL=http://localhost:8000
        restart: unless-stopped
      
      mock-api:
        image: ${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${local.name_prefix}/mock-api:latest
        ports:
          - "3000:3000"
        restart: unless-stopped
    COMPOSE
    
    # Login to ECR and pull images
    aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com
    
    # Start services
    docker-compose pull
    docker-compose up -d
    
    echo "MSIL MCP Dev environment started!"
  EOF
}

# =============================================================================
# VPC - Simplified (Public subnet only, no NAT Gateway)
# =============================================================================

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "${local.name_prefix}-vpc"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = {
    Name = "${local.name_prefix}-igw"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "${local.name_prefix}-public-subnet"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = {
    Name = "${local.name_prefix}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# =============================================================================
# Security Group
# =============================================================================

resource "aws_security_group" "dev_instance" {
  name        = "${local.name_prefix}-sg"
  description = "Security group for MSIL MCP dev instance"
  vpc_id      = aws_vpc.main.id
  
  # SSH access
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidrs
  }
  
  # MCP Server API
  ingress {
    description = "MCP Server API"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # Chat UI
  ingress {
    description = "Chat UI"
    from_port   = 3001
    to_port     = 3001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # Admin UI
  ingress {
    description = "Admin UI"
    from_port   = 3002
    to_port     = 3002
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # Mock API
  ingress {
    description = "Mock API"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # HTTPS (optional, if using nginx)
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # HTTP (optional, if using nginx)
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "${local.name_prefix}-sg"
  }
}

# =============================================================================
# IAM Role for EC2 (to access ECR)
# =============================================================================

resource "aws_iam_role" "dev_instance" {
  name = "${local.name_prefix}-ec2-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecr_readonly" {
  role       = aws_iam_role.dev_instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.dev_instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "dev_instance" {
  name = "${local.name_prefix}-ec2-profile"
  role = aws_iam_role.dev_instance.name
}

# =============================================================================
# EC2 Instance
# =============================================================================

resource "aws_instance" "dev" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.dev_instance.id]
  iam_instance_profile   = aws_iam_instance_profile.dev_instance.name
  key_name               = var.key_pair_name
  
  user_data = local.user_data
  
  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    encrypted   = true
  }
  
  tags = {
    Name = "${local.name_prefix}-instance"
  }
  
  lifecycle {
    ignore_changes = [ami]
  }
}

# Elastic IP (optional - remove to use dynamic IP and save $3.65/month)
resource "aws_eip" "dev" {
  count    = var.use_elastic_ip ? 1 : 0
  instance = aws_instance.dev.id
  domain   = "vpc"
  
  tags = {
    Name = "${local.name_prefix}-eip"
  }
}

# =============================================================================
# ECR Repositories (minimal)
# =============================================================================

resource "aws_ecr_repository" "repos" {
  for_each = toset(["mcp-server", "chat-ui", "admin-ui", "mock-api"])
  
  name                 = "${local.name_prefix}/${each.value}"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = false  # Disable for dev to save costs
  }
  
  tags = {
    Name = "${local.name_prefix}-${each.value}"
  }
}

# Lifecycle policy to clean up old images
resource "aws_ecr_lifecycle_policy" "repos" {
  for_each = aws_ecr_repository.repos
  
  repository = each.value.name
  
  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep only last 3 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 3
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# =============================================================================
# Optional: RDS for PostgreSQL (only if needed)
# =============================================================================

resource "aws_db_instance" "dev" {
  count = var.use_rds ? 1 : 0
  
  identifier = "${local.name_prefix}-postgres"
  
  engine         = "postgres"
  engine_version = "15.5"
  instance_class = "db.t3.micro"  # Free tier eligible
  
  allocated_storage = 20
  storage_type      = "gp2"
  storage_encrypted = true
  
  db_name  = "msil_mcp_db"
  username = "msil_mcp"
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds[0].id]
  db_subnet_group_name   = aws_db_subnet_group.dev[0].name
  publicly_accessible    = false
  
  backup_retention_period = 0  # No backups for dev
  skip_final_snapshot     = true
  deletion_protection     = false
  
  # Performance Insights disabled for cost
  performance_insights_enabled = false
  
  tags = {
    Name = "${local.name_prefix}-postgres"
  }
}

resource "aws_db_subnet_group" "dev" {
  count = var.use_rds ? 1 : 0
  
  name       = "${local.name_prefix}-db-subnet"
  subnet_ids = [aws_subnet.public.id, aws_subnet.public_2[0].id]
  
  tags = {
    Name = "${local.name_prefix}-db-subnet"
  }
}

resource "aws_subnet" "public_2" {
  count = var.use_rds ? 1 : 0
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "${local.name_prefix}-public-subnet-2"
  }
}

resource "aws_security_group" "rds" {
  count = var.use_rds ? 1 : 0
  
  name        = "${local.name_prefix}-rds-sg"
  description = "Security group for RDS"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.dev_instance.id]
  }
  
  tags = {
    Name = "${local.name_prefix}-rds-sg"
  }
}
