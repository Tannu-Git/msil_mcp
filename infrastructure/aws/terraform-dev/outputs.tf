# Outputs for MSIL MCP Dev Environment

output "instance_public_ip" {
  description = "Public IP of the dev instance"
  value       = var.use_elastic_ip ? aws_eip.dev[0].public_ip : aws_instance.dev.public_ip
}

output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.dev.id
}

output "mcp_server_url" {
  description = "MCP Server API URL"
  value       = "http://${var.use_elastic_ip ? aws_eip.dev[0].public_ip : aws_instance.dev.public_ip}:8000"
}

output "chat_ui_url" {
  description = "Chat UI URL"
  value       = "http://${var.use_elastic_ip ? aws_eip.dev[0].public_ip : aws_instance.dev.public_ip}:3001"
}

output "admin_ui_url" {
  description = "Admin UI URL"
  value       = "http://${var.use_elastic_ip ? aws_eip.dev[0].public_ip : aws_instance.dev.public_ip}:3002"
}

output "mock_api_url" {
  description = "Mock API URL"
  value       = "http://${var.use_elastic_ip ? aws_eip.dev[0].public_ip : aws_instance.dev.public_ip}:3000"
}

output "ssh_command" {
  description = "SSH command to connect"
  value       = var.key_pair_name != "" ? "ssh -i ${var.key_pair_name}.pem ec2-user@${var.use_elastic_ip ? aws_eip.dev[0].public_ip : aws_instance.dev.public_ip}" : "Use AWS SSM Session Manager"
}

output "ssm_command" {
  description = "SSM Session Manager command"
  value       = "aws ssm start-session --target ${aws_instance.dev.id}"
}

output "ecr_repositories" {
  description = "ECR repository URLs"
  value       = { for k, v in aws_ecr_repository.repos : k => v.repository_url }
}

output "database_info" {
  description = "Database connection info"
  value       = var.use_rds ? "postgresql://msil_mcp:****@${aws_db_instance.dev[0].endpoint}/msil_mcp_db" : "SQLite: /app/data/mcp.db"
}

output "estimated_monthly_cost" {
  description = "Estimated monthly cost"
  value       = <<-EOT
    Estimated Monthly Cost:
    - EC2 ${var.instance_type}: ~$${var.instance_type == "t3.micro" ? "7.50" : var.instance_type == "t3.small" ? "15.00" : "30.00"}
    - EBS 30GB gp3: ~$2.50
    - Elastic IP: ${var.use_elastic_ip ? "~$3.65" : "$0.00"}
    - RDS: ${var.use_rds ? "~$15.00" : "$0.00"}
    - ECR: ~$1.00
    - Data Transfer: ~$2.00
    ----------------------------------------
    TOTAL: ~$${var.use_rds ? (var.use_elastic_ip ? "39" : "35") : (var.use_elastic_ip ? "24" : "20")}/month
  EOT
}
