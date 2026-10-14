#!/usr/bin/env python3
# public/_script/gswitch.py
# 交互选择并切换分支；macOS 与 Windows 共用。

from __future__ import annotations

import os
import subprocess
import sys

from common import RED, RESET, YELLOW, interactive_select


def _run_git(args: list[str], cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=cwd or os.getcwd(),
        encoding="utf-8",
        errors="replace",
    )


def _ensure_git_repo() -> None:
    p = _run_git(["rev-parse", "--is-inside-work-tree"])
    if p.returncode != 0 or p.stdout.strip() != "true":
        print(f"{RED}❌ 当前目录不是 Git 仓库（或 git 不可用）。{RESET}")
        sys.exit(1)


def _current_branch() -> str:
    p = _run_git(["branch", "--show-current"])
    if p.returncode != 0:
        return ""
    return p.stdout.strip()


def _list_locals() -> list[str]:
    p = _run_git(["for-each-ref", "refs/heads/", "--format=%(refname:short)"])
    if p.returncode != 0:
        return []
    return [x.strip() for x in p.stdout.splitlines() if x.strip()]


def _list_remotes() -> list[str]:
    p = _run_git(["for-each-ref", "refs/remotes/", "--format=%(refname:short)"])
    if p.returncode != 0:
        return []
    out: list[str] = []
    for line in p.stdout.splitlines():
        line = line.strip()
        if not line or line.endswith("/HEAD"):
            continue
        if "/" not in line:
            continue
        out.append(line)
    return out


def build_branch_items(
    current: str, locals_: list[str], remotes: list[str]
) -> list[tuple[str, str, str]]:
    locals_sorted = sorted(locals_, key=lambda branch: (branch != current, branch.lower()))
    remotes_sorted = sorted(
        (ref for ref in remotes if not ref.endswith("/HEAD")), key=str.lower
    )
    items = [
        (
            branch,
            f"{'* ' if branch == current else '  '}[本地] {branch}",
            f"local\t{branch}",
        )
        for branch in locals_sorted
    ]
    items.extend(
        (ref, f"  [远端] {ref}", f"remote\t{ref}") for ref in remotes_sorted
    )
    return items

def switch_selected(source: str, ref: str) -> int:
    if source == "local":
        return subprocess.run(["git", "switch", ref], check=False).returncode
    if source == "remote" and "/" in ref:
        local_branch = ref.split("/", 1)[1]
        existing = _run_git(["show-ref", "--verify", "--quiet", f"refs/heads/{local_branch}"])
        args = ["switch", local_branch] if existing.returncode == 0 else ["switch", "--track", ref]
        return subprocess.run(["git", *args], check=False).returncode
    print(f"{RED}❌ 无效的分支选择结果: {source} {ref}{RESET}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) > 1:
        print(f"{RED}用法: gswitch [分支]{RESET}", file=sys.stderr)
        return 2
    if argv:
        return subprocess.run(["git", "switch", argv[0]], check=False).returncode
    _ensure_git_repo()

    current = _current_branch()
    items = build_branch_items(current, _list_locals(), _list_remotes())

    if not items:
        print(f"{YELLOW}没有可选分支。{RESET}")
        return 0


    _, value = interactive_select(
        "选择要切换的分支:",
        items,
        instruction="(按 ↑/↓ 选择，回车确认，Ctrl+C 退出)",
    )
    if value is None:
        print(f"{YELLOW}已取消操作。{RESET}")
        return 0
    source, ref = value.split("\t", 1)
    return switch_selected(source, ref)


if __name__ == "__main__":
    raise SystemExit(main())
