from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CHECK = Path(__file__).resolve().parents[1] / "scripts/check.py"


class OfflineCheckRunnerTests(unittest.TestCase):
    def test_success_failure_and_empty_discovery_with_path_spaces(self):
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace).resolve() / "checkout with spaces"
            (root / "scripts").mkdir(parents=True)
            (root / "tests").mkdir()
            (root / "scripts/validate.py").write_text("print('valid package')\n", encoding="utf-8")
            test = root / "tests/test_sample.py"
            test.write_text(
                "import unittest\nclass Good(unittest.TestCase):\n"
                " def test_ok(self): self.assertEqual(2, 1+1)\n", encoding="utf-8"
            )
            argv = [sys.executable, str(CHECK), "--root", str(root)]
            def run():
                return subprocess.run(argv, capture_output=True, text=True, encoding="utf-8")

            good = run()
            self.assertEqual(good.returncode, 0, good.stderr + good.stdout)
            self.assertIn("Package validation: PASS", good.stdout)
            self.assertIn("Local tests: PASS", good.stdout)

            test.write_text(
                "import unittest\nclass Bad(unittest.TestCase):\n"
                " def test_fails(self): self.fail('deliberate failure')\n", encoding="utf-8"
            )
            bad = run()
            self.assertEqual(bad.returncode, 1)
            self.assertIn("Local tests: FAIL", bad.stdout)

            test.unlink()
            empty = run()
            self.assertEqual(empty.returncode, 1)
            self.assertIn("No executed test count found", empty.stderr)

            (root / "scripts/validate.py").write_text("raise SystemExit(9)\n", encoding="utf-8")
            invalid = run()
            self.assertEqual(invalid.returncode, 1)
            self.assertIn("Package validation: FAIL", invalid.stdout)
            self.assertIn("Local tests: FAIL", invalid.stdout)
