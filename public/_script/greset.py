#!/usr/bin/env python3
# public/_script/greset.py

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from typing import List, Tuple

from common import GREEN, RED, RESET, YELLOW, interactive_select


def _run_git(args: List[str]) -> int:
    p = subprocess.run(["git", *args])
    return int(p.returncode)


def _ensure_git_repo() -> None:
    p = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if p.returncode != 0:
        print(f"{RED}ERROR: not a git repo (or git not installed).{RESET}", file=sys.stderr)
        sys.exit(2)


def _confirm(prompt: str) -> bool:
    try:
        ans = input(f"{YELLOW}{prompt}{RESET} ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        return False
    return ans in {"y", "yes"}


def action_all() -> int:
    if not _confirm("Run `git reset --hard HEAD` (discard ALL uncommitted changes)? (y/N)"):
        print(f"{YELLOW}Cancelled.{RESET}")
        return 0
    code = _run_git(["reset", "--hard", "HEAD"])
    if code == 0:
        print(f"{GREEN}OK: git reset --hard HEAD{RESET}")
    return code


def action_back_n(n: int) -> int:
    if n <= 0:
        print(f"{RED}ERROR: back -n requires n >= 1.{RESET}", file=sys.stderr)
        return 2
    target = f"HEAD~{n}"
    if not _confirm(f"Run `git reset --soft {target}` (undo last {n} commit(s), keep changes staged)? (y/N)"):
        print(f"{YELLOW}Cancelled.{RESET}")
        return 0
    code = _run_git(["reset", "--soft", target])
    if code == 0:
        print(f"{GREEN}OK: git reset --soft {target}{RESET}")
    return code


def action_back_gcmt() -> int:
    # “放弃本地缓存”这里按“放弃暂存区/缓存区（staging/index）”理解：只取消暂存，不丢工作区改动
    if not _confirm("Run `git reset` (unstage, keep working tree changes)? (y/N)"):
        print(f"{YELLOW}Cancelled.{RESET}")
        return 0
    code = _run_git(["reset"])
    if code == 0:
        print(f"{GREEN}OK: git reset (unstaged){RESET}")
    return code


def interactive() -> int:
    items: List[Tuple[str, str, str]] = [
        ("all", "all      # discard all changes (git reset --hard HEAD)", "all"),
        ("back1", "back -1  # undo last commit (soft reset, keep staged)", "back:-1"),
        ("gcmt", "back gcmt # unstage (git reset)", "back:gcmt"),
    ]
    key, value = interactive_select(
        "Select greset action:",
        items,
        instruction="(Up/Down to select, Enter to confirm, Ctrl+C to quit)",
    )
    if value is None:
        print(f"{YELLOW}Cancelled.{RESET}")
        return 0

    if value == "all":
        return action_all()
    if value == "back:-1":
        return action_back_n(1)
    if value == "back:gcmt":
        return action_back_gcmt()

    print(f"{RED}ERROR: unknown option: {value}{RESET}", file=sys.stderr)
    return 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="greset.py",
        description="Interactive git reset (cross-platform).",
    )
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("all", help="Discard all uncommitted changes (git reset --hard HEAD)")

    back = sub.add_parser("back", help="Undo commits (soft reset) or unstage (mixed reset)")
    back.add_argument(
        "mode",
        nargs="?",
        help="Optional: -1/-2/... or gcmt; omit for interactive menu",
    )

    return p


def main() -> int:
    _ensure_git_repo()

    parser = build_parser()
    args = parser.parse_args()

    if args.cmd is None:
        return interactive()

    if args.cmd == "all":
        return action_all()

    if args.cmd == "back":
        if not args.mode:
            return interactive()
        if args.mode == "gcmt":
            return action_back_gcmt()
        if args.mode.startswith("-"):
            try:
                n = int(args.mode[1:])
            except ValueError:
                print(f"{RED}ERROR: invalid back argument: {args.mode}{RESET}", file=sys.stderr)
                return 2
            return action_back_n(n)
        print(f"{RED}ERROR: unsupported back argument: {args.mode}{RESET}", file=sys.stderr)
        return 2

    print(f"{RED}ERROR: unknown command.{RESET}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

