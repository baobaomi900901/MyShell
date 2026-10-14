import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import init


class ProfileBlockTests(unittest.TestCase):
    def test_replaces_managed_block_without_duplicates(self):
        old = "before\n" + init.zsh_block(Path("/old/MyShell")) + "\nafter\n"
        updated = init.replace_block(old, init.zsh_block(Path("/new/MyShell")))

        self.assertEqual(updated.count(init.START_MARKER), 1)
        self.assertEqual(updated.count(init.END_MARKER), 1)
        self.assertIn("after", updated)
        self.assertNotIn("/old/MyShell", updated)
        self.assertEqual(
            init.replace_block(updated, init.zsh_block(Path("/new/MyShell"))),
            updated,
        )

    def test_migrates_old_windows_block(self):
        old = "before\n" + init.OLD_POWERSHELL_BLOCK + "\n"
        updated = init.replace_block(
            old, init.powershell_block(Path("C:/MyShell")),
            legacy=(init.OLD_POWERSHELL_BLOCK,),
        )

        self.assertEqual(updated.count("$functionsDir ="), 1)
        self.assertIn(init.START_MARKER, updated)

    def test_rejects_broken_marker_pair(self):
        with self.assertRaises(init.InstallError):
            init.replace_block(init.START_MARKER + "\n", "new block")


class PathChoiceTests(unittest.TestCase):
    def test_move_choice_defaults_to_no(self):
        with patch("builtins.input", return_value=""):
            self.assertFalse(init.ask_to_move(Path("/tmp/current"), Path("/tmp/target")))

    def test_moves_entire_project(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "download" / "MyShell"
            target = Path(temp) / "standard" / "MyShell"
            source.mkdir(parents=True)
            (source / "init.py").write_text("example", encoding="utf-8")
            original_cwd = Path.cwd()
            try:
                result = init.move_project(source, target)
            finally:
                os.chdir(original_cwd)

            self.assertEqual(result, target)
            self.assertEqual((target / "init.py").read_text(encoding="utf-8"), "example")
            self.assertFalse(source.exists())


class InstallationFlowTests(unittest.TestCase):
    def test_macos_runs_reloadsh_then_hsh(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            root = Path(temp) / "MyShell"
            home.mkdir()
            root.mkdir()
            with (
                patch.object(init.Path, "home", return_value=home),
                patch("init.shutil.which", side_effect=lambda name: "/usr/bin/" + name),
                patch("init.ensure_python_module"),
                patch("init.install_tracked_packages"),
                patch("init.run") as run,
            ):
                init.install_macos(root)

            commands = [call.args[0] for call in run.call_args_list]
            self.assertEqual(
                commands,
                [["zsh", "-i", "-c", "reloadsh"], ["zsh", "-i", "-c", "hsh"]],
            )
            profile = (home / ".zshrc").read_text(encoding="utf-8")
            self.assertIn("compinit", profile)
            self.assertIn(str(root), profile)

    def test_windows_runs_reloadsh_without_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "MyShell"
            profile = Path(temp) / "profile.ps1"
            root.mkdir()
            with (
                patch("init.shutil.which", side_effect=lambda name: name if name in {"python", "powershell"} else None),
                patch("init.powershell_profile", return_value=profile),
                patch("init.ensure_python_module"),
                patch("init.install_tracked_packages"),
                patch("init.update_windows_environment"),
                patch("init.run") as run,
            ):
                init.install_windows(root)

            command = run.call_args.args[0]
            self.assertIn("reloadsh --no-restart", command[-1])
            self.assertIn("$LASTEXITCODE -ne 0", command[-1])
            self.assertIn("$env:MYSHELL", profile.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
