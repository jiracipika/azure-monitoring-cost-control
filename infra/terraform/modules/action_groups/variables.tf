variable "name" {
  description = "Action group name."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group hosting the action group."
  type        = string
}

variable "short_name" {
  description = "Short name embedded in email/SMS notifications (max 12 characters)."
  type        = string

  validation {
    condition     = length(var.short_name) <= 12 && length(var.short_name) > 0
    error_message = "short_name must be 1-12 characters (Azure Action Group limit)."
  }
}

variable "alert_emails" {
  description = "Recipient addresses for every alert in this stack. Replace the reserved example.invalid default before any approved deployment."
  type        = list(string)
  default     = ["ops-team@example.invalid"]

  validation {
    condition = length(var.alert_emails) > 0 && alltrue(
      [for e in var.alert_emails : can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", e))]
    )
    error_message = "alert_emails must contain at least one valid email address (action groups require a receiver)."
  }
}

variable "tags" {
  description = "Governance tags applied to the action group."
  type        = map(string)
  default     = {}
}
