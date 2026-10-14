from __future__ import annotations

import json
import sys

from support import RepositoryTest, call_main
import bench
import inventory
from common import EvolveError


def record(samples, **overrides):
    return {"name": "load", "unit": "ms", "direction": "lower", "workload": "fixture-1000",
            "environment": {"machine": "same", "runtime": "same", "mode": "release"},
            "samples": samples, **overrides}


class BenchmarkTests(RepositoryTest):
    def test_comparable_medians_and_improvement(self):
        result = bench.compare(record([100, 100, 110]), record([80, 80, 82]))
        self.assertAlmostEqual(result["improvement_percent"], 20)
        self.assertFalse(result["within_observed_variation"])

    def test_higher_is_better_is_supported(self):
        result = bench.compare(record([100, 100, 100], direction="higher"), record([120, 120, 120], direction="higher"))
        self.assertAlmostEqual(result["improvement_percent"], 20)

    def test_changed_workload_or_environment_is_rejected(self):
        for changes in ({"workload": "different"}, {"unit": "seconds"}, {"environment": {"machine": "different", "runtime": "same", "mode": "release"}}):
            with self.subTest(changes=changes), self.assertRaises(EvolveError):
                bench.compare(record([1, 2, 3]), record([1, 2, 3], **changes))

    def test_non_finite_boolean_zero_negative_and_too_few_samples_are_rejected(self):
        for samples in ([1, 2], [0, 1, 2], [-1, 1, 2], [True, 1, 2], [float("nan"), 1, 2], [float("inf"), 1, 2]):
            with self.subTest(samples=samples), self.assertRaises(EvolveError):
                bench.validate(record(samples))

    def test_small_change_with_large_variation_is_flagged(self):
        result = bench.compare(record([70, 100, 130]), record([65, 95, 125]))
        self.assertTrue(result["within_observed_variation"])

    def test_regression_threshold_returns_failure(self):
        before, after = self.root / "before.json", self.root / "after.json"
        before.write_text(json.dumps(record([100, 100, 100])))
        after.write_text(json.dumps(record([120, 120, 120])))
        code, _ = call_main(bench.main, ["compare", str(before), str(after), "--max-regression", "5"])
        self.assertEqual(code, 1)

    def test_collects_real_command_samples_without_overwriting(self):
        arguments = ["run", "--project", str(self.root), "--name", "launch", "--workload", "python-empty",
                     "--runtime", "Python " + sys.version.split()[0], "--machine", "test-runner", "--mode", "test",
                     "--samples", "3", "--warmups", "0", "--output", ".evolve/benchmark.json",
                     "--", sys.executable, "-c", "pass"]
        self.assertEqual(call_main(bench.main, arguments)[0], 0)
        data = json.loads((self.root / ".evolve/benchmark.json").read_text())
        self.assertEqual(len(data["samples"]), 3)
        self.assertTrue(all(value > 0 for value in data["samples"]))
        self.assertEqual(call_main(bench.main, arguments)[0], 2)

    def test_failed_benchmark_does_not_write_passing_record(self):
        code, _ = call_main(bench.main, ["run", "--project", str(self.root), "--name", "launch", "--workload", "fail",
                                      "--runtime", "test", "--machine", "test-runner", "--mode", "test", "--samples", "3", "--output", ".evolve/failure.json",
                                      "--", sys.executable, "-c", "raise SystemExit(1)"])
        self.assertEqual(code, 2)
        self.assertFalse((self.root / ".evolve/failure.json").exists())


class InventoryTests(RepositoryTest):
    def test_inventory_excludes_credentials_and_generated_files_without_execution(self):
        (self.root / "vendor").mkdir()
        (self.root / "vendor/a.py").write_text("raise RuntimeError('do not execute')")
        (self.root / ".env").write_text("secret=never-read")
        self.git("add", "vendor", ".env")
        result = inventory.inventory(self.root)
        self.assertIn("app.py", result["files"])
        self.assertNotIn("vendor/a.py", result["files"])
        self.assertNotIn(".env", result["files"])
        self.assertEqual(len(result["excluded"]), 2)
        self.assertNotIn("never-read", json.dumps(result))

    def test_inventory_limit_records_omissions(self):
        result = inventory.inventory(self.root, limit=1)
        self.assertEqual(len(result["files"]), 1)
        self.assertTrue(any(e["reason"] == "inventory limit" for e in result["excluded"]))

    def test_inventory_output_refuses_traversal_and_overwrite(self):
        code, _ = call_main(inventory.main, ["--project", str(self.root), "--output", "../outside.json"])
        self.assertEqual(code, 2)
        arguments = ["--project", str(self.root), "--output", ".evolve/inventory.json"]
        self.assertEqual(call_main(inventory.main, arguments)[0], 0)
        self.assertEqual(call_main(inventory.main, arguments)[0], 2)
