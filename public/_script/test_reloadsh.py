import unittest
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from io import StringIO
from unittest.mock import ANY, patch

import reloadsh


class DependencyScanTests(unittest.TestCase):
    def test_skips_local_modules_and_test_only_imports(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "common.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "worker.py").write_text(
                "import common\nimport colorama\n", encoding="utf-8"
            )
            (root / "test_worker.py").write_text("import pytest\n", encoding="utf-8")

            self.assertEqual(reloadsh.get_third_party_packages(root), ["colorama"])


class DetectTerminalTests(unittest.TestCase):
    def test_detects_tabby(self):
        with patch.dict(reloadsh.os.environ, {"TERM_PROGRAM": "Tabby"}):
            self.assertEqual(reloadsh.detect_terminal(), "tabby")

    def test_ignores_surrounding_whitespace(self):
        with patch.dict(reloadsh.os.environ, {"TERM_PROGRAM": " Tabby "}):
            self.assertEqual(reloadsh.detect_terminal(), "tabby")


class TerminalLaunchTests(unittest.TestCase):
    def launch(self, source, **kwargs):
        return reloadsh.open_terminal("测试终端", [sys.executable, "-c", source], **kwargs)

    def test_nonzero_exit_keeps_current_terminal_and_reports_diagnostics(self):
        with patch("reloadsh.sys.stderr", new=StringIO()) as diagnostics:
            with self.assertRaises(SystemExit) as result:
                self.launch("import sys; print('startup failed', file=sys.stderr); sys.exit(7)")
        self.assertEqual(result.exception.code, 10)
        self.assertIn("7", diagnostics.getvalue())
        self.assertIn("startup failed", diagnostics.getvalue())
        self.assertIn("当前终端", diagnostics.getvalue())

    def test_uncaught_exception_is_failure_even_with_zero_exit(self):
        with patch("reloadsh.sys.stderr", new=StringIO()) as diagnostics:
            with self.assertRaises(SystemExit) as result:
                self.launch("print('uncaughtException: TypeError: mixin.stripAnsi is not a function')")
        self.assertEqual(result.exception.code, 10)
        self.assertIn("mixin.stripAnsi", diagnostics.getvalue())

    def test_deprecation_warning_does_not_fail_launch(self):
        with patch("reloadsh.sys.stderr", new=StringIO()) as diagnostics:
            self.launch("import sys; print('DeprecationWarning: fs.Stats constructor is deprecated', file=sys.stderr)")
        self.assertIn("DeprecationWarning", diagnostics.getvalue())

    def test_large_output_does_not_block_and_diagnostics_are_bounded(self):
        with patch("reloadsh.sys.stderr", new=StringIO()) as diagnostics:
            with self.assertRaises(SystemExit):
                self.launch("import sys; print('x' * 200000); print('FATAL: launch failed'); sys.exit(1)")
        self.assertIn("FATAL: launch failed", diagnostics.getvalue())
        self.assertLess(len(diagnostics.getvalue()), 9000)

    def test_fatal_output_before_large_log_is_not_lost_with_zero_exit(self):
        with patch("reloadsh.sys.stderr", new=StringIO()) as diagnostics:
            with self.assertRaises(SystemExit) as result:
                self.launch("print('uncaughtException: TypeError: startup failed'); print('x' * 20000)")
        self.assertEqual(result.exception.code, 10)
        self.assertLess(len(diagnostics.getvalue()), 9000)

    def test_midline_error_text_at_chunk_boundary_is_not_an_exception(self):
        with patch("reloadsh.sys.stderr", new=StringIO()):
            self.launch("print('.' * 8192 + 'Error:' + '.' * 20000)")

    def test_running_terminal_is_not_terminated_on_observation_timeout(self):
        real_popen = subprocess.Popen
        children = []

        def spawn(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            children.append(process)
            return process

        try:
            with patch("reloadsh.subprocess.Popen", side_effect=spawn):
                self.launch("import time; time.sleep(30)", startup_timeout=0.05)
            self.assertIsNone(children[0].poll())
        finally:
            for child in children:
                child.terminate()
                child.wait(timeout=5)


class OpenTabbyTerminalTests(unittest.TestCase):
    def test_opens_new_tab_in_current_directory(self):
        self.assertTrue(hasattr(reloadsh, "open_tabby_terminal"))

        with (
            patch.dict(
                reloadsh.os.environ,
                {"LOCALAPPDATA": r"C:\Users\moby\AppData\Local"},
            ),
            patch("reloadsh.os.getcwd", return_value=r"C:\Work Folder"),
            patch("shutil.which", return_value=None),
            patch("reloadsh.Path.is_file", return_value=True),
            patch("reloadsh.subprocess.Popen") as popen,
        ):
            popen.return_value.wait.return_value = 0
            reloadsh.open_tabby_terminal()

        popen.assert_called_once_with(
            [
                os.path.join(r"C:\Users\moby\AppData\Local", "Programs", "Tabby", "Tabby.exe"),
                "open",
                r"C:\Work Folder",
            ],
            stdin=subprocess.DEVNULL,
            stdout=ANY,
            stderr=subprocess.STDOUT,
        )

    def test_finds_tabby_on_path_without_localappdata(self):
        with (
            patch.dict(reloadsh.os.environ, {}, clear=True),
            patch("shutil.which", return_value=r"D:\Apps\Tabby.exe"),
            patch("reloadsh.open_terminal") as launch,
            patch("reloadsh.os.getcwd", return_value=r"C:\Work Folder"),
        ):
            reloadsh.open_tabby_terminal()
        launch.assert_called_once_with("Tabby", [r"D:\Apps\Tabby.exe", "open", r"C:\Work Folder"])

    def test_missing_tabby_does_not_attempt_launch(self):
        with (
            patch.dict(reloadsh.os.environ, {}, clear=True),
            patch("shutil.which", return_value=None),
            patch("reloadsh.open_terminal") as launch,
            patch("reloadsh.sys.stderr", new=StringIO()),
        ):
            with self.assertRaises(SystemExit) as result:
                reloadsh.open_tabby_terminal()
        self.assertEqual(result.exception.code, 10)
        launch.assert_not_called()

    def test_finds_system_installation(self):
        with (
            patch.dict(reloadsh.os.environ, {"ProgramFiles": r"D:\Program Files"}, clear=True),
            patch("shutil.which", return_value=None),
            patch("reloadsh.Path.is_file", return_value=True),
            patch("reloadsh.open_terminal") as launch,
            patch("reloadsh.os.getcwd", return_value=r"C:\Work Folder"),
        ):
            reloadsh.open_tabby_terminal()
        launch.assert_called_once_with("Tabby", [str(Path(r"D:\Program Files") / "Tabby" / "Tabby.exe"), "open", r"C:\Work Folder"])


class OpenWindowsTerminalTests(unittest.TestCase):
    def test_opens_new_tab_in_current_directory(self):
        self.assertTrue(hasattr(reloadsh, "open_windows_terminal"))

        with (
            patch("reloadsh.os.getcwd", return_value=r"C:\Work Folder"),
            patch("reloadsh.subprocess.Popen") as popen,
        ):
            popen.return_value.wait.return_value = 0
            reloadsh.open_windows_terminal()

        popen.assert_called_once_with(
            ["wt.exe", "-w", "0", "new-tab", "-d", r"C:\Work Folder"],
            stdin=subprocess.DEVNULL,
            stdout=ANY,
            stderr=subprocess.STDOUT,
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


class RestartConfirmationTests(unittest.TestCase):
    def restart(self, answer):
        self.assertTrue(hasattr(reloadsh, "restart_windows_terminal"))
        with (
            patch("reloadsh.detect_terminal", return_value="tabby"),
            patch("reloadsh.open_tabby_terminal"),
            patch("reloadsh.questionary.confirm") as confirm,
            patch("reloadsh.sys.stdout", new=StringIO()) as output,
        ):
            confirm.return_value.ask.return_value = answer
            result = reloadsh.restart_windows_terminal()
        self.assertFalse(confirm.call_args.kwargs["default"])
        self.assertNotIn("新标签页已打开", output.getvalue())
        return result

    def test_closes_only_after_explicit_confirmation(self):
        self.assertIs(self.restart(True), True)

    def test_no_answer_keeps_current_terminal(self):
        for answer in (False, None):
            with self.subTest(answer=answer):
                self.assertIs(self.restart(answer), False)

    def test_ctrl_c_keeps_current_terminal(self):
        self.assertTrue(hasattr(reloadsh, "restart_windows_terminal"))
        with (
            patch("reloadsh.detect_terminal", return_value="vscode"),
            patch("reloadsh.send_vscode_combo"),
            patch("reloadsh.time.sleep"),
            patch("reloadsh.questionary.confirm") as confirm,
            patch("reloadsh.sys.stdout", new=StringIO()),
        ):
            confirm.return_value.ask.side_effect = KeyboardInterrupt
            self.assertFalse(reloadsh.restart_windows_terminal())


class MainRestartTests(unittest.TestCase):
    def run_main(self, answer, extra_args=(), launch_error=None):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            argv = ["reloadsh", "--system-dir", directory, "--json-file", str(root / "tracker.json"), "--system-type", "windows", *extra_args]
            with (
                patch("reloadsh.sys.argv", argv),
                patch("reloadsh.load_pip_config", return_value=([], {})),
                patch("reloadsh.detect_terminal", return_value="tabby"),
                patch("reloadsh.open_tabby_terminal") as launch,
                patch("reloadsh.questionary.select") as select,
                patch("reloadsh.questionary.confirm") as confirm,
                patch("reloadsh.sys.stdout", new=StringIO()) as output,
            ):
                select.return_value.ask.return_value = "Yes"
                confirm.return_value.ask.return_value = answer
                launch.side_effect = launch_error
                with self.assertRaises(SystemExit) as result:
                    reloadsh.main()
            self.assertNotIn("已重新加载所有函数文件", output.getvalue())
            return result.exception.code, launch.call_count, select.call_count, confirm.call_count

    def test_unconfirmed_new_terminal_never_returns_close_code(self):
        self.assertEqual(self.run_main(False), (0, 1, 1, 1))

    def test_confirmed_new_terminal_returns_close_code(self):
        self.assertEqual(self.run_main(True), (43, 1, 1, 1))

    def test_no_restart_skips_both_launch_and_confirmation(self):
        self.assertEqual(self.run_main(None, ("--no-restart",)), (0, 0, 0, 0))

    def test_failed_launch_never_asks_to_close_current_terminal(self):
        self.assertEqual(self.run_main(True, launch_error=SystemExit(10)), (10, 1, 1, 0))


POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")


@unittest.skipUnless(POWERSHELL, "PowerShell is not installed")
class PowerShellWrapperTests(unittest.TestCase):
    def run_wrapper(self, python_body, setup=""):
        root = Path(__file__).resolve().parents[2]
        quoted_root = str(root).replace("'", "''")
        script = f"""
$ErrorActionPreference = 'SilentlyContinue'
$env:myshell = '{quoted_root}'
. (Join-Path $env:myshell 'Windows/MT_General/reloadsh.ps1')
$global:closed = 0
function global:python {{ {python_body} }}
function global:closeTerminal {{ param($Seconds); $global:closed++ }}
{setup}
$global:LASTEXITCODE = 43
reloadsh
Write-Output ('RESULT:' + $global:LASTEXITCODE + ':' + $global:closed)
"""
        result = subprocess.run([POWERSHELL, "-NoProfile", "-NonInteractive", "-Command", script], capture_output=True, encoding="utf-8", errors="replace", timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_only_close_code_closes_terminal(self):
        for code in (0, 10, 43):
            with self.subTest(code=code):
                output = self.run_wrapper(f"$global:LASTEXITCODE = {code}")
                self.assertIn(f"RESULT:{code}:{int(code == 43)}", output)

    def test_python_invocation_exception_replaces_stale_close_code(self):
        self.assertIn("RESULT:10:0", self.run_wrapper("throw 'python invocation failed'"))

    def test_missing_python_does_not_use_stale_close_code(self):
        setup = r"""
function global:Get-Command {
    param($Name)
    if ($Name -eq 'python') { return $null }
    Microsoft.PowerShell.Core\Get-Command $Name -ErrorAction SilentlyContinue
}
"""
        self.assertIn("RESULT:10:0", self.run_wrapper("throw 'must not invoke missing Python'", setup))

    def test_real_python_close_code_is_not_rejected_by_native_error_policy(self):
        wrapper = Path(__file__).resolve().parents[2] / "Windows/MT_General/reloadsh.ps1"
        quoted_wrapper = str(wrapper).replace("'", "''")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            helper = root / "public/_script/reloadsh.py"
            helper.parent.mkdir(parents=True)
            helper.write_text("import sys\nprint('ARGS:' + repr(sys.argv[1:]))\nsys.exit(43)\n", encoding="utf-8")
            quoted_root = str(root).replace("'", "''")
            script = f"""
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
$env:myshell = '{quoted_root}'
. '{quoted_wrapper}'
$global:closed = 0
function global:closeTerminal {{ param($Seconds); $global:closed++ }}
reloadsh --no-restart
Write-Output ('RESULT:' + $global:LASTEXITCODE + ':' + $global:closed)
"""
            result = subprocess.run([POWERSHELL, "-NoProfile", "-NonInteractive", "-Command", script], capture_output=True, encoding="utf-8", errors="replace", timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("RESULT:43:1", result.stdout)
        self.assertIn("--no-restart", result.stdout)


if __name__ == "__main__":
    unittest.main()
