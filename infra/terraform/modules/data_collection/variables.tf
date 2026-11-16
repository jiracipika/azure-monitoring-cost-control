variable "name" {
  description = "Data collection rule name."
  type        = string
}

variable "location" {
  description = "Azure region for the data collection rule."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group hosting the data collection rule."
  type        = string
}

variable "workspace_resource_id" {
  description = "Central Log Analytics workspace that receives the collected streams."
  type        = string
}

variable "perf_sampling_seconds" {
  description = "Counter sampling interval. 60s keeps Perf-table volume (and cost) low."
  type        = number
  default     = 60

  validation {
    condition     = var.perf_sampling_seconds >= 60
    error_message = "perf_sampling_seconds must be at least 60 — sub-minute sampling multiplies ingestion cost."
  }
}

variable "tags" {
  description = "Governance tags applied to the data collection rule."
  type        = map(string)
  default     = {}
}
