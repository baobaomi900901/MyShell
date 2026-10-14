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


class LicenseMachineIdClipboardTests(unittest.TestCase):
    VALID_MACHINE_ID = "UEBF14D0A25DB325931012EE0323C157D"

    def test_valid_machine_id_from_clipboard_is_accepted(self):
        with patch("license_lite.pyperclip.paste", return_value=self.VALID_MACHINE_ID):
            self.assertEqual(
                license_lite.read_machine_id_from_clipboard(),
                self.VALID_MACHINE_ID,
            )

    def test_whitespace_around_clipboard_is_trimmed(self):
        with patch(
            "license_lite.pyperclip.paste",
            return_value=f"  {self.VALID_MACHINE_ID}\r\n",
        ):
            self.assertEqual(
                license_lite.read_machine_id_from_clipboard(),
                self.VALID_MACHINE_ID,
            )

    def test_invalid_clipboard_is_ignored(self):
        invalid_values = [
            "",
            "UEBF",
            "XEBF14D0A25DB325931012EE0323C157D",
            self.VALID_MACHINE_ID + "A",
            "license code from previous run",
        ]
        for value in invalid_values:
            with self.subTest(value=value):
                with patch("license_lite.pyperclip.paste", return_value=value):
                    self.assertIsNone(license_lite.read_machine_id_from_clipboard())

    def test_clipboard_read_error_is_ignored(self):
        with patch(
            "license_lite.pyperclip.paste",
            side_effect=RuntimeError("clipboard unavailable"),
        ):
            self.assertIsNone(license_lite.read_machine_id_from_clipboard())

    def test_prompt_uses_clipboard_default_when_user_presses_enter(self):
        with patch(
            "license_lite.read_machine_id_from_clipboard",
            return_value=self.VALID_MACHINE_ID,
        ), patch("builtins.input", return_value=""), patch("builtins.print"):
            self.assertEqual(
                license_lite.prompt_machine_id_single_interactive(),
                self.VALID_MACHINE_ID,
            )

    def test_prompt_allows_overriding_clipboard_default(self):
        replacement = "U" + "A" * 31
        with patch(
            "license_lite.read_machine_id_from_clipboard",
            return_value=self.VALID_MACHINE_ID,
        ), patch("builtins.input", return_value=replacement), patch("builtins.print"):
            self.assertEqual(
                license_lite.prompt_machine_id_single_interactive(),
                replacement,
            )

    def test_prompt_falls_back_to_manual_input_without_valid_clipboard(self):
        with patch("license_lite.read_machine_id_from_clipboard", return_value=None), patch(
            "builtins.input",
            return_value=self.VALID_MACHINE_ID,
        ), patch("builtins.print"):
            self.assertEqual(
                license_lite.prompt_machine_id_single_interactive(),
                self.VALID_MACHINE_ID,
            )


if __name__ == "__main__":
    unittest.main()
