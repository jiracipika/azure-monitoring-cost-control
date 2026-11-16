"""In-repo static security scanner (deterministic, offline, no network).

The GLM backlog asks for static security scanning in CI. Rather than
pulling a hosted scanner (network-dependent, uncontrolled rule drift),
this suite enforces a fixed policy set over every tracked file:

  S1  no credential-shaped material (keys, connection strings)
  S2  workflows: pinned action tags, read-only permissions, no
      pull_request_target, no apply/destroy/login steps
  S3  no real Azure GUIDs (only the all-zero placeholders)
  S4  no committed state, plans, or stray .tfvars outside environments/
  S5  .mimosa/ tool state never tracked
"""

from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


def tracked_files() -> list:
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    return [ROOT / p for p in out if (ROOT / p).is_file()]


def tracked_text_files() -> list:
    files = []
    for path in tracked_files():
        try:
            files.append((path, path.read_text(errors="replace")))
        except OSError:
            continue
    return files


class CredentialScan(unittest.TestCase):
    """S1 - secret-shaped material must never enter the repo."""

    PATTERNS = [
        (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key material"),
        (r"(?i)AccountKey=[A-Za-z0-9+/=]{40,}", "storage account key"),
        (r"(?i)(password|secret|token)\s*[:=]\s*['\"][^'\"<>{}]{8,}['\"]", "hardcoded credential"),
        (r"SharedAccessSignature sr=", "SAS token"),
        (r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}", "JWT"),
    ]

    def test_no_secret_shaped_strings(self):
        offenders = []
        for path, text in tracked_text_files():
            # Skip the scanner's own source (it contains the patterns it
            # enforces) — scanning the scanner is a false positive.
            if "tests" in path.relative_to(ROOT).parts:
                continue
            for pattern, label in self.PATTERNS:
                for m in re.finditer(pattern, text):
                    offenders.append(f"{label}: {path.relative_to(ROOT)}:{text[:m.start()].count(chr(10)) + 1}")
        self.assertEqual(offenders, [], "secret-shaped strings found:\n" + "\n".join(offenders))


class WorkflowScan(unittest.TestCase):
    """S2 - CI stays read-only and reproducible."""

    def test_actions_pinned_to_version_tags(self):
        wf = (ROOT / ".github/workflows/validate.yml").read_text()
        uses = re.findall(r"uses:\s*(\S+)", wf)
        self.assertTrue(uses)
        for ref in uses:
            self.assertRegex(ref, r"@[vV]\d+(\.\d+)*$", f"{ref} must be pinned to a version tag")

    def test_no_pull_request_target(self):
        self.assertNotIn("pull_request_target", (ROOT / ".github/workflows/validate.yml").read_text())

    def test_no_mutating_steps_anywhere(self):
        for path, text in tracked_text_files():
            if path.suffix == ".md":
                # docs may *describe* teardown; only scripts/workflows act
                continue
            self.assertNotRegex(text, r"(?m)^\s*terraform\s+(apply|destroy)", path.name)
            self.assertNotRegex(text, r"(?m)^\s*az\s+(login|account|network\s+vnet\s+create)", path.name)

    def test_workflow_declares_read_only_permissions(self):
        wf = (ROOT / ".github/workflows/validate.yml").read_text()
        self.assertIn("permissions:", wf)
        self.assertRegex(wf, r"contents:\s*read")
        self.assertNotRegex(wf, r"(id-token|packages|deployments):\s*write")


class PlaceholderGuidScan(unittest.TestCase):
    """S3 - no real subscription/tenant/object GUIDs at rest."""

    GUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
    PLACEHOLDER = "00000000-0000-0000-0000-000000000000"

    def test_only_placeholder_guids_committed(self):
        offenders = []
        for path, text in tracked_text_files():
            for m in self.GUID.finditer(text):
                if m.group(0) != self.PLACEHOLDER:
                    offenders.append(f"{path.relative_to(ROOT)}: {m.group(0)}")
        self.assertEqual(offenders, [], "non-placeholder GUIDs committed:\n" + "\n".join(offenders))


class RepoHygieneScan(unittest.TestCase):
    """S4/S5 - state, plans, ad-hoc tfvars and tool scratch never tracked."""

    def test_no_state_plans_or_loose_tfvars(self):
        bad = [str(p.relative_to(ROOT)) for p in tracked_files()
               if p.suffix in {".tfstate", ".tfplan"}
               or (p.name.endswith(".tfvars") and "environments" not in p.parts)]
        self.assertEqual(bad, [], f"forbidden tracked files: {bad}")

    def test_environments_tfvars_allowed_and_gated(self):
        files = tracked_files()
        env_tfvars = [p for p in files if p.parent.name == "environments" and p.suffix == ".tfvars"]
        self.assertTrue(env_tfvars, "environments/dev.tfvars must stay tracked")
        for p in env_tfvars:
            self.assertRegex(p.read_text(), r"deploy_enabled\s*=\s*false")

    def test_mimosa_never_tracked(self):
        self.assertFalse(any(".mimosa" in p.parts for p in tracked_files()),
                          ".mimosa/ tool state must be gitignored")

    def test_gitignore_has_env_exception_and_mimosa(self):
        gi = (ROOT / ".gitignore").read_text()
        self.assertRegex(gi, r"!.*environments/\*\.tfvars")
        self.assertIn(".mimosa/", gi)

    def test_provider_lockfile_committed_for_dependency_review(self):
        lock = ROOT / "infra/terraform/.terraform.lock.hcl"
        self.assertTrue(lock.is_file(), "committed .terraform.lock.hcl pins provider deps")
        self.assertIn("hashicorp/azurerm", lock.read_text())


if __name__ == "__main__":
    unittest.main()
