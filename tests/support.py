from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PACK_ROOT = Path(__file__).resolve().parents[1]
HELPERS = PACK_ROOT / "skills/evolve/scripts"
sys.path.insert(0, str(HELPERS))
sys.path.insert(0, str(PACK_ROOT / "scripts"))

import evolve


class RepositoryTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve() / "app with spaces"
        self.root.mkdir()
        self.git("init", "-q")
        (self.root / ".gitignore").write_text(".evolve/\n__pycache__/\n", encoding="utf-8")
        (self.root / "app.py").write_text("def value():\n    return 1\n", encoding="utf-8")
        self.git("add", ".")
        self.git("-c", "user.name=Evolve Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture")

    def git(self, *arguments):
        return subprocess.run(["git", "-C", str(self.root), *arguments], capture_output=True, check=True).stdout

    def ledger(self, *arguments):
        args = evolve.parser().parse_args(["--project", str(self.root), *arguments])
        return evolve.execute(args)

    def init(self):
        return self.ledger("init", "--goal", "Improve actual behaviour")

    def add(self, title="Fix behaviour", criteria=("regression",), dependencies=(), files=("app.py",)):
        command = ["add", "--title", title, "--evidence", "app.py:2 returns the wrong result", "--category", "correctness"]
        for criterion in criteria:
            command += ["--criterion", criterion]
        for dependency in dependencies:
            command += ["--depends-on", dependency]
        for path in files:
            command += ["--file", path]
        return self.ledger(*command)[0]

    def passing_check(self, identifier="E001", criterion="regression"):
        return self.ledger("run", "--task", identifier, "--criterion", criterion, "--", sys.executable, "-c", "print('verified')")


def call_main(function, arguments):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = function(arguments)
    payload = out.getvalue() or err.getvalue()
    return code, json.loads(payload) if payload else None
