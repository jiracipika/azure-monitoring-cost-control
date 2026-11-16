# Action group: the single notification hub every alert in this repo
# targets (query alerts, service health, budget notifications). Email
# receivers only — no webhooks, SMS or runbooks, so nothing here can
# execute code or reach a network endpoint.
locals {
  # email -> stable positional suffix, so receiver names stay readable
  # and deterministic regardless of email format.
  receivers = { for i, email in var.alert_emails : email => i }
}

resource "azurerm_monitor_action_group" "this" {
  name                = var.name
  resource_group_name = var.resource_group_name
  short_name          = var.short_name

  dynamic "email_receiver" {
    for_each = local.receivers
    content {
      name                    = format("email-%02d", email_receiver.value + 1)
      email_address           = email_receiver.key
      use_common_alert_schema = true
    }
  }

  tags = var.tags
}
