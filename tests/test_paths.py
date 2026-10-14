from pathlib import Path, PureWindowsPath
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
