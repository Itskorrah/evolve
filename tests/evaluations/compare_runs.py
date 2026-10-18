#!/usr/bin/env python3
"""Compare matched agent trials without inventing quality or token measurements."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ALLOWED = {"pass", "fail", "not_run"}


def read_record(path: Path) -> dict:
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValueError("Evaluation record must be a JSON object")
    for key in ("scenario", "host", "model", "starting_revision"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            raise ValueError(f"Missing evaluation identifier: {key}")
    checks = record.get("checks")
    if not isinstance(checks, dict) or not checks:
        raise ValueError("Checks must be a nonempty mapping")
    for name, check in checks.items():
        if not isinstance(name, str) or not isinstance(check, dict) or check.get("status") not in ALLOWED:
            raise ValueError(f"Invalid check: {name}")
        if check["status"] != "not_run" and not check.get("evidence"):
            raise ValueError(f"Executed check requires an evidence reference: {name}")
    tokens = record.get("tokens")
    if tokens is not None and (not isinstance(tokens, dict) or any(
        type(tokens.get(key)) is not int or tokens[key] < 0 for key in ("input", "output")
    )):
        raise ValueError("Tokens must be null or non-negative integer input/output counts")
    return record


def compare(before: dict, after: dict) -> dict:
    for key in ("scenario", "host", "model", "starting_revision"):
        if before[key] != after[key]:
            raise ValueError(f"Incomparable trials: {key} differs")
    if set(before["checks"]) != set(after["checks"]):
        raise ValueError("Incomparable trials: check identifiers differ")
    token_delta = None
    if before.get("tokens") is not None and after.get("tokens") is not None:
        token_delta = {key: after["tokens"][key] - before["tokens"][key]
                       for key in ("input", "output")}
    return {
        "scenario": before["scenario"], "host": before["host"], "model": before["model"],
        "checks": {key: {"without": before["checks"][key]["status"],
                         "with_evolve": after["checks"][key]["status"]}
                   for key in sorted(before["checks"])},
        "token_delta": token_delta,
        "limit": "Descriptive matched trials, not proof that Evolve caused differences. Review raw diffs and evidence.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--without", required=True, type=Path)
    parser.add_argument("--with-evolve", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        output = compare(read_record(args.without), read_record(args.with_evolve))
    except (ValueError, OSError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
