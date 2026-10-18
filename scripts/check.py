#!/usr/bin/env python3
"""Run Evolve's package validator and local test suite without GitHub Actions."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parent.parent),
                        help="Pack checkout to validate; defaults to this script's checkout")
    args = parser.parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    if not (root / "scripts/validate.py").is_file() or not (root / "tests").is_dir():
        parser.error("Expected a pack checkout with scripts/validate.py and tests/.")

    checks = (
        ("Package validation", [sys.executable, "scripts/validate.py"]),
        ("Local tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]),
    )
    failed = False
    for name, command in checks:
        print(f"== {name} ==", flush=True)
        try:
            result = subprocess.run(command, cwd=root, capture_output=True,
                                    text=True, encoding="utf-8", errors="replace", check=False)
        except OSError as error:
            print(f"FAILED: {error}", file=sys.stderr)
            failed = True
            continue
        if result.stdout:
            print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
        if result.stderr:
            print(result.stderr, end="" if result.stderr.endswith("\n") else "\n", file=sys.stderr)
        # unittest returns zero even if discovery silently runs zero tests.
        found = re.search(r"Ran (\d+) tests? in", result.stderr + result.stdout)
        no_tests = name == "Local tests" and (not found or int(found.group(1)) == 0)
        passed = result.returncode == 0 and not no_tests
        print(f"{name}: {'PASS' if passed else 'FAIL'} (exit {result.returncode})", flush=True)
        if no_tests:
            print("No executed test count found; do not treat empty discovery as a pass.", file=sys.stderr)
        failed |= not passed
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
