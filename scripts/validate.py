#!/usr/bin/env python3
"""Validate package structure, metadata, portable links and Python syntax."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from install import SKILLS


def validate(root: Path) -> list[str]:
    errors = []
    for name in SKILLS:
        folder = root / "skills" / name
        entry = folder / "SKILL.md"
        if not entry.is_file():
            errors.append(f"Missing entrypoint: {name}")
            continue
        content = entry.read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n", content, re.S)
        if not match:
            errors.append(f"Invalid frontmatter: {name}")
            continue
        header = match.group(1)
        if not re.search(rf"^name: {re.escape(name)}$", header, re.M):
            errors.append(f"Name does not match folder: {name}")
        if not re.search(r"^description: .{30,}$", header, re.M):
            errors.append(f"Missing discriminating description: {name}")
        ui = folder / "agents/openai.yaml"
        if not ui.is_file():
            errors.append(f"Missing UI metadata: {name}")
        else:
            metadata = ui.read_text(encoding="utf-8")
            if f"${name}" not in metadata:
                errors.append(f"Default prompt must invoke ${name}")
            short = re.search(r'  short_description: "(.+)"', metadata)
            if not short or not 25 <= len(short.group(1)) <= 64:
                errors.append(f"UI short description must be 25–64 characters: {name}")
    for path in root.rglob("*"):
        if any(part in {".git", "__pycache__", ".evolve"} for part in path.relative_to(root).parts):
            continue
        if path.is_symlink():
            errors.append(f"Pack source must not contain symlinks: {path.relative_to(root)}")
        if not path.is_file():
            continue
        if path.suffix == ".py":
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
            except (SyntaxError, UnicodeError) as error:
                errors.append(f"Python syntax: {path.relative_to(root)}: {error}")
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except ValueError:
                errors.append(f"Invalid JSON: {path.relative_to(root)}")
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        for link in re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", text):
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", link) or link.startswith("#"):
                continue
            target = (path.parent / link.split("#")[0]).resolve()
            if root.resolve() not in target.parents and target != root.resolve():
                errors.append(f"Link escapes pack: {path.relative_to(root)} → {link}")
            elif not target.exists():
                errors.append(f"Broken link: {path.relative_to(root)} → {link}")
    return errors


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    args = p.parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(json.dumps({"valid": False, "errors": ["Package root does not exist."]}))
        return 1
    errors = validate(root)
    print(json.dumps({"valid": not errors, "skills": len(SKILLS), "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
