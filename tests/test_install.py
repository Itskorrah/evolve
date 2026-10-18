from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

from support import RepositoryTest, call_main
import install


class InstallationTests(RepositoryTest):
    def setUp(self):
        super().setUp()
        self.target = self.root / "agent skills"

    def invoke(self, action="install", *options):
        return call_main(install.main, [action, "--target", str(self.target), *options])

    def test_install_contains_six_skills_and_self_contained_coordinator(self):
        code, result = self.invoke()
        self.assertEqual(code, 0)
        self.assertEqual(len(result["skills"]), 6)
        for name in install.SKILLS:
            self.assertTrue((self.target / name / "SKILL.md").is_file())
            self.assertTrue((self.target / name / "LICENSE").is_file())
        self.assertTrue((self.target / "evolve/scripts/evolve.py").is_file())
        self.assertTrue((self.target / install.MANIFEST).is_file())

    def test_selecting_specialist_also_installs_coordinator(self):
        _, result = self.invoke("install", "--skill", "evolve-build")
        self.assertEqual(result["skills"], ["evolve", "evolve-build"])

    def test_dry_run_does_not_create_target(self):
        code, result = self.invoke("install", "--dry-run")
        self.assertEqual(code, 0)
        self.assertTrue(result["dry_run"])
        self.assertFalse(self.target.exists())

    def test_update_is_repeatable_and_preserves_unrelated_content(self):
        self.invoke()
        (self.target / "unrelated").mkdir()
        (self.target / "unrelated/notes.md").write_text("keep")
        (self.target / "evolve/my-notes.md").write_text("keep this too")
        self.assertEqual(self.invoke()[0], 0)
        self.assertEqual((self.target / "unrelated/notes.md").read_text(), "keep")
        self.assertEqual((self.target / "evolve/my-notes.md").read_text(), "keep this too")

    def test_local_edit_prevents_update_and_uninstall(self):
        self.invoke()
        path = self.target / "evolve/SKILL.md"
        path.write_text("local customisation")
        for operation in ("install", "uninstall"):
            code, result = self.invoke(operation)
            self.assertEqual(code, 2)
            self.assertIn("Locally edited", result["error"])
            self.assertEqual(path.read_text(), "local customisation")

    def test_local_deletion_is_not_silently_restored_on_update(self):
        self.invoke()
        (self.target / "evolve/SKILL.md").unlink()
        self.assertEqual(self.invoke()[0], 2)

    def test_unmanaged_skill_is_never_adopted(self):
        (self.target / "evolve").mkdir(parents=True)
        (self.target / "evolve/SKILL.md").write_text("mine")
        code, result = self.invoke()
        self.assertEqual(code, 2)
        self.assertIn("Unmanaged", result["error"])

    def test_uninstall_keeps_user_added_files(self):
        self.invoke()
        (self.target / "evolve/custom.md").write_text("personal")
        self.assertEqual(self.invoke("uninstall")[0], 0)
        self.assertEqual((self.target / "evolve/custom.md").read_text(), "personal")
        self.assertFalse((self.target / "evolve/SKILL.md").exists())
        self.assertFalse((self.target / install.MANIFEST).exists())

    def test_uninstall_preserves_user_created_empty_directories(self):
        self.invoke()
        (self.target / "evolve/my-empty-folder").mkdir()
        (self.target / "evolve/nested/empty-folder").mkdir(parents=True)
        self.assertEqual(self.invoke("uninstall")[0], 0)
        self.assertTrue((self.target / "evolve/my-empty-folder").is_dir())
        self.assertTrue((self.target / "evolve/nested/empty-folder").is_dir())

    def test_update_preserves_user_created_empty_directories(self):
        self.invoke()
        (self.target / "evolve/my-empty-folder").mkdir()
        self.assertEqual(self.invoke("install")[0], 0)
        self.assertTrue((self.target / "evolve/my-empty-folder").is_dir())

    def test_coordinator_cannot_be_removed_before_remaining_specialists(self):
        self.invoke()
        self.assertEqual(self.invoke("uninstall", "--skill", "evolve")[0], 2)

    def test_tampered_manifest_cannot_escape_installation_root(self):
        self.invoke()
        manifest = self.target / install.MANIFEST
        data = json.loads(manifest.read_text())
        data["skills"]["evolve"]["../../app.py"] = "0" * 64
        manifest.write_text(json.dumps(data))
        self.assertEqual(self.invoke("uninstall")[0], 2)
        self.assertTrue((self.root / "app.py").exists())

    def test_symlinked_installation_path_is_refused(self):
        outside = self.root / "outside"
        outside.mkdir()
        try:
            self.target.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Symlinks unavailable on this host")
        self.assertEqual(self.invoke()[0], 2)
        self.assertEqual(list(outside.iterdir()), [])

    def test_project_install_uses_shared_agents_directory(self):
        code, result = call_main(install.main, ["install", "--host", "codex", "--project", str(self.root), "--dry-run"])
        self.assertEqual(code, 0)
        self.assertEqual(Path(result["target"]), self.root / ".agents/skills")

    def test_verify_is_read_only_and_reports_source_match(self):
        self.invoke()
        manifest_path = self.target / install.MANIFEST
        before = manifest_path.read_bytes()
        code, report = self.invoke("verify")
        self.assertEqual(code, 0)
        self.assertEqual(report["integrity"], "verified")
        self.assertEqual(report["source_pack_version"], install.PACK_VERSION)
        self.assertEqual(report["installed_pack_version"], install.PACK_VERSION)
        self.assertEqual(report["outdated"], [])
        self.assertEqual(len(report["source_matches"]), len(install.SKILLS))
        self.assertTrue(all(report["source_matches"].values()))
        self.assertEqual(manifest_path.read_bytes(), before)
        self.assertFalse((self.target / ".evolve-install.lock").exists())

    def test_verify_detects_outdated_source_without_writing(self):
        self.invoke()
        path = self.target / install.MANIFEST
        before = path.read_bytes()
        old = install.PACK_VERSION
        try:
            install.PACK_VERSION = "new-package-not-yet-installed"
            code, report = self.invoke("verify")
            self.assertEqual(code, 0)
            self.assertEqual(report["installed_pack_version"], old)
            self.assertEqual(report["source_pack_version"], install.PACK_VERSION)
            self.assertEqual(report["outdated"], [])  # source bytes still match
        finally:
            install.PACK_VERSION = old
        self.assertEqual(path.read_bytes(), before)

    def test_verify_rejects_tampered_installed_file(self):
        self.invoke()
        (self.target / "evolve/SKILL.md").write_text("edited locally", encoding="utf-8")
        code, result = self.invoke("verify")
        self.assertEqual(code, 2)
        self.assertIn("Locally edited", result["error"])

    def test_verify_rejects_unknown_installation(self):
        code, result = self.invoke("verify")
        self.assertEqual(code, 2)
        self.assertIn("No installed skills", result["error"])
        self.assertFalse(self.target.exists())

    def test_invalid_hex_checksum_rejected_before_removal(self):
        self.invoke()
        manifest = self.target / install.MANIFEST
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["skills"]["evolve"]["SKILL.md"] = "x" * 64
        manifest.write_text(json.dumps(data), encoding="utf-8")
        code, result = self.invoke("uninstall")
        self.assertEqual(code, 2)
        self.assertIn("checksum", result["error"])
        self.assertTrue((self.target / "evolve/SKILL.md").exists())

    def test_windows_junction_target_is_refused(self):
        if sys.platform != "win32":
            self.skipTest("Windows junction contract")
        outside = self.root / "outside-junction"
        outside.mkdir()
        process = subprocess.run(["cmd", "/c", "mklink", "/J", str(self.target), str(outside)],
                                 capture_output=True, text=True)
        if process.returncode:
            self.skipTest("Junction creation unavailable")
        self.assertEqual(self.invoke()[0], 2)
        self.assertEqual(list(outside.iterdir()), [])

    def test_verify_distinguishes_unchanged_old_payload_from_changed_checkout(self):
        self.invoke()
        original = install.source_files

        def updated_source(name):
            files = original(name)
            if name == "evolve-build":
                files["SKILL.md"] += b"\\n<!-- new upstream skill contents -->\\n"
            return files

        with patch.object(install, "source_files", side_effect=updated_source):
            code, report = self.invoke("verify")
            self.assertEqual(code, 0)
            self.assertEqual(report["integrity"], "verified")
            self.assertEqual(report["outdated"], ["evolve-build"])
            self.assertFalse(report["source_matches"]["evolve-build"])
            self.assertEqual(self.invoke("install", "--skill", "evolve-build")[0], 0)
            self.assertEqual(self.invoke("verify")[1]["outdated"], [])
        self.assertEqual(self.invoke("verify")[1]["outdated"], ["evolve-build"])
