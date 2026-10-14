from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
from unittest.mock import patch

from support import RepositoryTest, call_main
import evolve
import install
from common import EvolveError, snapshot


class ConcurrentEvidenceTests(RepositoryTest):
    def setUp(self):
        super().setUp()
        self.init()
        self.add()
        self.ledger("start", "--task", "E001")

    def slow_check(self, exit_code=0):
        code = "from pathlib import Path; import time; Path('.evolve/started').write_text('ready'); time.sleep(0.5); raise SystemExit(" + str(exit_code) + ")"
        return self.ledger("run", "--task", "E001", "--criterion", "regression", "--", sys.executable, "-c", code)

    def wait_for_command(self):
        deadline = time.monotonic() + 5
        while not (self.root / ".evolve/started").exists():
            if time.monotonic() > deadline:
                self.fail("Test command did not start")
            time.sleep(0.01)

    def test_pending_check_blocks_finish_even_after_an_earlier_pass(self):
        self.passing_check()
        with ThreadPoolExecutor(max_workers=1) as pool:
            running = pool.submit(self.slow_check, 1)
            self.wait_for_command()
            self.assertFalse(self.ledger("gate", "--task", "E001")[0]["ready"])
            with self.assertRaises(EvolveError):
                self.ledger("finish", "--task", "E001", "--summary", "Must not finish")
            self.assertEqual(running.result()[1], 1)
        checks = self.ledger("status")[0]["tasks"][0]["checks"]
        self.assertEqual([c["status"] for c in checks], ["pass", "fail"])
        self.assertFalse(self.ledger("gate", "--task", "E001")[0]["ready"])

    def test_overlapping_same_criterion_is_refused_and_later_failure_wins(self):
        with ThreadPoolExecutor(max_workers=1) as pool:
            running = pool.submit(self.slow_check)
            self.wait_for_command()
            with self.assertRaises(EvolveError):
                self.ledger("run", "--task", "E001", "--criterion", "regression", "--", sys.executable, "-c", "raise SystemExit(1)")
            self.assertEqual(running.result()[1], 0)
        self.ledger("run", "--task", "E001", "--criterion", "regression", "--", sys.executable, "-c", "raise SystemExit(1)")
        self.assertFalse(self.ledger("gate", "--task", "E001")[0]["ready"])

    def test_recovered_attempt_cannot_be_replaced_by_late_pass(self):
        with ThreadPoolExecutor(max_workers=1) as pool:
            running = pool.submit(self.slow_check)
            self.wait_for_command()
            self.ledger("recover-check", "--task", "E001", "--criterion", "regression", "--reason", "Exercise defensive recovery behaviour")
            with self.assertRaises(EvolveError):
                running.result()
        check = self.ledger("status")[0]["tasks"][0]["checks"][-1]
        self.assertEqual(check["status"], "interrupted")
        self.assertFalse(self.ledger("gate", "--task", "E001")[0]["ready"])

    def test_malformed_task_is_reported_without_overwriting_state(self):
        path = self.root / ".evolve/state.json"
        state = json.loads(path.read_text())
        state["tasks"] = [{}]
        original = json.dumps(state)
        path.write_text(original)
        code, result = call_main(evolve.main, ["--project", str(self.root), "next"])
        self.assertEqual(code, 2)
        self.assertIn("recover", result["error"])
        self.assertEqual(path.read_text(), original)

    def test_malformed_check_and_cyclic_dependencies_are_rejected(self):
        path = self.root / ".evolve/state.json"
        state = json.loads(path.read_text())
        state["tasks"][0]["checks"] = [{}]
        path.write_text(json.dumps(state))
        self.assertEqual(call_main(evolve.main, ["--project", str(self.root), "gate", "--task", "E001"])[0], 2)
        state["tasks"][0]["checks"] = []
        state["tasks"][0]["depends_on"] = ["E001"]
        path.write_text(json.dumps(state))
        self.assertEqual(call_main(evolve.main, ["--project", str(self.root), "next"])[0], 2)


class ConcurrentInstallerTests(RepositoryTest):
    def test_simultaneous_installs_retain_both_specialist_ownerships(self):
        target = self.root / "agent skills"
        first_in_preflight = threading.Event()
        release_first = threading.Event()
        original = install.source_files
        count = 0
        lock = threading.Lock()

        def controlled_source(name):
            nonlocal count
            with lock:
                count += 1
                first = count == 1
            if first:
                first_in_preflight.set()
                release_first.wait(timeout=5)
            return original(name)

        def install_skill(name):
            return install.operate(argparse.Namespace(action="install", target=str(target), project=None,
                                   host="codex", scope="project", skill=[name], dry_run=False))

        with patch.object(install, "source_files", controlled_source), ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(install_skill, "evolve-audit")
            self.assertTrue(first_in_preflight.wait(timeout=5))
            second = pool.submit(install_skill, "evolve-build")
            release_first.set()
            first.result()
            second.result()
        manifest = json.loads((target / install.MANIFEST).read_text())
        self.assertEqual(set(manifest["skills"]), {"evolve", "evolve-audit", "evolve-build"})
        self.assertEqual(call_main(install.main, ["install", "--target", str(target)])[0], 0)


class SubmoduleTests(RepositoryTest):
    def setUp(self):
        super().setUp()
        self.library = self.root.parent / "library"
        self.library.mkdir()
        subprocess.run(["git", "-C", str(self.library), "init", "-q"], check=True)
        (self.library / "lib.py").write_text("version = 1\n")
        subprocess.run(["git", "-C", str(self.library), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.library), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture"], check=True)
        self.git("-c", "protocol.file.allow=always", "submodule", "add", "--quiet", str(self.library), "library module")
        self.module = self.root / "library module"

    def test_submodule_dirty_source_changes_invalidate_fingerprint(self):
        before = snapshot(self.root)
        (self.module / "lib.py").write_text("version = 2\n")
        self.assertNotEqual(before["fingerprint"], snapshot(self.root)["fingerprint"])

    def test_submodule_commit_changes_invalidate_fingerprint(self):
        before = snapshot(self.root)
        subprocess.run(["git", "-C", str(self.module), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-qm", "changed commit"], check=True)
        self.assertNotEqual(before["fingerprint"], snapshot(self.root)["fingerprint"])

    def test_uninitialized_submodule_is_distinguished_from_initialized(self):
        before = snapshot(self.root)
        self.git("submodule", "deinit", "-f", "--", "library module")
        self.assertNotEqual(before["fingerprint"], snapshot(self.root)["fingerprint"])
