variable "deploy_enabled" {
  description = "Approval guard. When false, `terraform plan` proposes zero Azure resources."
  type        = bool
  default     = false
}

variable "location" {
  description = "Primary portfolio region."
  type        = string
  default     = "canadacentral"
}

variable "azure_subscription_id" {
  description = "Target subscription (Service Health alert scope). Placeholder default passes offline validation only."
  type        = string
  default     = "00000000-0000-0000-0000-000000000000"
}

variable "azure_tenant_id" {
  description = "Tenant owning the subscription. Placeholder default passes offline validation only."
  type        = string
  default     = "00000000-0000-0000-0000-000000000000"
}

variable "log_analytics_retention_days" {
  description = "Workspace interactive retention band (30 days is the cheapest)."
  type        = number
  default     = 30

  validation {
    condition     = var.log_analytics_retention_days >= 30 && var.log_analytics_retention_days <= 730
    error_message = "log_analytics_retention_days must be between 30 and 730."
  }
}

variable "daily_quota_gb" {
  description = "Daily ingestion cap (GB). The primary runaway-cost brake at workspace level."
  type        = number
  default     = 5

  validation {
    condition     = var.daily_quota_gb > 0
    error_message = "daily_quota_gb must be positive."
  }
}

variable "perf_sampling_seconds" {
  description = "Perf counter sampling interval; >= 60s keeps ingestion volume low."
  type        = number
  default     = 60

  validation {
    condition     = var.perf_sampling_seconds >= 60
    error_message = "perf_sampling_seconds must be at least 60."
  }
}

variable "budget_amount" {
  description = "Monthly budget (CAD) for the monitoring resource group. Alerts only — does not stop billing."
  type        = number
  default     = 20

  validation {
    condition     = var.budget_amount > 0
    error_message = "budget_amount must be positive."
  }
}

variable "budget_actual_thresholds" {
  description = "Escalating Actual-spend notification thresholds (percent of budget)."
  type        = list(number)
  default     = [50, 80]

  validation {
    condition     = alltrue([for t in var.budget_actual_thresholds : t > 0 && t <= 1000])
    error_message = "every budget threshold must be in (0, 1000] percent."
  }

  validation {
    condition = alltrue(
      [for i, t in var.budget_actual_thresholds : i == 0 ? true : t > var.budget_actual_thresholds[i - 1]]
    )
    error_message = "budget_actual_thresholds must be strictly increasing."
  }
}

variable "budget_forecast_threshold" {
  description = "Forecasted-spend threshold (percent) — the early warning before the cap."
  type        = number
  default     = 100

  validation {
    condition     = var.budget_forecast_threshold > 0 && var.budget_forecast_threshold <= 1000
    error_message = "budget_forecast_threshold must be in (0, 1000] percent."
  }
}

variable "alert_emails" {
  description = "Recipients of every alert and budget notification. Replace the reserved example.invalid default before any approved deployment."
  type        = list(string)
  default     = ["ops-team@example.invalid"]
}

variable "required_tags" {
  description = "Tags every resource must carry; drives tag-governance reporting in the workbook."
  type        = list(string)
  default     = ["environment", "costCenter"]
}

variable "tags" {
  description = "Base governance tags merged into every resource."
  type        = map(string)
  default = {
    environment = "portfolio-lab"
    managed_by  = "terraform"
  }
}
