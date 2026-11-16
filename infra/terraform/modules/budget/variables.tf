variable "resource_group_id" {
  description = "Resource group the budget guards."
  type        = string
}

variable "resource_group_name" {
  description = "Basis of the budget resource name."
  type        = string
}

variable "amount" {
  description = "Monthly budget for the resource group (CAD). Alerts only — does not stop billing."
  type        = number

  validation {
    condition     = var.amount > 0
    error_message = "amount must be positive."
  }
}

variable "actual_thresholds" {
  description = "Escalating Actual-spend notification thresholds in percent of the monthly budget."
  type        = list(number)
  default     = [50, 80]

  validation {
    condition     = length(var.actual_thresholds) > 0 && alltrue([for t in var.actual_thresholds : t > 0 && t <= 1000])
    error_message = "every actual threshold must be in (0, 1000] percent."
  }

  validation {
    condition = alltrue(
      [for i, t in var.actual_thresholds : i == 0 ? true : t > var.actual_thresholds[i - 1]]
    )
    error_message = "actual_thresholds must be strictly increasing so escalation order is deterministic."
  }
}

variable "forecast_threshold" {
  description = "Forecasted end-of-month spend threshold in percent — the early warning before the cap."
  type        = number
  default     = 100

  validation {
    condition     = var.forecast_threshold > 0 && var.forecast_threshold <= 1000
    error_message = "forecast_threshold must be in (0, 1000] percent."
  }
}

variable "alert_emails" {
  description = "Email recipients for budget notifications."
  type        = list(string)
}

variable "action_group_id" {
  description = "Action group that also receives budget notifications. Empty string disables the wiring."
  type        = string
  default     = ""
}
