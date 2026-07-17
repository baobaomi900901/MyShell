import os
import unittest
from pathlib import Path
from unittest.mock import patch

import license_lite
import license_rpa


class LicenseToolPathTests(unittest.TestCase):
    def test_lite_executable_is_relative_to_myshell(self):
        root = Path(r"C:\MyShell")
        with patch.dict(os.environ, {"MYSHELL": str(root)}):
            actual = Path(license_lite.get_default_exe_path())

        self.assertEqual(
            actual,
            root / "config" / "private" / "tools" / "LiteLicense.exe",
        )

    def test_rpa_executable_is_relative_to_myshell(self):
        self.assertTrue(hasattr(license_rpa, "get_default_exe_path"))

        root = Path(r"C:\MyShell")
        with patch.dict(os.environ, {"MYSHELL": str(root)}):
            actual = Path(license_rpa.get_default_exe_path())

        self.assertEqual(
            actual,
            root / "config" / "private" / "tools" / "LicensesMake.exe",
        )


if __name__ == "__main__":
    unittest.main()
