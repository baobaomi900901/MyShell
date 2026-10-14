#!/usr/bin/env python3
"""Cross-platform checks and opening used by interactive shell wrappers."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def activation_script(platform: str, cwd: Path) -> Path:
    if platform == "win":
        return cwd / ".venv" / "Scripts" / "Activate.ps1"
    if platform == "mac":
        return cwd / ".venv" / "bin" / "activate"
    raise ValueError(f"不支持的系统: {platform}")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("用法: shell_commands.py <venv-activate|venv-deactivate|open> [参数...]", file=sys.stderr)
        return 2
    command, *args = argv
    if command == "venv-activate":
        if len(args) != 1:
            return 2
        script = activation_script(args[0], Path.cwd())
        if not script.is_file():
            print(f"❌ 未找到 {script}，请确认当前目录是项目根目录且已创建 .venv", file=sys.stderr)
            return 1
        print(script)
        return 0
    if command == "venv-deactivate":
        if os.environ.get("VIRTUAL_ENV"):
            return 0
        print("⚠️ 当前未激活任何虚拟环境", file=sys.stderr)
        return 1
    if command == "open":
        paths = args or ["."]
        failed = False
        for name in paths:
            path = Path(name)
            if not path.exists():
                print(f"警告: 路径不存在，已跳过: {name}", file=sys.stderr)
                continue
            try:
                if sys.platform == "win32":
                    os.startfile(path)  # type: ignore[attr-defined]
                elif sys.platform == "darwin":
                    subprocess.run(["open", str(path)], check=True)
                else:
                    print("op_ 仅支持 macOS 和 Windows", file=sys.stderr)
                    return 2
            except OSError as exc:
                print(f"无法打开 {name}: {exc}", file=sys.stderr)
                failed = True
            except subprocess.CalledProcessError:
                failed = True
        return int(failed)
    print(f"未知命令: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
