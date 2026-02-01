output "web_acl_id" {
  description = "The ID of the WAF Web ACL"
  value       = aws_wafv2_web_acl.mcp_waf.id
}

output "web_acl_arn" {
  description = "The ARN of the WAF Web ACL"
  value       = aws_wafv2_web_acl.mcp_waf.arn
}

output "web_acl_capacity" {
  description = "The capacity of the WAF Web ACL"
  value       = aws_wafv2_web_acl.mcp_waf.capacity
}

output "ip_allowlist_arn" {
  description = "The ARN of the IP allowlist (if enabled)"
  value       = var.ip_allowlist_enabled ? aws_wafv2_ip_set.allowlist[0].arn : null
}

output "ip_blocklist_arn" {
  description = "The ARN of the IP blocklist (if enabled)"
  value       = var.ip_blocklist_enabled ? aws_wafv2_ip_set.blocklist[0].arn : null
}

output "log_group_name" {
  description = "The name of the CloudWatch log group for WAF logs"
  value       = var.enable_logging ? aws_cloudwatch_log_group.waf_logs[0].name : null
}
