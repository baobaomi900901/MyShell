#!/usr/bin/env python3
"""Install MyShell into the current user's Zsh or PowerShell profile."""

from __future__ import annotations

import errno
import json
import locale
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


START_MARKER = "# >>> MyShell init >>>"
END_MARKER = "# <<< MyShell init <<<"
REQUIRED_FILES = (
    "MacOS/MT_General/reloadsh.zsh",
    "Windows/MT_General/reloadsh.ps1",
    "public/_script/reloadsh.py",
)

OLD_ZSH_LOOP = """setopt extended_glob
for func_file in "$MYSHELL"/MacOS/**/*.zsh(N); do
  if [[ "$func_file" == *"/Expired/"* ]]; then
    continue
  fi
  source "$func_file"
done
zstyle ':completion:*' menu select=1"""

OLD_ZSH_HOME_LOOP = """for func_file in ~/MyShell/MacOS/**/*.zsh(N); do
  # 如果路径中包含 /Expired/ 则跳过
  if [[ "$func_file" == *"/Expired/"* ]]; then
    continue
  fi
  source "$func_file"
done
zstyle ':completion:*' menu select=1"""

OLD_POWERSHELL_BLOCK = r'''$functionsDir = Join-Path $env:MYSHELL "windows"
if ($env:MYSHELL -and (Test-Path $functionsDir)) {
    Get-ChildItem -Path $functionsDir -Recurse -Filter *.ps1 -File |
        Where-Object { $_.FullName -notmatch '\\Expired\\' } |
        ForEach-Object {
            . $_.FullName
        }
}
Import-Module PSReadLine'''


class InstallError(Exception):
    """An expected installation failure with a useful message."""


def run(command: list[str], *, env: dict[str, str] | None = None,
        capture: bool = False) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command, env=env, text=True, encoding="utf-8", errors="replace",
            capture_output=capture, check=False,
        )
    except OSError as exc:
        raise InstallError(f"无法执行 {command[0]}：{exc}") from exc
    if result.returncode != 0:
        detail = ((result.stderr or result.stdout or "").strip() if capture else "")
        raise InstallError(
            f"命令执行失败（退出码 {result.returncode}）：{command[0]}"
            + (f"\n{detail}" if detail else "")
        )
    return result


def same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left.resolve())) == os.path.normcase(str(right.resolve()))


def ask_to_move(current: Path, destination: Path) -> bool:
    print(f"当前目录：{current}")
    print(f"推荐目录：{destination}")
    try:
        response = input("是否将整个项目移动到推荐目录？[y/N] ").strip().lower()
    except EOFError:
        response = ""
    return response in {"y", "yes"}


def move_project(current: Path, destination: Path) -> Path:
    if destination.exists():
        raise InstallError(f"目标目录已存在，未覆盖：{destination}")
    if destination.parent.resolve().is_relative_to(current.resolve()):
        raise InstallError("推荐目录位于当前项目内部，无法移动。")

    destination.parent.mkdir(parents=True, exist_ok=True)
    # Python 离开源目录后再移动；跨磁盘时先完整复制到临时目录。
    os.chdir(destination.parent)
    try:
        current.rename(destination)
    except OSError as exc:
        # Windows 终端当前目录仍在源项目时，目录重命名可能被占用。
        can_copy = exc.errno == errno.EXDEV or (
            os.name == "nt" and exc.errno in {errno.EACCES, errno.EPERM}
        )
        if not can_copy:
            raise InstallError(f"移动项目失败：{exc}") from exc
        staging = Path(tempfile.mkdtemp(prefix=".myshell-move-", dir=destination.parent))
        try:
            shutil.rmtree(staging)
            shutil.copytree(current, staging, symlinks=True)
            staging.rename(destination)
        except (OSError, shutil.Error) as copy_exc:
            if staging.exists():
                shutil.rmtree(staging)
            raise InstallError(f"跨磁盘复制失败，原目录仍保留：{copy_exc}") from copy_exc
        try:
            shutil.rmtree(current)
        except OSError as remove_exc:
            print(
                f"警告：项目已复制到 {destination}，原目录因占用未能删除：{remove_exc}。"
                "关闭原终端后可手动删除旧目录。"
            )
    print(f"项目目录已更新：{destination}")
    return destination


def select_root(current: Path, system: str) -> Path:
    home = Path.home()
    destination = (
        home / "MyShell" if system == "Darwin"
        else home / "Documents" / "WindowsPowerShell" / "MyShell"
    )
    if same_path(current, destination):
        print(f"项目位于推荐目录：{current}")
        return current
    if ask_to_move(current, destination):
        return move_project(current, destination)
    print("将继续在当前目录安装。")
    return current


def read_profile(path: Path) -> tuple[str, str, str]:
    if not path.exists():
        return "", "utf-8-sig" if os.name == "nt" else "utf-8", "\n"
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        encoding = "utf-16"
    elif raw.startswith(b"\xef\xbb\xbf"):
        encoding = "utf-8-sig"
    else:
        try:
            raw.decode("utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            encoding = locale.getpreferredencoding(False)
    try:
        content = raw.decode(encoding)
    except UnicodeDecodeError as exc:
        raise InstallError(f"无法读取配置文件编码，未修改：{path}") from exc
    newline = "\r\n" if b"\r\n" in raw and encoding != "utf-16" else "\n"
    if encoding == "utf-16" and "\r\n" in content:
        newline = "\r\n"
    return content, encoding, newline


def replace_block(content: str, block: str, *, legacy: tuple[str, ...] = ()) -> str:
    normalized = content.replace("\r\n", "\n")
    start_count = normalized.count(START_MARKER)
    end_count = normalized.count(END_MARKER)
    if start_count != end_count or start_count > 1:
        raise InstallError("配置文件中的 MyShell 标记不完整或重复，请手动检查。")
    if start_count:
        pattern = re.compile(
            rf"(?m)^{re.escape(START_MARKER)}\n.*?^{re.escape(END_MARKER)}(?:\n|$)",
            re.DOTALL,
        )
        normalized, count = pattern.subn("", normalized)
        if count != 1:
            raise InstallError("无法安全替换已有 MyShell 配置块。")
    for old in legacy:
        normalized = normalized.replace(old + "\n", "").replace(old, "")
    return normalized.rstrip("\n") + "\n\n" + block + "\n"


def write_profile(path: Path, content: str, encoding: str, newline: str) -> bool:
    old_content, old_encoding, _ = read_profile(path)
    if old_content.replace("\r\n", "\n") == content and old_encoding == encoding:
        print(f"配置已是最新：{path}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_name(path.name + ".myshell.bak")
        if not backup.exists():
            shutil.copy2(path, backup)
            print(f"已备份原配置：{backup}")
    fd, temp_name = tempfile.mkstemp(prefix=".myshell-profile-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="") as stream:
            stream.write(content.replace("\n", newline))
        if path.exists():
            shutil.copymode(path, temp_name)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    print(f"已更新配置：{path}")
    return True


def ensure_private_dir(root: Path) -> None:
    (root / "config" / "private").mkdir(parents=True, exist_ok=True)


def ensure_python_module(python: str, module: str, package: str | None = None) -> None:
    check = subprocess.run(
        [python, "-c", f"import {module}"], capture_output=True, check=False,
    )
    if check.returncode == 0:
        return
    package = package or module
    print(f"安装 Python 依赖：{package}")
    run([python, "-m", "pip", "install", package])


def install_tracked_packages(root: Path, python: str) -> None:
    tracker = root / "config" / "private" / "function_tracker.json"
    if not tracker.exists():
        raise InstallError(f"未生成函数索引：{tracker}")
    try:
        packages = json.loads(tracker.read_text(encoding="utf-8")).get("pip_package", [])
    except (OSError, ValueError) as exc:
        raise InstallError(f"无法读取函数索引：{exc}") from exc
    if not isinstance(packages, list) or any(not isinstance(pkg, str) for pkg in packages):
        raise InstallError("函数索引的 pip_package 格式不正确。")
    failed: list[str] = []
    for package in packages:
        present = subprocess.run(
            [python, "-m", "pip", "show", package],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        )
        if present.returncode == 0:
            continue
        print(f"安装 Python 依赖：{package}")
        result = subprocess.run([python, "-m", "pip", "install", package], check=False)
        if result.returncode != 0:
            failed.append(package)
    if failed:
        raise InstallError("以下 Python 依赖安装失败：" + ", ".join(failed))


def zsh_block(root: Path) -> str:
    import shlex

    return f"""{START_MARKER}
export MYSHELL={shlex.quote(str(root))}
if ! (( $+functions[compdef] )); then
  autoload -Uz compinit
  compinit
fi
setopt extended_glob
for func_file in "$MYSHELL"/MacOS/**/*.zsh(N); do
  if [[ "$func_file" == *"/Expired/"* ]]; then
    continue
  fi
  source "$func_file"
done
zstyle ':completion:*' menu select=1
{END_MARKER}"""


def install_macos(root: Path) -> None:
    python = shutil.which("python3")
    if not python:
        raise InstallError("未找到 python3，请先安装 Python 3。")
    if not shutil.which("zsh"):
        raise InstallError("未找到 zsh。")
    if not shutil.which("jq"):
        raise InstallError("未找到 jq；hsh 需要 jq 才能显示命令索引。")
    ensure_python_module(python, "questionary")
    ensure_private_dir(root)

    profile = Path.home() / ".zshrc"
    content, encoding, newline = read_profile(profile)
    # 清理本项目旧版 init.py 写入的加载块和环境变量行。
    legacy = (OLD_ZSH_LOOP, OLD_ZSH_HOME_LOOP)
    content = re.sub(r"(?m)^export MYSHELL=.*\n?", "", content.replace("\r\n", "\n"))
    updated = replace_block(content, zsh_block(root), legacy=legacy)
    write_profile(profile, updated, encoding, newline)

    env = os.environ.copy()
    env["MYSHELL"] = str(root)
    print("在新的 Zsh 子进程中执行 reloadsh...")
    run(["zsh", "-i", "-c", "reloadsh"], env=env)
    install_tracked_packages(root, python)
    print("检查 hsh 输出...")
    run(["zsh", "-i", "-c", "hsh"], env=env)
    print("macOS 初始化完成。当前终端请执行：source ~/.zshrc")


def ps_single_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def powershell_profile(shell: str) -> Path:
    command = (
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); "
        "[Console]::Write($PROFILE.CurrentUserAllHosts)"
    )
    output = run([shell, "-NoProfile", "-NonInteractive", "-Command", command], capture=True)
    path = output.stdout.strip()
    if not path or not path.lower().endswith(".ps1"):
        raise InstallError(f"无法获取 {shell} 的 CurrentUserAllHosts 配置路径。")
    return Path(path)


def powershell_block(root: Path) -> str:
    return f"""{START_MARKER}
$env:MYSHELL = {ps_single_quote(str(root))}
$functionsDir = Join-Path $env:MYSHELL 'Windows'
if (Test-Path -LiteralPath $functionsDir) {{
    Get-ChildItem -LiteralPath $functionsDir -Recurse -Filter *.ps1 -File |
        Where-Object {{ $_.FullName -notmatch '\\\\Expired\\\\' }} |
        ForEach-Object {{ . $_.FullName }}
}}
{END_MARKER}"""


def update_windows_environment(root: Path) -> None:
    import winreg

    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            winreg.SetValueEx(key, "MYSHELL", 0, winreg.REG_SZ, str(root))
        os.environ["MYSHELL"] = str(root)
    except OSError as exc:
        raise InstallError(f"无法设置用户环境变量 MYSHELL：{exc}") from exc


def install_windows(root: Path) -> None:
    python = shutil.which("python")
    if not python:
        raise InstallError("未找到 python，请先将 Python 3 加入 PATH。")
    ensure_python_module(python, "questionary")
    ensure_python_module(python, "keyboard")
    ensure_private_dir(root)

    shells = [shell for shell in ("powershell", "pwsh") if shutil.which(shell)]
    if not shells:
        raise InstallError("未找到 Windows PowerShell 或 PowerShell 7。")
    profiles = [(shell, powershell_profile(shell)) for shell in shells]
    block = powershell_block(root)
    for shell, profile in profiles:
        content, encoding, newline = read_profile(profile)
        # Windows PowerShell 5.1 读取含非 ASCII 字符的脚本时需要 UTF-8 BOM。
        if shell == "powershell" and encoding != "utf-16":
            encoding = "utf-8-sig"
        updated = replace_block(content, block, legacy=(OLD_POWERSHELL_BLOCK,))
        write_profile(profile, updated, encoding, newline)
    update_windows_environment(root)

    shell, profile = profiles[0]
    escaped = ps_single_quote(str(profile))
    command = (
        f". {escaped}; reloadsh --no-restart; "
        "if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }"
    )
    print(f"使用 {shell} 执行 reloadsh --no-restart...")
    run([shell, "-NoProfile", "-NonInteractive", "-Command", command])
    install_tracked_packages(root, python)
    print("Windows 初始化完成。请重新打开终端窗口，再执行 hsh。")


def main() -> int:
    import platform

    system = platform.system()
    if system not in {"Darwin", "Windows"}:
        print(f"暂不支持该操作系统：{system}", file=sys.stderr)
        return 1
    current = Path(__file__).resolve().parent
    for relative in REQUIRED_FILES:
        if not (current / relative).is_file():
            print(f"项目文件缺失：{relative}", file=sys.stderr)
            return 1
    try:
        root = select_root(current, system)
        if system == "Darwin":
            install_macos(root)
        else:
            install_windows(root)
    except (InstallError, OSError) as exc:
        print(f"初始化失败：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
