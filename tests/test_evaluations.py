from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/evaluations/make_fixture.py"
COMPARE = ROOT / "tests/evaluations/compare_runs.py"


class EvaluationHarnessTests(unittest.TestCase):
    def test_scenarios_create_clean_repos_with_passing_baseline_smoke_tests(self):
        with tempfile.TemporaryDirectory() as parent:
            for scenario in ("bug", "ui", "refactor", "shipping"):
                with self.subTest(scenario=scenario):
                    # macOS may expose /var as a symlink to /private/var;
                    # exercise the fixture's real resolved temp path.
                    target = Path(parent).resolve() / f"{scenario} project"
                    generated = subprocess.run(
                        [sys.executable, str(FIXTURE), "--scenario", scenario, "--output", str(target)],
                        capture_output=True, text=True, encoding="utf-8")
                    self.assertEqual(generated.returncode, 0, generated.stderr)
                    self.assertTrue((target / ".git").is_dir())
                    self.assertTrue((target / "README.md").is_file())
                    run = subprocess.run(
                        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                        cwd=target, capture_output=True, text=True, encoding="utf-8")
                    self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                    remote = subprocess.run(["git", "-C", str(target), "remote"],
                                            capture_output=True, text=True)
                    self.assertEqual(remote.stdout.strip(), "")

    def test_record_comparison_requires_same_workload_and_real_evidence(self):
        with tempfile.TemporaryDirectory() as parent:
            before, after = (Path(parent) / name for name in ("without.json", "with.json"))
            record = {"scenario": "bug", "host": "test", "model": "test-model",
                      "starting_revision": "abc123", "checks": {
                          "regression": {"status": "fail", "evidence": "logs/before.txt"}
                      }, "tokens": {"input": 100, "output": 200}}
            before.write_text(json.dumps(record), encoding="utf-8")
            record["checks"]["regression"] = {"status": "pass", "evidence": "logs/after.txt"}
            record["tokens"] = {"input": 120, "output": 210}
            after.write_text(json.dumps(record), encoding="utf-8")
            args = [sys.executable, str(COMPARE), "--without", str(before), "--with-evolve", str(after)]
            outcome = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(outcome.returncode, 0, outcome.stderr)
            result = json.loads(outcome.stdout)
            self.assertEqual(result["token_delta"], {"input": 20, "output": 10})
            self.assertEqual(result["checks"]["regression"]["with_evolve"], "pass")
            record["model"] = "different-model"
            after.write_text(json.dumps(record), encoding="utf-8")
            self.assertEqual(subprocess.run(args, capture_output=True).returncode, 2)
            record["model"] = "test-model"
            record["checks"]["regression"].pop("evidence")
            after.write_text(json.dumps(record), encoding="utf-8")
            self.assertEqual(subprocess.run(args, capture_output=True).returncode, 2)
