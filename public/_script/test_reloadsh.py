import unittest
from io import StringIO
from unittest.mock import patch

import reloadsh


class DetectTerminalTests(unittest.TestCase):
    def test_detects_tabby(self):
        with patch.dict(reloadsh.os.environ, {"TERM_PROGRAM": "Tabby"}):
            self.assertEqual(reloadsh.detect_terminal(), "tabby")


class OpenTabbyTerminalTests(unittest.TestCase):
    def test_opens_new_tab_in_current_directory(self):
        self.assertTrue(hasattr(reloadsh, "open_tabby_terminal"))

        with (
            patch.dict(
                reloadsh.os.environ,
                {"LOCALAPPDATA": r"C:\Users\moby\AppData\Local"},
            ),
            patch("reloadsh.os.getcwd", return_value=r"C:\Work Folder"),
            patch("reloadsh.subprocess.Popen") as popen,
        ):
            reloadsh.open_tabby_terminal()

        popen.assert_called_once_with(
            [
                r"C:\Users\moby\AppData\Local\Programs\Tabby\Tabby.exe",
                "open",
                r"C:\Work Folder",
            ]
        )


class OpenWindowsTerminalTests(unittest.TestCase):
    def test_opens_new_tab_in_current_directory(self):
        self.assertTrue(hasattr(reloadsh, "open_windows_terminal"))

        with (
            patch("reloadsh.os.getcwd", return_value=r"C:\Work Folder"),
            patch("reloadsh.subprocess.Popen") as popen,
        ):
            reloadsh.open_windows_terminal()

        popen.assert_called_once_with(
            ["wt.exe", "-w", "0", "new-tab", "-d", r"C:\Work Folder"]
        )

    def test_launch_failure_keeps_current_terminal_open(self):
        self.assertTrue(hasattr(reloadsh, "open_windows_terminal"))

        with (
            patch("reloadsh.subprocess.Popen", side_effect=OSError("missing")),
            patch("reloadsh.sys.stderr", new=StringIO()),
        ):
            with self.assertRaises(SystemExit) as result:
                reloadsh.open_windows_terminal()

        self.assertEqual(result.exception.code, 10)


if __name__ == "__main__":
    unittest.main()
