from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from support import RepositoryTest, call_main
import install
from common import snapshot


class InstalledFlowTests(RepositoryTest):
    def test_installed_tools_complete_a_task_with_spaces_in_paths(self):
        target = self.root / ".agents/skills"
        code, _ = call_main(install.main, ["install", "--target", str(target)])
        self.assertEqual(code, 0)
        tool = target / "evolve/scripts/evolve.py"

        def run(*arguments):
            result = subprocess.run([sys.executable, str(tool), *arguments], cwd=self.root,
                                    capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            return json.loads(result.stdout)

        run("init", "--goal", "Exercise installed resources")
        run("add", "--title", "Verify actual module behaviour", "--evidence", "fixture app.py contract",
            "--category", "correctness", "--criterion", "regression", "--file", "app.py")
        run("start", "--task", "E001")
        check = run("run", "--task", "E001", "--criterion", "regression", "--",
                    sys.executable, "-c", "from app import value; assert value() == 1")
        self.assertEqual(check["status"], "pass")
        self.assertTrue(run("gate", "--task", "E001")["ready"])
        self.assertEqual(run("finish", "--task", "E001", "--summary", "Real contract passed")["status"], "complete")
        self.assertIsNone(run("next")["next"])

    def test_snapshot_records_executable_bit_changes(self):
        if sys.platform == "win32":
            self.skipTest("POSIX executable mode is not a Windows file contract")
        path = self.root / "app.py"
        before = snapshot(self.root)
        path.chmod(path.stat().st_mode | 0o111)
        self.assertNotEqual(before["fingerprint"], snapshot(self.root)["fingerprint"])

    def test_snapshot_does_not_follow_replaced_directory_symlink(self):
        directory = self.root / "module"
        directory.mkdir()
        (directory / "file.py").write_text("original")
        self.git("add", "module/file.py")
        (directory / "file.py").unlink()
        directory.rmdir()
        outside = self.root.parent / "outside"
        outside.mkdir()
        (outside / "file.py").write_text("private content")
        try:
            directory.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Symlinks unavailable on this host")
        before = snapshot(self.root)
        (outside / "file.py").write_text("changed private content")
        self.assertEqual(before["fingerprint"], snapshot(self.root)["fingerprint"])
