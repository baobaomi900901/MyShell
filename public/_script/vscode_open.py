#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
vscode_open.py - 通用 VS Code 打开脚本
根据配置文件中的路径，输出 `code "路径"` 命令供 Shell 执行。
"""

import os
import sys
import json
import platform
from pathlib import Path

# ANSI 颜色（终端支持）
YELLOW = '\033[93m'
RESET = '\033[0m'

def get_config_path():
    """返回配置文件（path_code.json）路径"""
    myshell = os.environ.get('MYSHELL')
    if myshell:
        return Path(myshell) / "config" / "private" / "path_code.json"
    # 兼容旧路径
    user_profile = os.environ.get('USERPROFILE', '')
    if not user_profile:
        user_profile = str(Path.home())
    return Path(user_profile) / "Documents" / "WindowsPowerShell" / "MyShell" / "config" / "private" / "path_code.json"

def load_config(config_path):
    """加载并解析 JSON 配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析错误: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}", file=sys.stderr)
        return None

def show_help(config):
    """打印彩色帮助信息"""
    lines = ["VS Code 快速打开", "用法: code_ <名称>", "", "可用项目:"]
    # 显示所有至少在一个系统上有路径的条目
    names = [key.replace('_', '-') for key, val in config.items() if val.get('win') or val.get('mac')]
    max_len = max(len(name) for name in names) if names else 0

    print()
    for key, val in config.items():
        if val.get('win') or val.get('mac'):
            display_name = key.replace('_', '-')
            desc = val.get('description', '')
            lines.append(f"  {YELLOW}{display_name:<{max_len}}{RESET} # {desc}")
    return "\n".join(lines)

def main():
    # 无参数或空参数 -> 显示帮助
    if len(sys.argv) < 2 or not sys.argv[1]:
        config_path = get_config_path()
        if not config_path.exists():
            print(f"❌ 配置文件不存在\n请手动创建: {config_path}", file=sys.stderr)
            sys.exit(1)
        config = load_config(config_path)
        if config is None:
            sys.exit(1)
        print(show_help(config))
        return

    action = sys.argv[1]
    internal_action = action.replace('-', '_')

    config_path = get_config_path()
    if not config_path.exists():
        print(f"❌ 配置文件不存在\n请手动创建: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    if config is None:
        sys.exit(1)

    if internal_action not in config:
        print(f"❌ 项目 '{action}' 不存在", file=sys.stderr)
        sys.exit(1)

    item = config[internal_action]
    system = platform.system()

    # 根据操作系统选择路径字段
    if system == "Windows":
        target_path = item.get('win')
        if target_path is None:
            print(f"❌ 项目 '{action}' 在 Windows 上未配置", file=sys.stderr)
            sys.exit(1)
    elif system == "Darwin":  # macOS
        target_path = item.get('mac')
        if target_path is None:
            print(f"❌ 项目 '{action}' 在 macOS 上未配置。请在配置中添加 'mac' 字段。", file=sys.stderr)
            sys.exit(1)
    else:
        # 其他 Unix 系统，优先 mac 字段，否则尝试 win（需转换）
        target_path = item.get('mac') or item.get('win')
        if target_path is None:
            print(f"❌ 项目 '{action}' 未配置", file=sys.stderr)
            sys.exit(1)
        if 'mac' not in item:
            print("⚠️  建议在配置中添加 'mac' 字段以支持 macOS", file=sys.stderr)

    # 路径规范化：如果是 macOS 但路径包含反斜杠（Windows 风格），尝试转换并警告
    if system != "Windows" and '\\' in target_path:
        print(f"⚠️  路径包含反斜杠，可能不是有效的 Unix 路径: {target_path}", file=sys.stderr)
        target_path = target_path.replace('\\', '/')

    path_obj = Path(target_path).expanduser().resolve()
    if not path_obj.exists():
        print(f"❌ 路径不存在 - {path_obj}", file=sys.stderr)
        sys.exit(1)
    # 文件或目录都可以被 VS Code 打开，所以只检查存在性，不检查类型

    target_path_str = str(path_obj)

    # 构造带双引号的路径，并转义内部双引号（如有）
    escaped = target_path_str.replace('"', '\\"')
    quoted_path = f'"{escaped}"'

    # 输出 VS Code 命令（跨平台，code 命令需在 PATH 中）
    print(f"code {quoted_path}")

if __name__ == "__main__":
    main()