# Outputs for MSIL MCP Infrastructure

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.redis.endpoint
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = module.alb.dns_name
}

output "alb_zone_id" {
  description = "Application Load Balancer Zone ID"
  value       = module.alb.zone_id
}

output "ecs_cluster_name" {
  description = "ECS Cluster name"
  value       = module.ecs.cluster_name
}

output "ecr_repository_urls" {
  description = "ECR repository URLs"
  value       = module.ecr.repository_urls
}

output "mcp_server_url" {
  description = "MCP Server URL"
  value       = "https://${module.alb.dns_name}"
}

output "chat_ui_url" {
  description = "Chat UI URL"
  value       = "https://${module.alb.dns_name}/chat"
}

output "admin_ui_url" {
  description = "Admin UI URL"
  value       = "https://${module.alb.dns_name}/admin"
}
