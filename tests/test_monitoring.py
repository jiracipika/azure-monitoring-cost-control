"""Monitoring & cost-control invariants — parsed from the actual Terraform
sources with REGEX assertions that survive `terraform fmt` realignment.

Covers: workspace retention/quota caps, data collection streams, diagnostic
destination safety (workspace only, never storage), action group shape,
alert rule wiring (data source, action group, auto-mitigation, thresholds),
Service Health coverage, budget threshold ladder, deploy gating and CI
safety.
"""

from pathlib import Path
import re
import unittest

import monitor_simulator as ms

ROOT = Path(__file__).resolve().parents[1]
TF = ROOT / "infra" / "terraform"


def read(rel: str) -> str:
    return (TF / rel).read_text()


class WorkspaceCostCaps(unittest.TestCase):
    """The workspace itself must be the first cost brake."""

    def test_retention_variable_validated_into_30_730_band(self):
        variables = read("variables.tf")
        self.assertRegex(
            variables,
            r'"log_analytics_retention_days"\s*\{[^}]*?30[^}]*?730',
            "retention must be validated into the cheapest interactive band",
        )

    def test_workspace_wires_retention_quota_and_lockdown(self):
        src = read("modules/observability/main.tf")
        self.assertRegex(src, r'sku\s*=\s*"PerGB2018"')
        self.assertRegex(src, r"retention_in_days\s*=\s*var\.retention_in_days")
        self.assertRegex(src, r"daily_quota_gb\s*=\s*var\.daily_quota_gb")
        self.assertRegex(read("modules/observability/variables.tf"),
                         r"var\.daily_quota_gb > 0",
                         "the quota cap must itself be validated")
        self.assertRegex(src, r"local_authentication_enabled\s*=\s*false",
                         "workspace-local keys must be disabled (Entra ID only)")
        self.assertRegex(src, r"internet_query_enabled\s*=\s*false",
                         "public query endpoint must stay closed")

    def test_perf_sampling_floor_is_60s(self):
        self.assertIn(
            "var.perf_sampling_seconds >= 60",
            read("modules/data_collection/variables.tf"),
            "sub-minute counter sampling multiplies ingestion cost",
        )


class DataCollectionStreams(unittest.TestCase):
    def test_dcr_collects_perf_and_syslog_only(self):
        src = read("modules/data_collection/main.tf")
        self.assertEqual(ms.dcr_tables(), {"Perf", "Syslog"})

    def test_syslog_levels_are_error_and_worse(self):
        src = read("modules/data_collection/main.tf")
        levels = re.search(r"log_levels\s*=\s*\[(.*?)\]", src, re.S).group(1)
        for level in ("Alert", "Critical", "Emergency", "Error", "Warning"):
            self.assertIn(f'"{level}"', levels)
        for noisy in ("Debug", "Info", "Notice"):
            self.assertNotIn(f'"{noisy}"', levels,
                             f"{noisy} syslog would inflate ingestion cost")

    def test_destination_is_workspace_only(self):
        src = read("modules/data_collection/main.tf")
        self.assertRegex(src, r"log_analytics\s*\{")
        self.assertNotIn("storage_blob", src)
        self.assertNotIn("event_hub", src)

    def test_root_wires_dcr_to_workspace(self):
        self.assertRegex(
            read("main.tf"),
            r"workspace_resource_id\s*=\s*one\(module\.observability\[\*\]\.workspace_id\)",
        )


class DiagnosticsSafety(unittest.TestCase):
    """Negative safety: telemetry must never land in a storage container."""

    def test_no_storage_account_resource_or_destination_anywhere(self):
        for path in TF.rglob("*.tf"):
            src = path.read_text()
            self.assertNotRegex(src, r'resource\s+"azurerm_storage_account"',
                                f"{path.name}: storage accounts are out of scope")
            self.assertNotIn("storage_account_id", src,
                             f"{path.name}: diagnostic settings must not target storage")

    def test_diagnostics_aggregate_into_workspace_with_dedicated_tables(self):
        src = read("modules/diagnostics/main.tf")
        self.assertRegex(src, r'log_analytics_destination_type\s*=\s*"Dedicated"')
        self.assertRegex(src, r"log_analytics_workspace_id\s*=\s*var\.workspace_resource_id")

    def test_workspace_self_audit_wired_from_root(self):
        main = read("main.tf")
        self.assertRegex(main, r'target_resource_id\s*=\s*one\(module\.observability\[\*\]\.workspace_id\)')
        self.assertRegex(main, r'log_categories\s*=\s*\["Audit",\s*"Usage"\]')


class ActionGroupShape(unittest.TestCase):
    def test_email_receivers_generated_from_variable_with_common_schema(self):
        src = read("modules/action_groups/main.tf")
        self.assertRegex(src, r'dynamic\s+"email_receiver"')
        self.assertRegex(src, r"use_common_alert_schema\s*=\s*true")

    def test_short_name_within_azure_12_char_limit(self):
        main = read("main.tf")
        short = re.search(r'short_name\s*=\s*"([^"]+)"', main).group(1)
        self.assertLessEqual(len(short), 12)

    def test_default_alert_email_is_reserved_example_domain(self):
        variables = read("variables.tf")
        block = re.search(r'variable "alert_emails" \{(.*?)\n\}', variables, re.S).group(1)
        self.assertRegex(block, r"example\.invalid", "no real addresses may be committed")


class QueryAlertWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = {r["label"]: r for r in ms.load_query_rules()}
        cls.main = read("main.tf")

    def test_exactly_two_query_alert_rules_parsed(self):
        self.assertEqual(set(self.rules), {"high_cpu", "syslog_error_burst"})

    def test_root_wires_data_source_and_action_group(self):
        self.assertRegex(self.main,
                         r"workspace_data_source_id\s*=\s*one\(module\.observability\[\*\]\.workspace_id\)")
        self.assertRegex(self.main,
                         r"action_group_id\s*=\s*one\(module\.action_groups\[\*\]\.action_group_id\)")

    def test_every_query_alert_references_the_shared_action_group(self):
        src = read("modules/alert_rules/main.tf")
        self.assertEqual(len(re.findall(r"action_group\s*=\s*\[var\.action_group_id\]", src)), 2)

    def test_rules_auto_mitigate_with_valid_severities(self):
        for label, rule in self.rules.items():
            self.assertTrue(rule["auto_mitigation"], f"{label} must auto-mitigate")
            self.assertIn(rule["severity"], (0, 1, 2, 3, 4), label)
        self.assertNotEqual(self.rules["high_cpu"]["severity"],
                            self.rules["syslog_error_burst"]["severity"],
                            "escalation must be distinguishable by severity")

    def test_window_is_multiple_of_frequency(self):
        for label, rule in self.rules.items():
            self.assertEqual(rule["window_min"] % rule["frequency_min"], 0, label)
            self.assertGreater(rule["window_min"], rule["frequency_min"], label)

    def test_thresholds_are_positive_and_operator_strict(self):
        for label, rule in self.rules.items():
            self.assertGreater(rule["threshold"], 0, label)
            self.assertEqual(rule["operator"], "GreaterThan", label)

    def test_alert_queries_reference_only_ingested_tables(self):
        ingested = ms.dcr_tables()
        for label, rule in self.rules.items():
            self.assertTrue(rule["query"].strip(), f"{label}: empty query")
            used = ms.kql_tables(rule["query"])
            self.assertTrue(used, f"{label}: no recognizable table")
            self.assertLessEqual(used, ingested,
                                 f"{label} queries tables the DCR never ingests")


class ServiceHealthCoverage(unittest.TestCase):
    def test_activity_log_alert_covers_service_health(self):
        src = read("modules/alert_rules/main.tf")
        self.assertRegex(src, r'category\s*=\s*"ServiceHealth"')
        events = re.search(r"events\s*=\s*\[(.*?)\]", src, re.S).group(1)
        for event in ("Incident", "ActionRequired", "Maintenance"):
            self.assertIn(f'"{event}"', events)
        self.assertRegex(src, r"locations\s*=\s*\[var\.location\]",
                         "health events filtered to the portfolio region")

    def test_scoped_to_subscription(self):
        self.assertRegex(read("modules/alert_rules/main.tf"),
                         r'scopes\s*=\s*\["/subscriptions/\$\{var\.subscription_id\}"\]')


class BudgetGuardrails(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = read("modules/budget/main.tf")
        cls.config = ms.load_budget_config()

    def test_thresholds_escalate_actuals_then_forecast(self):
        thresholds = sorted(t for t in self.config["actual_thresholds"])
        self.assertLess(thresholds[0], thresholds[-1], "actual thresholds must escalate")
        self.assertEqual(len(set(self.config["actual_thresholds"])), len(thresholds),
                         "thresholds must be unique")
        self.assertGreater(self.config["forecast_threshold"],
                           self.config["actual_thresholds"][-1],
                           "forecast early-warning sits above the last actual rung")

    def test_module_declares_one_forecast_notification(self):
        self.assertEqual(len(re.findall(r'threshold_type\s*=\s*"Forecasted"', self.src)), 1)
        self.assertEqual(len(re.findall(r'threshold_type\s*=\s*"Actual"', self.src)), 1,
                         "actual thresholds come from the validated variable (one dynamic block)")

    def test_notifications_reach_emails_and_action_group(self):
        self.assertRegex(self.src, r"contact_emails\s*=\s*var\.alert_emails")
        self.assertRegex(self.src, r"contact_groups\s*=\s*var\.action_group_id != \"\" \? \[var\.action_group_id\] : \[\]")

    def test_monthly_grain_and_future_start(self):
        self.assertRegex(self.src, r'time_grain\s*=\s*"Monthly"')
        start = re.search(r'start_date\s*=\s*"([^"]+)"', self.src).group(1)
        self.assertRegex(start, r"^\d{4}-\d{2}-\d{2}T00:00:00Z$")
        self.assertGreater(start, "2026-11-16T00:00:00Z", "budgets cannot start in the past")

    def test_root_wires_budget_to_observability_resource_group(self):
        self.assertRegex(read("main.tf"),
                         r"resource_group_id\s*=\s*one\(module\.observability\[\*\]\.resource_group_id\)")

    def test_amount_must_be_positive_variable_validation(self):
        self.assertRegex(read("variables.tf"),
                         r'"budget_amount"\s*\{[^}]*?var\.budget_amount > 0')


class WorkbookGovernance(unittest.TestCase):
    def test_workbook_queries_cover_cpu_syslog_usage_and_tags(self):
        queries = " ".join(ms.workbook_queries())
        self.assertIn("Perf", queries)
        self.assertIn("Syslog", queries)
        self.assertIn("Usage", queries)
        self.assertRegex(read("modules/workbook/main.tf"),
                         r"isempty\(tags\['%s'\]\)",
                         "tag-governance query must be generated from required tags")

    def test_workbook_locked_flag_false_and_bound_to_workspace(self):
        src = read("modules/workbook/main.tf")
        self.assertRegex(src, r"isLocked\s*=\s*false")
        self.assertRegex(src, r"fallbackResourceIds\s*=\s*\[var\.workspace_resource_id\]")

    def test_required_tags_variable_defaults_to_environment_and_cost_center(self):
        variables = read("variables.tf")
        block = re.search(r'variable "required_tags" \{(.*?)\n\}', variables, re.S).group(1)
        self.assertIn('"environment"', block)
        self.assertIn('"costCenter"', block)


class DeployGateAndSafety(unittest.TestCase):
    MODULES = ["action_groups", "alert_rules", "budget", "data_collection",
               "diagnostics", "observability", "workbook"]

    def test_deploy_disabled_by_default(self):
        self.assertRegex(read("variables.tf"), r'"deploy_enabled"\s*\{[^}]*?default\s*=\s*false')

    def test_every_root_module_is_gated(self):
        main = read("main.tf")
        self.assertEqual(main.count("var.deploy_enabled ? 1 : 0"), len(self.MODULES))
        for module in self.MODULES:
            self.assertRegex(main, rf'module "{module}"')

    def test_module_inventory_matches_design(self):
        found = sorted(p.name for p in (TF / "modules").iterdir() if p.is_dir())
        self.assertEqual(found, self.MODULES)

    def test_child_modules_declare_required_providers(self):
        for module in self.MODULES:
            src = read(f"modules/{module}/versions.tf")
            self.assertIn("required_providers", src, module)
            self.assertRegex(src, r"hashicorp/azurerm", module)

    def test_placeholder_subscription_and_tenant_ids(self):
        variables = read("variables.tf")
        for var in ("azure_subscription_id", "azure_tenant_id"):
            m = re.search(rf'variable "{var}" \{{[^}}]*?default\s*=\s*"([^"]+)"', variables)
            self.assertEqual(m.group(1), "00000000-0000-0000-0000-000000000000", var)

    def test_no_real_guids_anywhere_in_terraform(self):
        guid = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
        for path in TF.rglob("*.tf"):
            for match in guid.findall(path.read_text()):
                self.assertEqual(match, "00000000-0000-0000-0000-000000000000",
                                 f"unexpected GUID {match} in {path}")

    def test_environment_tfvars_keeps_gate_closed(self):
        self.assertRegex(read("environments/dev.tfvars"), r"deploy_enabled\s*=\s*false")


class CiSafety(unittest.TestCase):
    def test_workflow_has_no_apply_destroy_or_login(self):
        wf = (ROOT / ".github/workflows/validate.yml").read_text()
        self.assertNotIn("terraform apply", wf)
        self.assertNotIn("terraform destroy", wf)
        self.assertNotIn("az login", wf)
        self.assertNotIn("id-token: write", wf)

    def test_workflow_permissions_read_only(self):
        self.assertIn("contents: read", (ROOT / ".github/workflows/validate.yml").read_text())

    def test_terraform_version_pinned(self):
        wf = (ROOT / ".github/workflows/validate.yml").read_text()
        self.assertRegex(wf, r"terraform_version:\s*'\d+\.\d+\.\d+'")


class DiagramMatchesImplementation(unittest.TestCase):
    def test_diagram_names_the_implemented_pieces(self):
        mmd = (ROOT / "diagrams/architecture.mmd").read_text().lower()
        self.assertIn("flowchart", mmd)
        for needle in ("workspace", "data collection", "action group",
                       "budget", "workbook", "service health", "tag"):
            self.assertIn(needle, mmd, f"diagram must mention {needle}")


if __name__ == "__main__":
    unittest.main()
