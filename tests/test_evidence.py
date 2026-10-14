from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import sys
from unittest.mock import patch

from support import RepositoryTest, call_main
import evolve
from common import EvolveError, StateLock, redact, run_command, snapshot


class EvidenceTests(RepositoryTest):
    def setUp(self):
        super().setUp()
        self.init()

    def test_complete_requires_all_registered_criteria(self):
        self.add(criteria=("regression", "integration"))
        self.ledger("start", "--task", "E001")
        self.passing_check()
        result, code = self.ledger("gate", "--task", "E001")
        self.assertEqual(code, 1)
        self.assertIn("integration: no evidence", result["reasons"])
        with self.assertRaises(EvolveError):
            self.ledger("finish", "--task", "E001", "--summary", "not done")
        self.passing_check(criterion="integration")
        task, code = self.ledger("finish", "--task", "E001", "--summary", "Working end to end")
        self.assertEqual(task["status"], "complete")
        self.assertIsNone(task["delivery"])

    def test_source_edit_invalidates_passing_evidence(self):
        self.add()
        self.ledger("start", "--task", "E001")
        self.passing_check()
        (self.root / "app.py").write_text("def value():\n    return 2\n")
        result, code = self.ledger("gate", "--task", "E001")
        self.assertEqual(code, 1)
        self.assertTrue(any("stale" in r for r in result["reasons"]))

    def test_new_untracked_source_invalidates_evidence(self):
        self.add()
        self.ledger("start", "--task", "E001")
        self.passing_check()
        (self.root / "new.py").write_text("raise RuntimeError()\n")
        self.assertFalse(self.ledger("gate", "--task", "E001")[0]["ready"])

    def test_latest_failure_supersedes_pass(self):
        self.add()
        self.ledger("start", "--task", "E001")
        self.passing_check()
        result, code = self.ledger("run", "--task", "E001", "--criterion", "regression", "--", sys.executable, "-c", "raise SystemExit(3)")
        self.assertEqual(code, 1)
        self.assertEqual(result["exit_code"], 3)
        self.assertFalse(self.ledger("gate", "--task", "E001")[0]["ready"])

    def test_failed_command_start_invalidates_previous_pass(self):
        self.add()
        self.ledger("start", "--task", "E001")
        self.passing_check()
        result, code = self.ledger("run", "--task", "E001", "--criterion", "regression", "--", "evolve-intentionally-missing-command-78219")
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "error")
        self.assertFalse(self.ledger("gate", "--task", "E001")[0]["ready"])

    def test_mutating_check_is_not_fresh_verification(self):
        self.add()
        self.ledger("start", "--task", "E001")
        self.ledger("run", "--task", "E001", "--criterion", "regression", "--", sys.executable, "-c", "from pathlib import Path; Path('app.py').write_text('x = 3\\n')")
        self.assertFalse(self.ledger("gate", "--task", "E001")[0]["ready"])
        self.passing_check()
        self.assertTrue(self.ledger("gate", "--task", "E001")[0]["ready"])

    def test_snapshot_survives_commit_without_source_changes(self):
        before = snapshot(self.root)
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-qm", "checkpoint")
        after = snapshot(self.root)
        self.assertNotEqual(before["revision"], after["revision"])
        self.assertEqual(before["fingerprint"], after["fingerprint"])

    def test_state_changes_do_not_invalidate_source_snapshot(self):
        before = snapshot(self.root)
        self.add()
        self.assertEqual(before["fingerprint"], snapshot(self.root)["fingerprint"])

    def test_observation_artifact_must_exist_and_remain_unchanged(self):
        self.add(criteria=("review",))
        self.ledger("start", "--task", "E001")
        result, code = self.ledger("observe", "--task", "E001", "--criterion", "review", "--artifact", ".evolve/missing.txt", "--detail", "inspected", "--outcome", "pass")
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "error")
        artifact = self.root / ".evolve/review.txt"
        artifact.write_text("Reviewer checked actual acceptance criteria.")
        self.ledger("observe", "--task", "E001", "--criterion", "review", "--artifact", ".evolve/review.txt", "--detail", "Validated the assertions against the requested result.", "--outcome", "pass")
        self.assertTrue(self.ledger("gate", "--task", "E001")[0]["ready"])
        artifact.write_text("changed")
        self.assertFalse(self.ledger("gate", "--task", "E001")[0]["ready"])

    def test_reconcile_reports_completed_stale_tasks_without_rewriting_history(self):
        self.add()
        self.ledger("start", "--task", "E001")
        self.passing_check()
        self.ledger("finish", "--task", "E001", "--summary", "Fixed")
        (self.root / "app.py").write_text("changed\n")
        report, _ = self.ledger("reconcile")
        self.assertEqual(report["completed_with_stale_evidence"], ["E001"])
        self.assertEqual(self.ledger("status")[0]["tasks"][0]["status"], "complete")

    def test_dependency_order_and_overlapping_ownership(self):
        self.add()
        self.add(title="Dependent", dependencies=("E001",))
        with self.assertRaises(EvolveError):
            self.ledger("start", "--task", "E002")
        self.ledger("start", "--task", "E001")
        self.add(title="Overlapping task")
        with self.assertRaises(EvolveError):
            self.ledger("start", "--task", "E003")

    def test_priority_selects_eligible_work_and_skips_deferred(self):
        self.add()
        self.add(title="Blocked", dependencies=("E001",), files=("other.py",))
        self.ledger("move", "--task", "E001", "--status", "deferred", "--reason", "outside this run")
        self.assertIsNone(self.ledger("next")[0]["next"])

    def test_init_is_idempotent_and_does_not_grant_new_permission(self):
        result, _ = self.ledger("init", "--goal", "Different goal", "--delivery", "merge")
        self.assertFalse(result["created"])
        self.assertEqual(result["state"]["delivery_mode"], "local")

    def test_concurrent_adds_do_not_lose_tasks(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda title: self.add(title=title), ["First", "Second"]))
        self.assertEqual({r["id"] for r in results}, {"E001", "E002"})
        self.assertEqual(len(self.ledger("status")[0]["tasks"]), 2)

    def test_invalid_scope_traversal_is_rejected(self):
        for value in ("../outside.py", "C:\\outside.py", "/tmp/outside", "a/../b"):
            with self.subTest(value=value), self.assertRaises(EvolveError):
                self.add(files=(value,))

    def test_symlink_in_state_is_refused(self):
        link = self.root / ".evolve/outside"
        try:
            link.symlink_to(self.root, target_is_directory=True)
        except OSError:
            self.skipTest("Symlinks unavailable on this host")
        self.add(criteria=("review",))
        self.ledger("start", "--task", "E001")
        result, code = self.ledger("observe", "--task", "E001", "--criterion", "review", "--artifact", ".evolve/outside/app.py", "--detail", "checked", "--outcome", "pass")
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "error")

    def test_delivery_record_does_not_execute_git(self):
        self.add()
        with self.assertRaises(EvolveError):
            self.ledger("delivery", "--task", "E001", "--status", "merged", "--ref", "https://example.invalid/pr/1")
        self.ledger("start", "--task", "E001")
        self.passing_check()
        self.ledger("finish", "--task", "E001", "--summary", "Fixed")
        before = self.git("rev-parse", "HEAD")
        task, _ = self.ledger("delivery", "--task", "E001", "--status", "local", "--ref", "working tree")
        self.assertEqual(before, self.git("rev-parse", "HEAD"))
        self.assertEqual(task["delivery"]["status"], "local")

    def test_cli_missing_state_is_an_actionable_error(self):
        (self.root / ".evolve/state.json").unlink()
        code, result = call_main(evolve.main, ["--project", str(self.root), "status"])
        self.assertEqual(code, 2)
        self.assertIn("init", result["error"])


class RunnerTests(RepositoryTest):
    def test_timeout_cannot_be_reported_as_pass(self):
        result = run_command(self.root, [sys.executable, "-c", "import time; time.sleep(3)"], 0.1)
        self.assertEqual(result["status"], "timeout")
        self.assertLess(result["seconds"], 2)

    def test_output_capture_is_bounded(self):
        result = run_command(self.root, [sys.executable, "-c", "print('x' * 700000)"], 10)
        self.assertTrue(result["output_truncated"])
        self.assertLessEqual(len(result["output"]), 512 * 1024)

    def test_secret_patterns_and_environment_values_are_redacted(self):
        secret = "private-environment-value"
        with patch.dict(os.environ, {"SERVICE_TOKEN": secret}):
            result = run_command(self.root, [sys.executable, "-c", "import os; print(os.environ['SERVICE_TOKEN']); print('token=hiddenvalue')"], 10)
        self.assertNotIn(secret, result["output"])
        self.assertNotIn("hiddenvalue", result["output"])

    def test_argv_is_not_interpreted_as_shell_code(self):
        literal = "$(touch accidental-file)"
        result = run_command(self.root, [sys.executable, "-c", "import sys; print(sys.argv[1])", literal], 10)
        self.assertIn(literal, result["output"])
        self.assertFalse((self.root / "accidental-file").exists())
