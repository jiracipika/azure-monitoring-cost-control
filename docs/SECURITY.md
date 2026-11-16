# Threat model

Threats: supply-chain compromise, privileged CI job, state exposure, accidental public endpoints, lateral workload movement, log data leaks and incomplete teardown.

Mitigations: minimum GitHub permissions, reviewable changes, state protection, scoped OIDC, no public admin access, cloud policy guardrails and negative tests.

## Implemented controls (offline-verified)

- **Workspace key auth disabled** (`local_authentication_enabled = false`): no long-lived primary/secondary keys to leak; Entra ID only.
- **Public query endpoint closed** (`internet_query_enabled = false`). Public ingestion remains on BY DESIGN (no private link in this scaffold) — documented tradeoff, revisit before production with a private data collection endpoint.
- **Telemetry never lands in storage**: diagnostic settings and the DCR target Log Analytics only; a negative test forbids any `storage_account_id` destination and any storage-account resource (public-container diagnostic leak path eliminated, not just configured-away).
- **No secrets at rest**: placeholder GUIDs only (scanner-enforced), reserved `example.invalid` alert emails, provider lock file pins azurerm 4.81.0, CI has read-only `contents: read`, actions pinned to version tags, no `pull_request_target`, no apply/destroy/login steps anywhere.
- **No credential-shaped strings** committed (in-repo scanner S1).
- **Cost as a safety property**: daily ingestion quota caps runaway volume even if an attacker or bug floods telemetry; budget ladder pages a human.

## Residual risks (honest)

- Alert/budget emails identify an on-call address once real values replace placeholders — treat tfvars with real emails as sensitive; do not commit them (gitignore keeps only `environments/*.tfvars`).
- Budgets notify, they do not enforce: a compromised workload can still spend up to the quota ceiling before humans react.
- No CMK (customer-managed key) on the workspace yet; platform-managed keys only.
- Service Health `scopes` uses a placeholder subscription id; deploying with it unchanged would create a useless alert — the tfvars flow sets the real id.

Do not configure cloud admin roles or enable paid production resources automatically.
