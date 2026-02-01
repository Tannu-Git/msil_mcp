# AWS WAF Module for MSIL MCP Server

This Terraform module creates an AWS WAF Web ACL with comprehensive L7 protection.

## Features

- **Rate Limiting**: 2000 requests per 5 minutes per IP (configurable)
- **AWS Managed Rules**: 
  - Core Rule Set (CRS)
  - Known Bad Inputs
  - SQL Injection Protection
  - Linux OS Protection
- **IP Allowlist/Blocklist**: Optional IP-based access control
- **Geo Blocking**: Optional country-based blocking
- **CloudWatch Logging**: Full request logging with PII redaction
- **CloudWatch Alarms**: Automated alerting for security events

## Usage

```hcl
module "waf" {
  source = "./modules/waf"
  
  project_name = "msil-mcp"
  environment  = "prod"
  
  # Rate limiting
  rate_limit = 2000
  
  # IP allowlist (optional)
  ip_allowlist_enabled = true
  allowed_ips = [
    "203.0.113.0/24",  # Office network
    "198.51.100.0/24"  # VPN network
  ]
  
  # Geo blocking (optional)
  blocked_countries = ["CN", "RU"]  # Block China and Russia
  
  # Logging
  enable_logging      = true
  log_retention_days  = 90
  
  # Alarms
  enable_alarms               = true
  blocked_requests_threshold  = 1000
  
  tags = {
    Project     = "MSIL MCP"
    CostCenter  = "Engineering"
    Compliance  = "SOC2"
  }
}

# Associate with ALB
resource "aws_wafv2_web_acl_association" "alb" {
  resource_arn = aws_lb.main.arn
  web_acl_arn  = module.waf.web_acl_arn
}

# Associate with API Gateway (REST API)
resource "aws_wafv2_web_acl_association" "api_gateway" {
  resource_arn = aws_api_gateway_stage.prod.arn
  web_acl_arn  = module.waf.web_acl_arn
}
```

## WAF Rules

### Priority 1: Rate Limiting
- **Limit**: 2000 requests per 5 minutes per IP
- **Action**: Block with 429 response
- **Scope**: Excludes health check endpoints

### Priority 2: AWS Common Rule Set
- Cross-site scripting (XSS) protection
- SQL injection protection
- Path traversal protection
- Command injection protection

### Priority 3: Known Bad Inputs
- Protection against known malicious patterns
- CVE-based rules

### Priority 4: SQL Injection
- Advanced SQLi protection
- Multiple evasion technique detection

### Priority 5: Linux OS Protection
- Command injection for Linux
- Local file inclusion (LFI)
- Remote file inclusion (RFI)

### Priority 10: IP Allowlist (Optional)
- Allow traffic from specific IPs
- Bypass all other rules

### Priority 11: IP Blocklist (Optional)
- Block traffic from specific IPs
- 403 response

### Priority 12: Geo Blocking (Optional)
- Block traffic from specific countries
- ISO 3166-1 alpha-2 country codes

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| project_name | Project name | string | "msil-mcp" | no |
| environment | Environment | string | "dev" | no |
| scope | WAF scope (REGIONAL/CLOUDFRONT) | string | "REGIONAL" | no |
| rate_limit | Requests per 5 minutes per IP | number | 2000 | no |
| ip_allowlist_enabled | Enable IP allowlist | bool | false | no |
| allowed_ips | Allowed IP CIDRs | list(string) | [] | no |
| ip_blocklist_enabled | Enable IP blocklist | bool | false | no |
| blocked_ips | Blocked IP CIDRs | list(string) | [] | no |
| blocked_countries | Country codes to block | list(string) | [] | no |
| enable_logging | Enable CloudWatch logging | bool | true | no |
| log_retention_days | Log retention in days | number | 30 | no |
| enable_alarms | Enable CloudWatch alarms | bool | true | no |

## Outputs

| Name | Description |
|------|-------------|
| web_acl_id | WAF Web ACL ID |
| web_acl_arn | WAF Web ACL ARN |
| web_acl_capacity | WAF capacity used |
| ip_allowlist_arn | IP allowlist ARN |
| ip_blocklist_arn | IP blocklist ARN |
| log_group_name | CloudWatch log group name |

## Monitoring

### CloudWatch Metrics
- `BlockedRequests`: Total blocked requests
- `AllowedRequests`: Total allowed requests
- `CountedRequests`: Requests that matched rules but weren't blocked

### CloudWatch Alarms
1. **High Blocked Requests**: Triggers when blocked requests exceed threshold
2. **Rate Limit Triggered**: Triggers when rate limiting is activated

### CloudWatch Logs
- Full request/response logging
- PII redaction (Authorization, Cookie headers)
- Retention configurable (default: 30 days)

## Cost Estimation

### WAF Pricing (us-east-1)
- Web ACL: $5.00/month
- Rules: $1.00/month per rule (8 rules = $8.00/month)
- Requests: $0.60 per million requests
- Rule evaluations: Included

### Example Monthly Cost
- 100M requests/month
- 8 active rules
- CloudWatch logging enabled

**Total**: ~$73/month
- Web ACL: $5
- Rules: $8
- Requests: $60 (100M * $0.60)

## Security Best Practices

1. **Start with Monitor Mode**: Set rules to `count` initially
2. **Review Logs**: Analyze blocked requests before enforcing
3. **IP Allowlist**: Use for known trusted IPs only
4. **Geo Blocking**: Enable only if required by compliance
5. **Rate Limiting**: Tune based on legitimate traffic patterns
6. **Regular Updates**: AWS Managed Rules auto-update

## Integration with MCP Server

Add to MCP server configuration:

```python
# app/config.py
WAF_ENABLED: bool = True
WAF_WEB_ACL_ARN: Optional[str] = None
WAF_RATE_LIMIT: int = 2000
WAF_IP_ALLOWLIST_ENABLED: bool = False
WAF_ALLOWED_IPS: str = ""  # Comma-separated CIDRs
```

## Troubleshooting

### False Positives
1. Check CloudWatch logs for blocked requests
2. Identify the rule blocking legitimate traffic
3. Add exceptions or adjust thresholds

### High Blocked Requests
1. Review source IPs in logs
2. Verify if attack or misconfiguration
3. Update IP blocklist if needed

### Performance Impact
- WAF adds ~1-5ms latency
- Minimal impact on application performance
- Scales automatically with traffic

## References

- [AWS WAF Documentation](https://docs.aws.amazon.com/waf/)
- [AWS Managed Rules](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups.html)
- [WAF Best Practices](https://docs.aws.amazon.com/waf/latest/developerguide/waf-chapter.html)
