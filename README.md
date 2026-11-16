# 10 — Monitoring & Cost Control

**Azure Cloud Engineering Portfolio** · [GitHub: jiracipika](https://github.com/jiracipika) · **PUBLIC repository** · **Offline implementation / Azure NOT DEPLOYED**

## Goal
Detect failures and control Azure spend with measured telemetry.

## Planned Azure architecture
Azure Monitor, Log Analytics, KQL, alerts, Workbooks and budgets.

## GLM / ZCode — start here

1. Read [AGENTS.md](AGENTS.md), [GLM tasks](docs/GLM_TASKS.md), [architecture](docs/ARCHITECTURE.md), [security](docs/SECURITY.md), and [validation](docs/VALIDATION.md).
2. Implement the next offline milestone in **docs/GLM_TASKS.md** with runnable code and negative tests, not just a plan.
3. Verify Terraform syntax and security, run unit tests, record actual results, and keep diagrams/documentation current.
4. **Do not apply Terraform or deploy any billable Azure resources or alter cloud IAM without my explicit approval.**
5. Report changed files, actual tests and blockers in your ZCode session and commits.

## Offline starting commands

```sh
python3 -m unittest discover -s tests -v
terraform -chdir=infra/terraform fmt -check -recursive
terraform -chdir=infra/terraform init -backend=false -input=false
terraform -chdir=infra/terraform validate
```

## Implemented offline (2026-11-16, gated behind deploy_enabled=false)

Seven modules under `infra/terraform/modules/` (see [architecture](docs/ARCHITECTURE.md) for the full map):

- `observability` — central Log Analytics workspace with the cost brakes built in (PerGB2018, 30-day retention default, daily ingestion quota, no workspace-local keys, public query endpoint closed)
- `data_collection` — data collection rule: CPU/memory counters (>=60s sampling) + error-level syslog; Log Analytics destination only
- `diagnostics` — diagnostic settings aggregation into the workspace (never storage; test-enforced)
- `action_groups` — single email action group with common alert schema
- `alert_rules` — KQL alerts (sustained CPU sev 2, syslog error burst sev 1, auto-mitigating) + subscription-scoped Service Health alert
- `budget` — escalating Actual 50%/80% + Forecasted 100% notifications to emails and the action group
- `workbook` — error triage, ingestion-by-type and untagged-resources (tag governance) reporting

Offline determinism: `tests/monitor_simulator.py` parses the real HCL and
replays spend trajectories against the budget ladder and metric series
against the alert thresholds (fire/resolve with hysteresis) —
74 tests total, see [validation](docs/VALIDATION.md) for real outputs.

## Source contents

- `AGENTS.md`: enforceable GLM implementation contract
- `docs/GLM_TASKS.md`: project-specific milestones
- `docs/ARCHITECTURE.md`: implemented topology and trust boundaries
- `docs/SECURITY.md` / `docs/COSTS.md`: guardrails and financial control
- `docs/VALIDATION.md`: log real evidence only
- `docs/TEARDOWN.md`: future approved cleanup plan
- `diagrams/architecture.mmd`: Mermaid model matching the modules
- `infra/terraform/`: seven gated modules + offline provider root
- `examples/`: KQL investigation pack (error triage, cost control, tag governance)
- `.github/workflows/validate.yml`: offline validation, no deploy step
- `tests/`: scaffold safety, static HCL invariants, simulator scenarios, security scanner

## Status and safety

Offline implementation complete for milestone M1; **nothing is deployed** and the deploy gate stays closed. **Repository visibility must remain PRIVATE.** No credentials, secrets, real customer data, Terraform state or internal account identifiers may be committed.
