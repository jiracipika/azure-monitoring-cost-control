"""Scaffold safety regressions.

Regex assertions only: exact-string matches break whenever `terraform fmt`
realigns attribute equals signs (this exact failure turned CI red on run
43903676726 after the canonical fmt fix).
"""

import re
import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]


class SafetyTests(unittest.TestCase):
    def test_docs(self):
        self.assertTrue((R / "AGENTS.md").is_file())
        self.assertTrue((R / "docs/GLM_TASKS.md").is_file())

    def test_cloud_disabled(self):
        variables = (R / "infra/terraform/variables.tf").read_text()
        self.assertRegex(
            variables,
            r'"deploy_enabled"\s*\{[^}]*?default\s*=\s*false',
            "deploy gate must default to false",
        )
        workflow = (R / ".github/workflows/validate.yml").read_text()
        self.assertNotIn("terraform apply", workflow)
        self.assertNotIn("terraform destroy", workflow)

    def test_diagram(self):
        self.assertIn("flowchart", (R / "diagrams/architecture.mmd").read_text())


if __name__ == "__main__":
    unittest.main()
