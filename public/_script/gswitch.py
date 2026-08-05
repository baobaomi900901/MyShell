#!/usr/bin/env python3
# public/_script/gswitch.py
# 交互选择分支并写入临时文件，供 PowerShell 执行 git switch（风格同 cd_.ps1 + common.interactive_select）

from __future__ import annotations

import os
import subprocess
import sys

from common import RED, RESET, YELLOW, interactive_select, write_temp_file


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


def _switch_arg_for_remote(ref: str) -> str:
    """传给 git switch 的短名：origin/hotfix/x -> hotfix/x"""
    return ref.split("/", 1)[1]


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

def main() -> None:
    if len(sys.argv) < 2:
        print(f"{RED}❌ 参数不足：需要临时文件路径{RESET}")
        sys.exit(1)

    out_file = sys.argv[1]
    _ensure_git_repo()

    current = _current_branch()
    items = build_branch_items(current, _list_locals(), _list_remotes())

    if not items:
        print(f"{YELLOW}没有可选分支。{RESET}")
        sys.exit(0)


    _, value = interactive_select(
        "选择要切换的分支:",
        items,
        instruction="(按 ↑/↓ 选择，回车确认，Ctrl+C 退出)",
    )
    if value is None:
        print(f"{YELLOW}已取消操作。{RESET}")
        sys.exit(0)

    write_temp_file(out_file, value)


if __name__ == "__main__":
    main()
