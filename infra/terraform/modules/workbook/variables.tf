variable "name" {
  description = "Workbook resource name."
  type        = string
}

variable "display_name" {
  description = "Human-readable workbook title shown in the Workbooks gallery."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group hosting the workbook."
  type        = string
}

variable "location" {
  description = "Azure region for the workbook."
  type        = string
}

variable "workspace_resource_id" {
  description = "Central workspace the workbook queries are bound to."
  type        = string
}

variable "required_tags" {
  description = "Governance tags every resource must carry; drives the untagged-resources query."
  type        = list(string)
  default     = ["environment", "costCenter"]

  validation {
    condition     = length(var.required_tags) > 0
    error_message = "required_tags cannot be empty — tag governance is part of the cost model."
  }
}

variable "tags" {
  description = "Governance tags applied to the workbook resource itself."
  type        = map(string)
  default     = {}
}
