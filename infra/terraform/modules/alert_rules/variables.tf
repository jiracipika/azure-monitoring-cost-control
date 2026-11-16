variable "resource_group_name" {
  description = "Resource group hosting the alert rules."
  type        = string
}

variable "location" {
  description = "Azure region for the query alert rules and the Service Health event filter."
  type        = string
}

variable "workspace_data_source_id" {
  description = "Central workspace the alert queries run against (data_source_id)."
  type        = string
}

variable "action_group_id" {
  description = "Shared action group every alert notifies."
  type        = string
}

variable "subscription_id" {
  description = "Subscription scope for the Service Health activity log alert. Placeholder default passes offline validation only."
  type        = string
  default     = "00000000-0000-0000-0000-000000000000"
}

variable "high_cpu_threshold_pct" {
  description = "Sustained average CPU percentage that fires the high-CPU alert."
  type        = number
  default     = 85

  validation {
    condition     = var.high_cpu_threshold_pct > 0 && var.high_cpu_threshold_pct <= 100
    error_message = "high_cpu_threshold_pct must be a percentage in (0, 100]."
  }
}

variable "syslog_error_threshold" {
  description = "Error-or-worse syslog records per host per 15-minute window that fires the burst alert."
  type        = number
  default     = 50

  validation {
    condition     = var.syslog_error_threshold > 0
    error_message = "syslog_error_threshold must be positive."
  }
}

variable "tags" {
  description = "Governance tags applied to every alert rule."
  type        = map(string)
  default     = {}
}
