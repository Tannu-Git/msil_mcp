variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "repositories" {
  description = "List of ECR repository names"
  type        = list(string)
}

variable "cross_account_access_enabled" {
  description = "Enable cross-account access"
  type        = bool
  default     = false
}

variable "cross_account_arns" {
  description = "List of ARNs for cross-account access"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
