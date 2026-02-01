output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

output "https_listener_arn" {
  description = "ARN of the HTTPS listener"
  value       = length(aws_lb_listener.https) > 0 ? aws_lb_listener.https[0].arn : null
}

output "http_listener_arn" {
  description = "ARN of the HTTP listener"
  value       = aws_lb_listener.http.arn
}

output "target_group_arns" {
  description = "Map of target group ARNs"
  value = {
    "mcp-server" = aws_lb_target_group.mcp_server.arn
    "chat-ui"    = aws_lb_target_group.chat_ui.arn
    "admin-ui"   = aws_lb_target_group.admin_ui.arn
    "mock-api"   = aws_lb_target_group.mock_api.arn
  }
}
