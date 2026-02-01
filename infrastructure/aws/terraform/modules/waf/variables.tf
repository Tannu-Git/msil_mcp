variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "msil-mcp"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "scope" {
  description = "WAF scope - REGIONAL for ALB/API Gateway, CLOUDFRONT for CloudFront"
  type        = string
  default     = "REGIONAL"
  
  validation {
    condition     = contains(["REGIONAL", "CLOUDFRONT"], var.scope)
    error_message = "Scope must be either REGIONAL or CLOUDFRONT"
  }
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "rate_limit" {
  description = "Rate limit per IP (requests per 5 minutes)"
  type        = number
  default     = 2000
}

variable "ip_allowlist_enabled" {
  description = "Enable IP allowlist"
  type        = bool
  default     = false
}

variable "allowed_ips" {
  description = "List of allowed IP addresses (CIDR notation)"
  type        = list(string)
  default     = []
}

variable "ip_blocklist_enabled" {
  description = "Enable IP blocklist"
  type        = bool
  default     = false
}

variable "blocked_ips" {
  description = "List of blocked IP addresses (CIDR notation)"
  type        = list(string)
  default     = []
}

variable "blocked_countries" {
  description = "List of country codes to block (ISO 3166-1 alpha-2)"
  type        = list(string)
  default     = []
}

variable "enable_logging" {
  description = "Enable WAF logging to CloudWatch"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "enable_alarms" {
  description = "Enable CloudWatch alarms for WAF"
  type        = bool
  default     = true
}

variable "blocked_requests_threshold" {
  description = "Threshold for blocked requests alarm"
  type        = number
  default     = 1000
}

variable "rate_limit_response_body" {
  description = "Custom response body for rate limit violations"
  type        = string
  default     = <<-EOT
    {
      "error": "rate_limit_exceeded",
      "message": "Too many requests. Please try again later.",
      "retry_after": 300
    }
  EOT
}

variable "geo_block_response_body" {
  description = "Custom response body for geo blocking"
  type        = string
  default     = <<-EOT
    {
      "error": "geo_blocked",
      "message": "Access from your location is not allowed."
    }
  EOT
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}
