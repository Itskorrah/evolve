#!/usr/bin/env python3
"""Install/update/remove Evolve skills with checksum ownership and edit protection."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

PACK_ROOT = Path(__file__).resolve().parent.parent
SKILLS = ("evolve", "evolve-audit", "evolve-build", "evolve-design", "evolve-verify", "evolve-ship")
MANIFEST = ".evolve-install.json"
PACK_ID = "Itskorrah/evolve"


class InstallError(Exception):
    pass


class InstallLock:
    def __init__(self, target: Path):
        self.path = child(target, ".evolve-install.lock")

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + 5
        while True:
            try:
                descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                with os.fdopen(descriptor, "w") as handle:
                    handle.write(f"pid={os.getpid()}\n")
                return self
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise InstallError("Installation is locked. Wait for the writer; after a crash verify no writer remains before removing .evolve-install.lock.")
                time.sleep(0.05)

    def __exit__(self, *unused):
        self.path.unlink()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_path(path: Path) -> None:
    for item in (path, *path.parents):
        if item.is_symlink():
            raise InstallError(f"Symlink in installation path: {item}")


def child(root: Path, relative: str) -> Path:
    if not relative or relative.startswith("/") or "\\" in relative or ":" in relative:
        raise InstallError("Invalid managed relative path.")
    candidate = Path(relative)
    if candidate.is_absolute() or any(p in {"", ".", ".."} for p in relative.split("/")):
        raise InstallError("Traversal in managed path is refused.")
    result = root / candidate
    check_path(result)
    return result


def target_for(args) -> Path:
    if args.target:
        if args.project or args.scope == "global":
            raise InstallError("Use --target by itself; do not combine it with --project or global scope.")
        result = Path(args.target).expanduser().absolute()
    else:
        if args.host == "portable":
            raise InstallError("Portable installation requires --target.")
        if args.scope == "global":
            if args.project:
                raise InstallError("Global scope does not take --project.")
            base = Path.home()
        else:
            if not args.project:
                raise InstallError("Project scope requires --project.")
            base = Path(args.project).expanduser().absolute()
            if not base.is_dir():
                raise InstallError("The application project directory must already exist.")
        result = base / (".claude/skills" if args.host == "claude" else ".agents/skills")
    check_path(result)
    source = PACK_ROOT / "skills"
    if result.resolve() == source.resolve() or source.resolve() in result.resolve().parents:
        raise InstallError("Do not install into the pack's source skills directory.")
    return result


def read_manifest(target: Path) -> dict:
    path = child(target, MANIFEST)
    if not path.exists():
        return {"version": 1, "pack": PACK_ID, "skills": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as error:
        raise InstallError("Installation manifest is unreadable; preserve it before recovery.") from error
    if not isinstance(data, dict) or data.get("version") != 1 or data.get("pack") != PACK_ID or not isinstance(data.get("skills"), dict):
        raise InstallError("Unknown installation manifest; refusing to adopt files.")
    for name, files in data["skills"].items():
        if name not in SKILLS or not isinstance(files, dict):
            raise InstallError("Invalid skill ownership in manifest.")
        for relative, checksum in files.items():
            child(target, f"{name}/{relative}")
            if not isinstance(checksum, str) or len(checksum) != 64:
                raise InstallError("Invalid file checksum in manifest.")
    return data


def source_files(name: str) -> dict[str, bytes]:
    source = PACK_ROOT / "skills" / name
    if not (source / "SKILL.md").is_file():
        raise InstallError(f"Source skill is missing: {name}")
    files = {}
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise InstallError(f"Symlink in skill source: {path}")
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        if path.is_file():
            files[path.relative_to(source).as_posix()] = path.read_bytes()
    files["LICENSE"] = (PACK_ROOT / "LICENSE").read_bytes()
    return files


def verify_owned(target: Path, name: str, owned: dict, uninstall: bool) -> None:
    folder = child(target, name)
    if folder.exists():
        if not folder.is_dir():
            raise InstallError(f"Skill path is not a directory: {name}")
        for path in folder.rglob("*"):
            if path.is_symlink():
                raise InstallError(f"Symlink in installed skill: {path}")
    for relative, checksum in owned.items():
        path = child(target, f"{name}/{relative}")
        if not path.exists():
            if uninstall:
                continue
            raise InstallError(f"Locally removed managed file: {name}/{relative}. Preserve/reset your installation explicitly before updating.")
        if not path.is_file() or digest(path.read_bytes()) != checksum:
            raise InstallError(f"Locally edited managed file: {name}/{relative}. Preserve the edit before updating or removing.")


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".evolve-install-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def prune(folder: Path) -> None:
    if not folder.exists():
        return
    directories = sorted((p for p in folder.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True)
    for path in [*directories, folder]:
        try:
            path.rmdir()
        except OSError:
            pass  # Keep any user-added files and their parent directories.


def operate(args) -> dict:
    target = target_for(args)
    if args.dry_run:
        return operate_locked(args, target)
    with InstallLock(target):
        return operate_locked(args, target)


def operate_locked(args, target: Path) -> dict:
    manifest = read_manifest(target)
    selected = list(dict.fromkeys(args.skill or (SKILLS if args.action == "install" else manifest["skills"])))
    if args.action == "install" and "evolve" not in selected:
        selected.insert(0, "evolve")
    if args.action == "uninstall" and "evolve" in selected:
        remaining = set(manifest["skills"]) - set(selected)
        if remaining:
            raise InstallError("Remove specialist skills before removing their evolve support folder.")
    payload = {}
    for name in selected:
        folder = child(target, name)
        owned = manifest["skills"].get(name)
        if args.action == "uninstall" and owned is None:
            raise InstallError(f"Skill is not owned by this installation: {name}")
        if args.action == "install" and folder.exists() and owned is None:
            raise InstallError(f"Unmanaged skill folder exists: {name}; refusing to overwrite it.")
        verify_owned(target, name, owned or {}, args.action == "uninstall")
        if args.action == "install":
            payload[name] = source_files(name)
            for relative in payload[name]:
                path = child(target, f"{name}/{relative}")
                if path.exists() and relative not in (owned or {}):
                    raise InstallError(f"A user-added file conflicts with new release content: {name}/{relative}")
    result = {"action": args.action, "target": str(target), "skills": selected,
              "dry_run": args.dry_run, "files": sum(len(v) for v in payload.values())}
    if args.dry_run or not selected:
        return result
    target.mkdir(parents=True, exist_ok=True)
    # Preflight all selected skills before any writes. Each file replacement is
    # atomic; a whole-pack update is deliberately not advertised as transactional.
    for name in selected:
        previous = manifest["skills"].get(name, {})
        if args.action == "install":
            for relative, content in payload[name].items():
                atomic_write(child(target, f"{name}/{relative}"), content)
            removed = set(previous) - set(payload[name])
            manifest["skills"][name] = {p: digest(c) for p, c in payload[name].items()}
        else:
            removed = set(previous)
            del manifest["skills"][name]
        for relative in removed:
            path = child(target, f"{name}/{relative}")
            if path.exists():
                path.unlink()
        prune(child(target, name))
    manifest_path = child(target, MANIFEST)
    if manifest["skills"]:
        atomic_write(manifest_path, (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())
    elif manifest_path.exists():
        manifest_path.unlink()
    return result


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("install", "uninstall"))
    p.add_argument("--host", choices=("codex", "claude", "agents", "portable"), default="codex")
    p.add_argument("--scope", choices=("project", "global"), default="project")
    p.add_argument("--project")
    p.add_argument("--target")
    p.add_argument("--skill", choices=SKILLS, action="append")
    p.add_argument("--dry-run", action="store_true")
    try:
        result = operate(p.parse_args(argv))
        print(json.dumps(result, indent=2))
        return 0
    except (InstallError, OSError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
