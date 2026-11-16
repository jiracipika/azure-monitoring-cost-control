variable "name" {
  description = "Diagnostic setting name (unique per target resource)."
  type        = string
}

variable "target_resource_id" {
  description = "Resource whose platform telemetry is aggregated into the workspace."
  type        = string
}

variable "workspace_resource_id" {
  description = "Central Log Analytics workspace receiving the telemetry."
  type        = string
}

variable "log_categories" {
  description = "Log categories to collect (e.g. Audit/Usage for a Log Analytics workspace)."
  type        = list(string)
  default     = []
}

variable "metric_categories" {
  description = "Platform metric categories to collect. Empty for resources that only expose logs."
  type        = list(string)
  default     = []
}
