# AWS WAF v2 Configuration for MSIL MCP Server
# Provides L7 protection with OWASP rules, rate limiting, and IP allowlisting

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# WAF Web ACL
resource "aws_wafv2_web_acl" "mcp_waf" {
  name  = "${var.project_name}-${var.environment}-waf"
  scope = var.scope # REGIONAL for ALB/API Gateway, CLOUDFRONT for CloudFront
  
  description = "WAF for MSIL MCP Server - OWASP protection and rate limiting"
  
  default_action {
    allow {}
  }
  
  # Rule 1: Rate Limiting (2000 requests per 5 minutes per IP)
  rule {
    name     = "rate-limit-rule"
    priority = 1
    
    action {
      block {
        custom_response {
          response_code = 429
          custom_response_body_key = "rate_limit_response"
        }
      }
    }
    
    statement {
      rate_based_statement {
        limit              = var.rate_limit
        aggregate_key_type = "IP"
        
        scope_down_statement {
          not_statement {
            statement {
              byte_match_statement {
                search_string         = "health"
                positional_constraint = "CONTAINS"
                
                field_to_match {
                  uri_path {}
                }
                
                text_transformation {
                  priority = 0
                  type     = "LOWERCASE"
                }
              }
            }
          }
        }
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name               = "${var.project_name}-rate-limit"
      sampled_requests_enabled  = true
    }
  }
  
  # Rule 2: AWS Managed Rules - Core Rule Set (CRS)
  rule {
    name     = "aws-managed-rules-common"
    priority = 2
    
    override_action {
      none {}
    }
    
    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesCommonRuleSet"
        
        # Exclude rules if needed (example)
        # excluded_rule {
        #   name = "SizeRestrictions_BODY"
        # }
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name               = "${var.project_name}-aws-common-rules"
      sampled_requests_enabled  = true
    }
  }
  
  # Rule 3: Known Bad Inputs
  rule {
    name     = "aws-managed-rules-known-bad-inputs"
    priority = 3
    
    override_action {
      none {}
    }
    
    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name               = "${var.project_name}-bad-inputs"
      sampled_requests_enabled  = true
    }
  }
  
  # Rule 4: SQL Injection Protection
  rule {
    name     = "aws-managed-rules-sql-injection"
    priority = 4
    
    override_action {
      none {}
    }
    
    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesSQLiRuleSet"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name               = "${var.project_name}-sqli-protection"
      sampled_requests_enabled  = true
    }
  }
  
  # Rule 5: Linux OS Protection
  rule {
    name     = "aws-managed-rules-linux"
    priority = 5
    
    override_action {
      none {}
    }
    
    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesLinuxRuleSet"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name               = "${var.project_name}-linux-protection"
      sampled_requests_enabled  = true
    }
  }
  
  # Rule 6: IP Allowlist (Optional)
  dynamic "rule" {
    for_each = var.ip_allowlist_enabled ? [1] : []
    
    content {
      name     = "ip-allowlist"
      priority = 10
      
      action {
        allow {}
      }
      
      statement {
        ip_set_reference_statement {
          arn = aws_wafv2_ip_set.allowlist[0].arn
        }
      }
      
      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name               = "${var.project_name}-ip-allowlist"
        sampled_requests_enabled  = true
      }
    }
  }
  
  # Rule 7: IP Blocklist (Optional)
  dynamic "rule" {
    for_each = var.ip_blocklist_enabled ? [1] : []
    
    content {
      name     = "ip-blocklist"
      priority = 11
      
      action {
        block {
          custom_response {
            response_code = 403
          }
        }
      }
      
      statement {
        ip_set_reference_statement {
          arn = aws_wafv2_ip_set.blocklist[0].arn
        }
      }
      
      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name               = "${var.project_name}-ip-blocklist"
        sampled_requests_enabled  = true
      }
    }
  }
  
  # Rule 8: Geo Blocking (Optional)
  dynamic "rule" {
    for_each = length(var.blocked_countries) > 0 ? [1] : []
    
    content {
      name     = "geo-blocking"
      priority = 12
      
      action {
        block {
          custom_response {
            response_code = 403
            custom_response_body_key = "geo_block_response"
          }
        }
      }
      
      statement {
        geo_match_statement {
          country_codes = var.blocked_countries
        }
      }
      
      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name               = "${var.project_name}-geo-blocking"
        sampled_requests_enabled  = true
      }
    }
  }
  
  # Custom response bodies
  custom_response_body {
    key          = "rate_limit_response"
    content      = var.rate_limit_response_body
    content_type = "APPLICATION_JSON"
  }
  
  custom_response_body {
    key          = "geo_block_response"
    content      = var.geo_block_response_body
    content_type = "APPLICATION_JSON"
  }
  
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name               = "${var.project_name}-waf"
    sampled_requests_enabled  = true
  }
  
  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-waf"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  )
}

# IP Set for Allowlist
resource "aws_wafv2_ip_set" "allowlist" {
  count = var.ip_allowlist_enabled ? 1 : 0
  
  name               = "${var.project_name}-ip-allowlist"
  scope              = var.scope
  ip_address_version = "IPV4"
  addresses          = var.allowed_ips
  
  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-ip-allowlist"
    }
  )
}

# IP Set for Blocklist
resource "aws_wafv2_ip_set" "blocklist" {
  count = var.ip_blocklist_enabled ? 1 : 0
  
  name               = "${var.project_name}-ip-blocklist"
  scope              = var.scope
  ip_address_version = "IPV4"
  addresses          = var.blocked_ips
  
  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-ip-blocklist"
    }
  )
}

# CloudWatch Log Group for WAF logs
resource "aws_cloudwatch_log_group" "waf_logs" {
  count = var.enable_logging ? 1 : 0
  
  name              = "/aws/wafv2/${var.project_name}-${var.environment}"
  retention_in_days = var.log_retention_days
  
  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-waf-logs"
    }
  )
}

# WAF Logging Configuration
resource "aws_wafv2_web_acl_logging_configuration" "waf_logging" {
  count = var.enable_logging ? 1 : 0
  
  resource_arn = aws_wafv2_web_acl.mcp_waf.arn
  
  log_destination_configs = [
    aws_cloudwatch_log_group.waf_logs[0].arn
  ]
  
  redacted_fields {
    single_header {
      name = "authorization"
    }
  }
  
  redacted_fields {
    single_header {
      name = "cookie"
    }
  }
}

# CloudWatch Alarms for WAF
resource "aws_cloudwatch_metric_alarm" "waf_blocked_requests" {
  count = var.enable_alarms ? 1 : 0
  
  alarm_name          = "${var.project_name}-waf-blocked-requests-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "BlockedRequests"
  namespace           = "AWS/WAFV2"
  period              = 300
  statistic           = "Sum"
  threshold           = var.blocked_requests_threshold
  alarm_description   = "This metric monitors WAF blocked requests"
  treat_missing_data  = "notBreaching"
  
  dimensions = {
    WebACL = aws_wafv2_web_acl.mcp_waf.name
    Region = var.region
    Rule   = "ALL"
  }
  
  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "waf_rate_limit" {
  count = var.enable_alarms ? 1 : 0
  
  alarm_name          = "${var.project_name}-waf-rate-limit-triggered"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "BlockedRequests"
  namespace           = "AWS/WAFV2"
  period              = 300
  statistic           = "Sum"
  threshold           = 100
  alarm_description   = "This metric monitors rate limit triggers"
  treat_missing_data  = "notBreaching"
  
  dimensions = {
    WebACL = aws_wafv2_web_acl.mcp_waf.name
    Region = var.region
    Rule   = "rate-limit-rule"
  }
  
  tags = var.tags
}
