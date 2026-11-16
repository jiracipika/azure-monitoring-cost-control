variable "resource_group_name" {
  description = "Monitoring resource group holding the workspace and alerting resources."
  type        = string
}

variable "workspace_name" {
  description = "Central Log Analytics workspace receiving all telemetry."
  type        = string
}

variable "location" {
  description = "Azure region for the monitoring stack."
  type        = string
}

variable "retention_in_days" {
  description = "Interactive retention band for workspace data (30 days is the cheapest)."
  type        = number

  validation {
    condition     = var.retention_in_days >= 30 && var.retention_in_days <= 730
    error_message = "retention_in_days must be between 30 and 730."
  }
}

variable "daily_quota_gb" {
  description = "Daily ingestion cap in GB. Stops ingestion beyond the cap — the workspace-level cost brake."
  type        = number
  default     = 5

  validation {
    condition     = var.daily_quota_gb > 0
    error_message = "daily_quota_gb must be positive (use a larger budget instead of disabling the cap)."
  }
}

variable "internet_ingestion_enabled" {
  description = "Public ingestion endpoint. Required true until a private data collection endpoint exists; queries are blocked either way."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Governance tags applied to every resource in the module."
  type        = map(string)
  default     = {}
}
