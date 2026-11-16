"""Offline, deterministic monitoring/cost simulators.

Parses the REAL Terraform sources (no mocks, no network) and replays
scenarios against the declared configuration:

- Budgets: spend trajectories vs the notification thresholds wired in
  modules/budget + root variables, honouring Azure's Actual vs Forecasted
  semantics (operator GreaterThan is STRICT).
- Alert rules: value series vs the parsed threshold / frequency / window of
  each azurerm_monitor_scheduled_query_rules_alert, through a fired/resolved
  state machine that models auto-mitigation hysteresis.

Approximations (documented, deterministic): budgets are evaluated once per
day at month-day granularity with a linear run-rate forecast
(cumulative / elapsed_days * month_days); log-alert firing requires a fully
breached look-back window of window/frequency consecutive evaluations.
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TF = ROOT / "infra" / "terraform"

# Azure Monitor stream name -> Log Analytics table produced by the stream.
STREAM_TABLES = {
    "Microsoft-Perf": "Perf",
    "Microsoft-Syslog": "Syslog",
}


def read(rel: str) -> str:
    return (TF / rel).read_text()


def blocks(src: str, resource_type: str):
    """(label, body) for every `resource "<type>" "<label>" { ... }` using
    brace matching — robust to nested blocks and heredoc KQL."""
    out = []
    for m in re.finditer(rf'resource "{re.escape(resource_type)}" "([\w-]+)" \{{', src):
        depth, i = 1, m.end()
        while depth and i < len(src):
            if src[i] == "{":
                depth += 1
            elif src[i] == "}":
                depth -= 1
            i += 1
        out.append((m.group(1), src[m.end():i - 1]))
    return out


def _attr(body: str, name: str):
    m = re.search(rf'^\s*{name}\s*=\s*(.+?)\s*$', body, re.M)
    return m.group(1).strip() if m else None


def _number(value: str):
    return float(value.rstrip('"'))


def variable_default(variables_src: str, name: str):
    """Default value of `variable "name"` — number, list or bool literal."""
    m = re.search(rf'variable "{re.escape(name)}" \{{', variables_src)
    if not m:
        raise ValueError(f"variable {name} not found")
    depth, i = 1, m.end()
    while depth and i < len(variables_src):
        if variables_src[i] == "{":
            depth += 1
        elif variables_src[i] == "}":
            depth -= 1
        i += 1
    body = variables_src[m.end():i - 1]
    d = re.search(r"default\s*=\s*(.+)", body)
    if not d:
        raise ValueError(f"variable {name} has no default")
    raw = d.group(1).strip()
    if raw.startswith("["):
        return [float(x) if "." in x else int(x) for x in re.findall(r"[\d.]+", raw)]
    if raw in ("true", "false"):
        return raw == "true"
    return float(raw) if "." in raw else int(raw)


# --- Budget ----------------------------------------------------------------------

def load_budget_config() -> dict:
    """Amount + threshold ladder exactly as committed (root defaults are the
    single source of truth; static tests assert the module wiring)."""
    root_vars = read("variables.tf")
    return {
        "amount": variable_default(root_vars, "budget_amount"),
        "actual_thresholds": variable_default(root_vars, "budget_actual_thresholds"),
        "forecast_threshold": variable_default(root_vars, "budget_forecast_threshold"),
    }


def simulate_budget(daily_spend, amount, actual_thresholds, forecast_threshold,
                    month_days=30):
    """Replay daily spend. Returns (timeline, all_fired) where timeline is a
    per-day dict {day, actual_pct, forecast_pct, fired: frozenset} and
    `fired` entries are (type, threshold) tuples crossed with STRICT >."""
    cumulative = 0.0
    timeline, all_fired = [], set()
    for day, spend in enumerate(daily_spend, start=1):
        cumulative += spend
        actual_pct = 100.0 * cumulative / amount
        forecast_pct = actual_pct * month_days / day  # linear run-rate
        fired = set()
        for t in actual_thresholds:
            if actual_pct > t:
                fired.add(("Actual", t))
        if forecast_pct > forecast_threshold:
            fired.add(("Forecasted", forecast_threshold))
        timeline.append({
            "day": day,
            "actual_pct": round(actual_pct, 2),
            "forecast_pct": round(forecast_pct, 2),
            "fired": frozenset(fired),
        })
        all_fired |= fired
    return timeline, all_fired


# --- Scheduled query alert rules ---------------------------------------------------

def load_query_rules() -> list:
    """Both azurerm_monitor_scheduled_query_rules_alert resources with
    threshold variables resolved to their committed defaults."""
    src = read("modules/alert_rules/main.tf")
    module_vars = read("modules/alert_rules/variables.tf")
    rules = []
    for label, body in blocks(src, "azurerm_monitor_scheduled_query_rules_alert"):
        trig = re.search(r"trigger \{", body)
        if not trig:
            raise ValueError(f"{label}: no trigger block — parser drift")
        depth, i = 1, trig.end()
        while depth and i < len(body):
            if body[i] == "{":
                depth += 1
            elif body[i] == "}":
                depth -= 1
            i += 1
        trigger_body = body[trig.end():i - 1]
        threshold_raw = _attr(trigger_body, "threshold")
        if threshold_raw and threshold_raw.startswith("var."):
            threshold = variable_default(module_vars, threshold_raw[4:])
        else:
            threshold = _number(threshold_raw)
        query = re.search(r'<<-KQL\s*\n(.*?)\n\s*KQL', body, re.S)
        if not query:
            raise ValueError(f"{label}: no KQL heredoc — parser drift")
        rules.append({
            "label": label,
            "name": _attr(body, "name").strip('"'),
            "severity": int(_number(_attr(body, "severity"))),
            "frequency_min": int(_number(_attr(body, "frequency"))),
            "window_min": int(_number(_attr(body, "time_window"))),
            "threshold": threshold,
            "operator": _attr(trigger_body, "operator").strip('"'),
            "auto_mitigation": _attr(body, "auto_mitigation_enabled") == "true",
            "query": query.group(1),
        })
    return rules


def replay_rule(rule: dict, series) -> list:
    """Replay one value per frequency interval through the rule state machine.

    OK --(window fully breached)--> FIRED --(full window clear + auto
    mitigation)--> OK.  Without auto_mitigation FIRED latches forever.
    Breach is STRICT (operator GreaterThan): value == threshold never fires.
    """
    n = max(1, rule["window_min"] // rule["frequency_min"])
    state, breach_streak, clear_streak, out = "OK", 0, 0, []
    for v in series:
        breach = v > rule["threshold"] if rule["operator"] == "GreaterThan" else v < rule["threshold"]
        if state == "FIRED" and not rule["auto_mitigation"]:
            out.append(state)  # latched: no auto-resolve
            continue
        if breach:
            breach_streak += 1
            clear_streak = 0
        else:
            clear_streak += 1
            breach_streak = 0
        if state != "FIRED" and breach_streak >= n:
            state, clear_streak = "FIRED", 0
        elif state == "FIRED" and clear_streak >= n:
            state, breach_streak, clear_streak = "OK", 0, 0
        out.append(state)
    return out


# --- KQL / stream consistency ------------------------------------------------------

def dcr_tables() -> set:
    """Log Analytics tables the data collection rule actually produces."""
    src = read("modules/data_collection/main.tf")
    streams = set()
    for _, body in blocks(src, "azurerm_monitor_data_collection_rule"):
        streams |= set(re.findall(r'"(Microsoft-[A-Za-z]+)"', body))
    return {STREAM_TABLES[s] for s in streams if s in STREAM_TABLES}


def kql_tables(query: str) -> set:
    known = ("Perf", "Syslog", "Heartbeat", "Usage", "AzureActivity",
             "AzureDiagnostics", "AzureMetrics", "InsightsMetrics")
    return {t for t in re.findall(r"\b[A-Za-z]+\b", query) if t in known}


def workbook_queries() -> list:
    """Query strings embedded in the workbook JSON builder."""
    src = read("modules/workbook/main.tf")
    return [m.group(1) for m in re.finditer(r'query\s*=\s*"((?:[^"\\]|\\.)*)"', src)]
