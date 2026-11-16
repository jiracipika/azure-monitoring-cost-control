# 10 — Monitoring and Cost Control

**Azure Cloud Engineering Portfolio · Project 10 of 10**

**Owner:** jiracipika · **Visibility:** PRIVATE · **Status:** Scaffold, NOT deployed

## Project objective

Detect anomalies with documented KQL, actionable alerts and cost controls.

## Target Azure architecture

Log Analytics, Azure Monitor, Application Insights, Workbooks, budgets and alerts.

## GLM / ZCode start instructions

1. Read `AGENTS.md`, `docs/GLM_TASKS.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md` and `docs/VALIDATION.md` before implementation.
2. Implement and test a safe offline milestone first. Keep diagrams and README aligned with actual implementation.
3. Use modular, version-constrained Terraform and reproducible CI. Validate with `python3 -m unittest discover -s tests -v` and `terraform fmt -check` / `terraform validate` where available.
4. Do not execute billable Azure provisioning, Terraform apply/destroy, production identity changes or paid load tests without separate explicit approval.
5. Record all real checks and outstanding blockers in `docs/VALIDATION.md`. Open a PR for substantial improvements.

## Initial checkpoints

- [ ] Baseline documentation and architecture diagram
- [ ] Terraform offline validated with safe defaults
- [ ] CI and tests passing
- [ ] Detailed security and cost review
- [ ] Human authorization before any live cloud deployment

**This GitHub repository must remain PRIVATE.** No tokens, credentials, private Terraform state, customer data or tenant secrets may be committed.
