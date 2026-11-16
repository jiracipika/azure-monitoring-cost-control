# Tests and verification

Every entry below is an actual command execution with its real result. Azure
live deployment: **NOT RUN** (no authorization; offline `terraform plan`
with default variables proposes only the `status` output — zero resources,
deploy gate holds — then stops at the provider authorizer because the
sandbox has no `az` CLI or credentials: expected, not a code failure).

## 2026-11-16T16:19Z — local offline battery (GLM/ZCode session, terraform v1.9.8, azurerm 4.81.0)

| Command | Result | Evidence |
|---|---|---|
| `python3 -m unittest discover -s tests` | **PASS** | `Ran 74 tests ... OK` |
| `terraform -chdir=infra/terraform fmt -check -recursive` | **PASS** | exit 0 |
| `terraform -chdir=infra/terraform init -backend=false -input=false` | **PASS** | azurerm v4.81.0 (lock file); 7 modules loaded |
| `terraform -chdir=infra/terraform validate` | **PASS** | `Success! The configuration is valid.` |
| `terraform -chdir=infra/terraform plan -input=false -refresh=false` | **PARTIAL (expected)** | proposes only `+ status = "implemented-offline-gated"` (zero resources — deploy gate holds); then errors `could not configure AzureCli Authorizer: az: executable file not found` |

Test composition: 3 scaffold safety + 42 static HCL invariants
(test_monitoring.py) + 18 simulator scenarios (test_monitor_sim.py via
monitor_simulator.py, which parses the real budget/alert HCL) + 11
security-scanner checks (test_security_scan.py).

### Failures found and fixed during this run (real history)

1. **CI was red on arrival** (runs 43875648359, 43875805580): `fmt -check`
   exit 3 on scaffold `variables.tf` — fixed with `terraform fmt -recursive`
   (commit 829e66b).
2. Fixing fmt exposed a second latent failure (run 43903676726):
   test_scaffold asserted the exact string `default = false`, which
   `terraform fmt` realigns to `default     = false`. Test rewritten to a
   regex assertion (commit 5f9b773) — the repo rule "regex, not exact
   string" now starts at the scaffold level.
3. First `terraform validate` of the new modules failed with 7 type errors,
   all from 4.x-vs-3.x attribute-shape differences caught by validation
   BEFORE any commit: `frequency`/`time_window` on scheduled query rules are
   plain numbers (minutes), not `PT5M` ISO strings; `action.action_group`
   is a set of strings (`[var.action_group_id]`); `enabled_metric` has no
   `retention_policy` sub-block (only `enabled_log` does). All corrected
   against the installed provider schema.
4. First unittest run (74 tests): 3 failures —
   (a) the no-storage negative test tripped on the word `storage_account_id`
   appearing in a COMMENT in modules/diagnostics (comment reworded; the
   test itself is correct — comments are scanned deliberately);
   (b) the diagram test failed because diagrams/architecture.mmd was still
   the scaffold stub — rewritten to match the implemented modules (stale
   documentation is exactly what that test exists to catch);
   (c) `environments/dev.tfvars` was not yet git-tracked, so the hygiene
   scan correctly refused to pass until it was staged.

### Schema verification method (as required)

Every resource attribute was verified against the installed provider
before/while writing HCL: `terraform -chdir=infra/terraform providers
schema -json` (azurerm 4.81.0). Notable findings that shaped the code:
workbooks are `azurerm_application_insights_workbook` with `data_json`
(`azurerm_monitor_workbook` does NOT exist in 4.81.0); scheduled query
rules use `data_source_id` + `action{action_group(set)}` + `trigger`
blocks; action-group email receivers use `use_common_alert_schema`; DCR
syslog sources use `facility_names` + `log_levels`; budget `notification`
blocks support `contact_groups` (action-group ids) alongside
`contact_emails`.

## GitHub Actions history

| Date | Run | Conclusion |
|---|---|---|
| 2026-11-16T13:25Z | 43875648359 (scaffold) | failure — `fmt -check` exit 3 on variables.tf |
| 2026-11-16T13:26Z | 43875805580 (scaffold) | failure — `fmt -check` exit 3 on variables.tf |
| 2026-11-16T16:05Z | 43903676726 (fmt fix) | failure — scaffold exact-string test broke on realigned fmt |
| 2026-11-16T16:06Z | 43903816788 (regex test fix) | **success — 3 tests + fmt + init + validate green** |
| 2026-11-16T16:22Z | 43906777526 (M1 implementation, commit 9e7e295) | **success — 74 tests + fmt + init + validate green on ubuntu runner / terraform 1.10.5** |
