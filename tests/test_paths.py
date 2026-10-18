from pathlib import Path, PureWindowsPath
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from support import RepositoryTest
import common
import install


class PortablePathTests(unittest.TestCase):
    def test_windows_drive_rooted_path_is_rejected_even_without_a_drive(self):
        # PureWindowsPath('/outside') is rooted but not is_absolute().
        self.assertFalse(PureWindowsPath("/outside").is_absolute())
        with patch.object(common, "Path", PureWindowsPath):
            with self.assertRaises(common.EvolveError):
                common.relative_path("/outside")

    def test_redundant_separators_cannot_disguise_overlapping_scope(self):
        for path in ("a//b.py", "a/", "./a.py", "a/../b.py"):
            with self.subTest(path=path), self.assertRaises(common.EvolveError):
                common.relative_path(path)

    def test_installer_rejects_rooted_paths_before_host_path_interpretation(self):
        with patch.object(install, "Path", PureWindowsPath):
            with self.assertRaises(install.InstallError):
                install.child(Path("ordinary-root"), "/outside")

    def test_evidence_managed_path_rejects_simulated_windows_junction(self):
        # Simulates the Windows st_file_attributes contract on Linux/macOS too.
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            (root / "redirect").mkdir()
            original = Path.lstat

            def mocked_lstat(path, *args, **kwargs):
                info = original(path, *args, **kwargs)
                if path.name == "redirect":
                    return SimpleNamespace(
                        st_mode=info.st_mode,
                        st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT,
                    )
                return info

            with patch.object(Path, "lstat", mocked_lstat):
                with self.assertRaisesRegex(common.EvolveError, "Reparse point"):
                    common.managed_path(root, "redirect/state.json")

    def test_evidence_managed_path_still_allows_normal_directories(self):
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            (root / ".evolve").mkdir()
            self.assertEqual(
                common.managed_path(root, ".evolve/state.json"),
                root / ".evolve/state.json",
            )
