provider "azurerm" {
  # Placeholders satisfy offline validation; set ARM_SUBSCRIPTION_ID /
  # ARM_TENANT_ID or tfvars values before any approved deployment.
  subscription_id = var.azure_subscription_id
  tenant_id       = var.azure_tenant_id
  features {}
}
