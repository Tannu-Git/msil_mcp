output "db_instance_id" {
  description = "Database instance ID"
  value       = aws_db_instance.main.id
}

output "endpoint" {
  description = "Database endpoint (host:port)"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "address" {
  description = "Database host address"
  value       = aws_db_instance.main.address
}

output "port" {
  description = "Database port"
  value       = aws_db_instance.main.port
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}

output "arn" {
  description = "Database ARN"
  value       = aws_db_instance.main.arn
}
