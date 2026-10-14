#!/usr/bin/env python3
"""Shared implementation for the small Git terminal commands."""

from __future__ import annotations

import subprocess
import sys


COMMANDS = {
    "gs": ["status"],
    "gpr": ["pull", "--rebase"],
    "gsuk": ["stash", "-u", "-k"],
    "gspop": ["stash", "pop"],
    "grecmt": ["reset", "--soft", "HEAD~1"],
    "glocal": ["log", "origin/develop..HEAD", "--oneline"],
}


def git_arguments(command: str, args: list[str], platform: str) -> list[str]:
    if command == "ga":
        return ["add", *(args or ["."])]
    if command == "gcmt":
        # A commit message containing spaces must remain one Git argument.
        return ["commit", "-m", " ".join(args)]
    if command == "gpo":
        return ["push", "origin"] if platform == "mac" else ["push"]
    if command in COMMANDS:
        return COMMANDS[command]
    raise ValueError(f"未知 Git 命令: {command}")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 2 or argv[0] not in {"mac", "win"}:
        print("用法: git_commands.py <mac|win> <命令> [参数...]", file=sys.stderr)
        return 2
    platform, command, *args = argv
    try:
        git_args = git_arguments(command, args, platform)
        result = subprocess.run(["git", *git_args], check=False)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"无法执行 Git: {exc}", file=sys.stderr)
        return 127
    if result.returncode == 0 and platform == "win" and command == "ga":
        print("Added specified files to staging area." if args else "Added all changes to staging area.")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
