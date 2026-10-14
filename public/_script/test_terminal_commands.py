import pathlib
import tempfile
import unittest
from unittest import mock

import git_commands
import gswitch
import shell_commands


class GitCommandTests(unittest.TestCase):
    def test_arguments_preserve_spaces_and_platform_push_behavior(self):
        self.assertEqual(git_commands.git_arguments("ga", ["a b.txt"], "mac"), ["add", "a b.txt"])
        self.assertEqual(git_commands.git_arguments("gcmt", ["fix", "spaces"], "win"), ["commit", "-m", "fix spaces"])
        self.assertEqual(git_commands.git_arguments("gpo", [], "mac"), ["push", "origin"])
        self.assertEqual(git_commands.git_arguments("gpo", [], "win"), ["push"])

    def test_git_exit_code_is_returned(self):
        with mock.patch.object(git_commands.subprocess, "run", return_value=mock.Mock(returncode=7)) as run:
            self.assertEqual(git_commands.main(["mac", "ga", "a b.txt"]), 7)
        run.assert_called_once_with(["git", "add", "a b.txt"], check=False)

    def test_remote_selection_uses_local_branch_when_present(self):
        with mock.patch.object(gswitch, "_run_git", return_value=mock.Mock(returncode=0)), mock.patch.object(
            gswitch.subprocess, "run", return_value=mock.Mock(returncode=0)
        ) as run:
            self.assertEqual(gswitch.switch_selected("remote", "origin/feature/a"), 0)
        run.assert_called_once_with(["git", "switch", "feature/a"], check=False)

    def test_remote_selection_tracks_when_local_branch_is_missing(self):
        with mock.patch.object(gswitch, "_run_git", return_value=mock.Mock(returncode=1)), mock.patch.object(
            gswitch.subprocess, "run", return_value=mock.Mock(returncode=3)
        ) as run:
            self.assertEqual(gswitch.switch_selected("remote", "origin/feature/a"), 3)
        run.assert_called_once_with(["git", "switch", "--track", "origin/feature/a"], check=False)


class ShellCommandTests(unittest.TestCase):
    def test_activation_path_is_platform_specific(self):
        root = pathlib.Path("project")
        self.assertEqual(shell_commands.activation_script("mac", root), root / ".venv/bin/activate")
        self.assertEqual(shell_commands.activation_script("win", root), root / ".venv/Scripts/Activate.ps1")

    def test_missing_activation_does_not_emit_a_path(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(shell_commands.Path, "cwd", return_value=pathlib.Path(directory)):
            self.assertEqual(shell_commands.main(["venv-activate", "mac"]), 1)

    def test_open_passes_a_path_with_spaces_as_one_argument(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "name with spaces.txt"
            path.touch()
            with mock.patch.object(shell_commands.sys, "platform", "darwin"), mock.patch.object(
                shell_commands.subprocess, "run", return_value=mock.Mock(returncode=0)
            ) as run:
                self.assertEqual(shell_commands.main(["open", str(path)]), 0)
            run.assert_called_once_with(["open", str(path)], check=True)


if __name__ == "__main__":
    unittest.main()
