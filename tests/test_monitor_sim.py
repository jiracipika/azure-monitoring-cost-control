"""Deterministic offline demo — the GLM backlog's "demonstrate error
investigations, appropriate alerts and controlled dev-environment spend".

All scenarios replay through monitor_simulator.py, which parses the REAL
HCL (budget ladder from root variables, alert thresholds/frequency/window
from modules/alert_rules) — nothing is mocked.
"""

import unittest

import monitor_simulator as ms


def rule(label):
    return {r["label"]: r for r in ms.load_query_rules()}[label]


class BudgetSimulation(unittest.TestCase):
    """Spend trajectories vs the committed threshold ladder."""

    @classmethod
    def setUpClass(cls):
        cls.config = ms.load_budget_config()
        # committed defaults: amount 20 CAD, actuals [50, 80], forecast 100
        assert cls.config["amount"] == 20
        assert cls.config["actual_thresholds"] == [50, 80]
        assert cls.config["forecast_threshold"] == 100

    def simulate(self, daily_spend, **kw):
        return ms.simulate_budget(
            daily_spend,
            self.config["amount"],
            self.config["actual_thresholds"],
            self.config["forecast_threshold"],
            **kw,
        )

    def test_steady_under_budget_fires_nothing(self):
        # 0.3 CAD/day * 30 = 9 CAD = 45% of the 20 CAD budget
        timeline, fired = self.simulate([0.3] * 30)
        self.assertEqual(fired, set())
        self.assertEqual(timeline[-1]["actual_pct"], 45.0)

    def test_sustained_overspend_escalates_actuals_in_order(self):
        # 1.0 CAD/day run-rate crosses 50% on day 11 (cumulative 11 = 55%)
        # and 80% on day 17 (cumulative 17 = 85%)
        timeline, fired = self.simulate([1.0] * 30)
        first_50 = next(d["day"] for d in timeline if ("Actual", 50) in d["fired"])
        first_80 = next(d["day"] for d in timeline if ("Actual", 80) in d["fired"])
        self.assertEqual(first_50, 11)
        self.assertEqual(first_80, 17)
        self.assertIn(("Actual", 50), fired)
        self.assertIn(("Actual", 80), fired)
        self.assertIn(("Forecasted", 100), fired)

    def test_overspend_run_rate_fires_forecast_before_actuals(self):
        # 1.0 CAD on day 1 projects to 30 CAD (150%) — the forecast warning
        # fires on day 1, long before any actual threshold.
        timeline, fired = self.simulate([1.0] * 30)
        self.assertIn(("Forecasted", 100), timeline[0]["fired"])
        self.assertEqual(timeline[0]["fired"], frozenset({("Forecasted", 100)}))

    def test_early_burst_fires_forecast_then_recovers(self):
        # 12 CAD on day 1 (60% actual, projects to 1800%) then zero spend:
        # forecast clears once cumulative/day drops below 100/30 per day —
        # day 18 is the first day the forecast stops firing.
        timeline, fired = self.simulate([12.0] + [0.0] * 29)
        self.assertIn(("Actual", 50), fired)
        self.assertNotIn(("Actual", 80), fired, "60% peak never reaches the 80% rung")
        forecast_days = [d["day"] for d in timeline if ("Forecasted", 100) in d["fired"]]
        self.assertEqual(forecast_days, list(range(1, 18)))

    def test_exactly_at_threshold_never_fires_strict_operator(self):
        # 10 CAD cumulative = exactly 50% -> GreaterThan is strict
        timeline, fired = self.simulate([10.0] + [0.0] * 29)
        self.assertNotIn(("Actual", 50), fired)

    def test_escalation_order_is_monotonic_per_day(self):
        # an 80% Actual fire day always also carries the 50% Actual fire
        timeline, _ = self.simulate([1.5] * 30)
        for day in timeline:
            if ("Actual", 80) in day["fired"]:
                self.assertIn(("Actual", 50), day["fired"])


class AlertStateMachine(unittest.TestCase):
    """Error-investigation alerts: fire/resolves semantics with hysteresis."""

    @classmethod
    def setUpClass(cls):
        cls.cpu = rule("high_cpu")          # threshold 85%, freq 5, window 15
        cls.syslog = rule("syslog_error_burst")  # threshold 50, freq 5, window 15

    def test_parsed_rules_match_committed_defaults(self):
        self.assertEqual(self.cpu["threshold"], 85)
        self.assertEqual(self.cpu["frequency_min"], 5)
        self.assertEqual(self.cpu["window_min"], 15)
        self.assertEqual(self.syslog["threshold"], 50)
        self.assertEqual(self.syslog["severity"], 1)
        self.assertEqual(self.cpu["severity"], 2)
        self.assertTrue(self.cpu["auto_mitigation"])
        self.assertTrue(self.syslog["auto_mitigation"])

    def test_quiet_series_never_fires(self):
        self.assertEqual(ms.replay_rule(self.cpu, [10.0] * 20),
                         ["OK"] * 20)

    def test_sustained_saturation_fires_after_full_window(self):
        # window/frequency = 3 consecutive breaches needed
        states = ms.replay_rule(self.cpu, [90.0, 90.0, 90.0, 90.0])
        self.assertEqual(states[:2], ["OK", "OK"])
        self.assertEqual(states[2:], ["FIRED"] * 2)

    def test_flapping_series_lacks_sustained_breach(self):
        # 2 up, 1 down repeating: streak never reaches 3 -> no page at 3am
        flapping = [90.0, 90.0, 20.0] * 6
        self.assertEqual(set(ms.replay_rule(self.cpu, flapping)), {"OK"})

    def test_auto_mitigation_resolves_after_clear_window(self):
        states = ms.replay_rule(self.cpu, [90.0] * 3 + [20.0] * 4)
        self.assertEqual(states[2], "FIRED")
        # steps 4..6 are the clearing window; step 6 is OK again
        self.assertEqual(states[5], "OK")
        self.assertEqual(states[6], "OK")

    def test_recovery_requires_full_window_hysteresis(self):
        states = ms.replay_rule(self.cpu, [90.0] * 3 + [20.0, 20.0, 90.0, 90.0, 90.0, 90.0])
        # only 2 clear steps then re-saturation: FIRED persists, never OK
        self.assertNotIn("OK", states[3:], "partial clear window must not resolve")

    def test_value_exactly_at_threshold_is_not_a_breach(self):
        states = ms.replay_rule(self.cpu, [85.0] * 10)
        self.assertEqual(set(states), {"OK"})

    def test_syslog_burst_threshold_semantics(self):
        states = ms.replay_rule(self.syslog, [49, 49, 49, 50, 51, 51, 51])
        self.assertEqual(set(states[:4]), {"OK"})
        self.assertEqual(states[6], "FIRED")

    def test_without_auto_mitigation_alert_latches(self):
        latch_rule = dict(self.cpu, auto_mitigation=False)
        states = ms.replay_rule(latch_rule, [90.0] * 3 + [10.0] * 10)
        self.assertEqual(states[2], "FIRED")
        self.assertEqual(set(states[3:]), {"FIRED"})


class QueryTableConsistency(unittest.TestCase):
    """Alert queries may only read what the DCR ingests (drift guard)."""

    def test_dcr_tables_are_perf_and_syslog(self):
        self.assertEqual(ms.dcr_tables(), {"Perf", "Syslog"})

    def test_every_alert_query_stays_within_ingested_tables(self):
        for r in ms.load_query_rules():
            self.assertLessEqual(ms.kql_tables(r["query"]), ms.dcr_tables(), r["label"])

    def test_workbook_queries_use_ingested_or_workspace_system_tables(self):
        allowed = ms.dcr_tables() | {"Usage"}
        for query in ms.workbook_queries():
            if "Resources |" in query:  # Azure Resource Graph, not Log Analytics
                continue
            used = ms.kql_tables(query)
            self.assertTrue(used)
            self.assertLessEqual(used, allowed, query[:60])


if __name__ == "__main__":
    unittest.main()
