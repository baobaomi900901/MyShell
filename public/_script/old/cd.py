#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
cd.py - 通用目录跳转脚本（中文帮助，兼容 Windows 旧终端）
"""

import os
import sys
import json
import platform
import subprocess
import ctypes
from pathlib import Path

# ---------- 获取控制台实际编码 ----------
def get_console_encoding():
    """返回控制台实际使用的编码名称（Windows 下通常为 cp936/GBK）"""
    if platform.system() == "Windows":
        try:
            if hasattr(ctypes, 'windll'):
                cp = ctypes.windll.kernel32.GetConsoleOutputCP()
                return f'cp{cp}'
        except Exception:
            pass
        return 'gbk'  # 默认
    else:
        return 'utf-8'

CONSOLE_ENCODING = get_console_encoding()

def safe_print(text, file=sys.stdout):
    """根据控制台实际编码安全打印，避免乱码"""
    try:
        # 直接打印，让 Python 自动转换
        print(text, file=file)
    except UnicodeEncodeError:
        # 如果默认编码失败，强制用控制台编码重新编码
        encoded_bytes = text.encode(CONSOLE_ENCODING, errors='replace')
        decoded = encoded_bytes.decode(CONSOLE_ENCODING, errors='replace')
        print(decoded, file=file)

# ---------- 颜色控制：旧终端下完全禁用 ----------
def use_color():
    """Windows 旧终端（非 Windows Terminal）下禁用颜色"""
    if platform.system() != "Windows":
        return True
    if 'WT_SESSION' in os.environ:
        return True
    # 尝试启用虚拟终端处理，若失败则禁用颜色
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        if (mode.value & 0x0004) == 0:
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        return True
    except Exception:
        return False

_use_color = use_color()
YELLOW = '\033[93m' if _use_color else ''
RED    = '\033[91m' if _use_color else ''
GRAY   = '\033[90m' if _use_color else ''
RESET  = '\033[0m'  if _use_color else ''

# ---------- 配置路径 ----------
def get_config_path():
    myshell = os.environ.get('MYSHELL')
    if myshell:
        return Path(myshell) / "config" / "private" / "path.json"
    user_profile = os.environ.get('USERPROFILE', str(Path.home()))
    return Path(user_profile) / "Documents" / "WindowsPowerShell" / "MyShell" / "config" / "private" / "path.json"

def load_config(config_path):
    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except Exception as e:
        safe_print(f"{RED}加载配置文件失败: {e}{RESET}", file=sys.stderr)
        return None

def print_missing_config(config_path):
    safe_print(f"\n{RED}配置文件不存在: {config_path}{RESET}")
    safe_print(f"{YELLOW}请手动创建该文件，模板如下（保存为 UTF-8 无 BOM 格式）：{RESET}")
    example = {
        "MyShell": {
            "win": r"C:\Users\YourUsername\Documents\WindowsPowerShell\MyShell",
            "mac": "/Users/YourUsername/MyShell",
            "description": "MyShell 配置目录"
        }
    }
    safe_print(json.dumps(example, indent=2, ensure_ascii=False))
    safe_print("")

def show_help(config):
    """显示中文帮助信息"""
    lines = [
        f"{YELLOW}快速目录跳转{RESET}",
        f"用法: {YELLOW}cd_ <名称>{RESET}",
        "",
        f"{YELLOW}可用目录:{RESET}"
    ]
    items = [(key.replace('_', '-'), val) for key, val in config.items() if val.get('win') or val.get('mac')]
    if not items:
        lines.append("  (无可用目录)")
    else:
        max_len = max(len(name) for name, _ in items)
        for name, val in items:
            desc = val.get('description', '')
            lines.append(f"  {YELLOW}{name:<{max_len}}{RESET} # {desc}")
    return "\n".join(lines)

def fix_win_path(path_str):
    """修正 Windows 路径中的重复盘符，如 D:D:\\xxx -> D:\\xxx"""
    import re
    return re.sub(r'^([A-Za-z]):\1:\\', r'\1:\\', path_str)

def main():
    config_path = get_config_path()

    if len(sys.argv) < 2 or not sys.argv[1]:
        if not config_path.exists():
            print_missing_config(config_path)
            sys.exit(1)
        config = load_config(config_path)
        if config is None:
            sys.exit(1)
        safe_print(show_help(config))
        return

    action = sys.argv[1]
    internal_action = action.replace('-', '_')

    if not config_path.exists():
        print_missing_config(config_path)
        sys.exit(1)

    config = load_config(config_path)
    if config is None:
        sys.exit(1)

    if internal_action not in config:
        safe_print(f"{RED}目录 '{action}' 不存在{RESET}")
        sys.exit(1)

    item = config[internal_action]
    system = platform.system()

    if system == "Windows":
        target_path = item.get('win')
        if target_path is None:
            safe_print(f"{RED}目录 '{action}' 在 Windows 上未配置{RESET}")
            sys.exit(1)
        target_path = fix_win_path(target_path)
    elif system == "Darwin":
        target_path = item.get('mac')
        if target_path is None:
            safe_print(f"{RED}目录 '{action}' 在 macOS 上未配置{RESET}")
            sys.exit(1)
    else:
        target_path = item.get('mac') or item.get('win')
        if target_path is None:
            safe_print(f"{RED}目录 '{action}' 未配置{RESET}")
            sys.exit(1)

    if system != "Windows" and '\\' in target_path:
        target_path = target_path.replace('\\', '/')

    path_obj = Path(target_path).expanduser().resolve()
    if not path_obj.exists():
        safe_print(f"{RED}目录不存在: {path_obj}{RESET}")
        sys.exit(1)
    if not path_obj.is_dir():
        safe_print(f"{RED}路径不是目录: {path_obj}{RESET}")
        sys.exit(1)

    target = str(path_obj)

    # 输出跳转命令（路径中可能含中文，但 safe_print 会处理）
    if os.name == 'nt':
        escaped = target.replace("'", "''")
        safe_print(f"Set-Location '{escaped}'")
    else:
        escaped = target.replace("'", "'\\''")
        safe_print(f"cd '{escaped}'")

if __name__ == "__main__":
    main()